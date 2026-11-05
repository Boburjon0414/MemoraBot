"""AIChatService: multi-turn AI conversation using the full Tool Calling Layer.

Full pipeline per user turn
----------------------------
1.  Load ChatSessionPayload from FeatureOutput.
2.  Maybe summarise if history is too long.
3.  AIPlanner.plan() — selects tools, executes them concurrently, returns AIContext.
4.  PromptBuilder.build_system_prompt() — assembles prompt from real data only.
5.  AIRouter.complete() — calls the LLM.
6.  ResponseValidator.validate() — guards against fabrication.
7.  Persist both turns to FeatureOutput.
8.  MemoryUpdateHook.process() — detect and persist explicit user-stated facts.
9.  Return the (validated) reply.

Backward compatibility
----------------------
AIPlanner, ContextBuilder, and MemoryUpdateHook are all optional.
If None is passed, the service falls back to the previous ContextBuilder-only
path. This allows tests and legacy handlers to construct AIChatService with
only the required ai_router + feature_output_service.
"""

from __future__ import annotations

import logging
from datetime import datetime, UTC

from app.core.exceptions import AIProviderError
from app.database.models.feature_output import OutputType
from app.services.ai.router import AIRequest, AIRouter
from app.services.context.context_builder import AIContext, ContextBuilder, ContextPolicy
from app.services.context.memory_update_hook import MemoryUpdateHook
from app.services.context.prompt_builder import PromptBuilder
from app.services.context.user_context import UserContext
from app.services.feature_output_service import FeatureOutputService
from app.services.outputs.schemas import ChatMessage, ChatSessionPayload
from app.services.tools.base import ToolContext
from app.services.tools.planner import AIPlanner
from app.services.tools.response_validator import ResponseValidator

logger = logging.getLogger(__name__)

_SUMMARISE_THRESHOLD = 8_000
_KEEP_RECENT = 6
_SUMMARISE_SYSTEM_PROMPT = (
    "Summarise the following conversation into 3-5 concise bullet points. "
    "Preserve: main topics, vocabulary/grammar points, and personal details the learner shared. "
    "Output only the bullet-point summary. No preamble, no conclusion."
)

_prompt_builder = PromptBuilder()
_validator = ResponseValidator()


class AIChatService:
    """Multi-turn AI chat with full Tool Calling Layer integration."""

    def __init__(
        self,
        ai_router: AIRouter,
        feature_output_service: FeatureOutputService,
        # Optional — progressively degraded without them
        planner: AIPlanner | None = None,
        context_builder: ContextBuilder | None = None,
        memory_hook: MemoryUpdateHook | None = None,
        tool_context_factory=None,   # callable: (user_id, user_context) → ToolContext
    ) -> None:
        self._router = ai_router
        self._output_svc = feature_output_service
        self._planner = planner
        self._context_builder = context_builder
        self._memory_hook = memory_hook
        self._tool_context_factory = tool_context_factory

    # ── Session management ─────────────────────────────────────────────── #

    async def get_or_create_session(
        self,
        user_id: int,
        user_context: UserContext,
    ) -> tuple[int, ChatSessionPayload]:
        sessions = await self._output_svc.list_for_user(
            user_id, output_type=OutputType.CHAT_SESSION
        )
        if sessions:
            payload = await self._output_svc.load(
                user_id, sessions[0].id, schema=ChatSessionPayload
            )
            if payload is not None:
                return sessions[0].id, payload
        return await self._create_session(user_id)

    async def new_session(self, user_id: int) -> tuple[int, ChatSessionPayload]:
        for s in await self._output_svc.list_for_user(user_id, output_type=OutputType.CHAT_SESSION):
            await self._output_svc.archive(user_id, s.id)
        return await self._create_session(user_id)

    async def _create_session(self, user_id: int) -> tuple[int, ChatSessionPayload]:
        payload = ChatSessionPayload(messages=[])
        output = await self._output_svc.save(
            user_id=user_id,
            output_type=OutputType.CHAT_SESSION,
            payload=payload,
            title=f"Chat — {datetime.now(UTC).strftime('%b %d %H:%M')}",
        )
        return output.id, payload

    # ── Chat turn ──────────────────────────────────────────────────────── #

    async def chat(
        self,
        user_id: int,
        session_id: int,
        user_message: str,
        user_context: UserContext,
        tool_context: ToolContext | None = None,
    ) -> str:
        """Full pipeline: plan → build → generate → validate → persist → hook.

        Raises:
            AIProviderError: if all AI providers are exhausted.
        """
        # 1. Load session history
        payload = await self._output_svc.load(
            user_id, session_id, schema=ChatSessionPayload
        ) or ChatSessionPayload(messages=[])

        # 2. Summarise if long
        payload = await self._maybe_summarise(payload, user_context)

        # 3. Build AIContext via Planner (preferred) or ContextBuilder (fallback)
        ai_context = await self._build_context(
            user_message, user_context, tool_context
        )

        # 4. Assemble system prompt — only populated sections
        system_prompt = _prompt_builder.build_system_prompt(ai_context, feature="chat")

        # 5. Format conversation history + current message
        history = _format_history(payload)
        user_turn = f"{history}\nUser: {user_message}" if history else f"User: {user_message}"

        # 6. Call the LLM
        response = await self._router.complete(
            AIRequest(
                system_prompt=system_prompt,
                user_message=user_turn,
                temperature=0.7,
                max_tokens=1024,
                request_type="chat",
            ),
            is_premium=user_context.is_premium,
        )
        raw_reply = response.raw_text.strip()

        # 7. Validate — guard against fabrication
        validation = _validator.validate(raw_reply, ai_context)
        if not validation.valid:
            logger.warning(
                "AIChatService: response failed validation uid=%s violations=%s",
                user_id, validation.violations,
            )
        final_reply = validation.response

        # 8. Persist both turns
        now = datetime.now(UTC).isoformat()
        payload.messages.extend([
            ChatMessage(role="user", content=user_message, occurred_at=now),
            ChatMessage(role="assistant", content=final_reply, occurred_at=now),
        ])
        await self._output_svc.update_payload(session_id, payload=payload)

        # 9. Memory hook — fire-and-forget
        if self._memory_hook is not None:
            try:
                await self._memory_hook.process(user_id, user_message)
            except Exception:
                logger.warning("AIChatService: memory hook failed uid=%s", user_id, exc_info=True)

        return final_reply

    # ── Context assembly ───────────────────────────────────────────────── #

    async def _build_context(
        self,
        message: str,
        user_context: UserContext,
        tool_context: ToolContext | None,
    ) -> AIContext:
        """Build AIContext via Planner (if available) else ContextBuilder."""
        if self._planner is not None and tool_context is not None:
            ai_context, trace = await self._planner.plan(
                message, user_context, tool_context, feature="chat"
            )
            return ai_context

        if self._context_builder is not None:
            return await self._context_builder.build(user_context, ContextPolicy.for_chat())

        # Minimal fallback — just the user_context
        return AIContext(
            user_context=user_context,
            weak_words=list(user_context.recent_weak_words),
        )

    # ── Summarisation ──────────────────────────────────────────────────── #

    async def _maybe_summarise(
        self,
        payload: ChatSessionPayload,
        user_context: UserContext,
    ) -> ChatSessionPayload:
        total_chars = sum(len(m.content) for m in payload.messages)
        if total_chars <= _SUMMARISE_THRESHOLD or len(payload.messages) <= _KEEP_RECENT:
            return payload

        old_msgs = [m for m in payload.messages[:-_KEEP_RECENT] if m.role != "summary"]
        if not old_msgs:
            return payload

        history_text = "\n".join(f"{m.role.capitalize()}: {m.content}" for m in old_msgs)
        try:
            response = await self._router.complete(
                AIRequest(
                    system_prompt=_SUMMARISE_SYSTEM_PROMPT,
                    user_message=history_text,
                    temperature=0.3,
                    max_tokens=512,
                    request_type="chat_summarise",
                ),
                is_premium=user_context.is_premium,
            )
            summary_text = response.raw_text.strip()
        except Exception:
            logger.warning("AIChatService: summarisation failed", exc_info=True)
            return payload

        summary_msg = ChatMessage(
            role="summary",
            content=f"[Earlier conversation summary]\n{summary_text}",
            occurred_at=datetime.now(UTC).isoformat(),
        )
        new_payload = ChatSessionPayload(
            messages=[summary_msg] + list(payload.messages[-_KEEP_RECENT:])
        )
        logger.info("AIChatService: compressed %d old messages into summary", len(old_msgs))
        return new_payload


def _format_history(payload: ChatSessionPayload) -> str:
    if not payload.messages:
        return ""
    lines = []
    for msg in payload.messages:
        if msg.role == "summary":
            lines.append(msg.content)
        elif msg.role == "user":
            lines.append(f"User: {msg.content}")
        elif msg.role == "assistant":
            lines.append(f"Assistant: {msg.content}")
    return "\n".join(lines)
