"""The `AIRouter` abstraction: the generic interface for sending any structured
request to an AI provider and receiving a structured response.

Why this exists alongside `MnemonicProvider`
--------------------------------------------
`MnemonicProvider` is correctly scoped to mnemonic generation — it takes a
`word` and returns a `MnemonicResult`.  It is NOT the right interface for
AI Chat, RAG Q&A, Quiz generation, Summarisation, or Presentation
generation, because none of those take a `word` or return a `MnemonicResult`.

Without `AIRouter`, every new AI feature faces three bad options:
  1. Add a new method to `MnemonicProvider` (violates ISP — mnemonic
     generation and chat turn have nothing to do with each other).
  2. Call the HTTP API directly (bypasses all Gateway routing, key rotation,
     health tracking, and tier separation — duplicates 400 lines of infra).
  3. Copy the Gateway for each feature (catastrophic duplication).

`AIRouter` provides the correct fourth option: a single `complete()` method
that accepts any `AIRequest` and returns any `AIResponse`, routed through
exactly the same Gateway pool, key rotation, cooldown, and tier logic that
`generate_mnemonic` already uses — because `AIGateway` implements BOTH
`MnemonicProvider` and `AIRouter` simultaneously.

Relationship to `MnemonicProvider`
-----------------------------------
`MnemonicProvider.generate_mnemonic()` now delegates to
`AIRouter.complete()` inside each concrete provider — it is the adapter
layer between the mnemonic-specific contract and the generic routing layer.

Call sites:
  MnemonicService      → calls provider.generate_mnemonic()   (unchanged)
  AIChatService        → calls ai_router.complete(chat_request)
  RAGService           → calls ai_router.complete(rag_request)
  QuizService          → calls ai_router.complete(quiz_request)
  SummaryService       → calls ai_router.complete(summary_request)
  PresentationService  → calls ai_router.complete(presentation_request)

All of the above get the same Gateway routing for free — zero duplication.

`response_schema`
-----------------
When set, `response_schema` is a JSON Schema dict that instructs the
provider to return structured JSON.  Gemini natively supports this via
`responseSchema`.  Groq supports constrained JSON via
`response_format: {type: "json_object"}` (not full JSON Schema, but
sufficient for our use cases with well-designed prompts).  When None,
the provider returns free-form text.

`temperature` and `max_tokens`
-------------------------------
These have deliberate defaults that differ from the mnemonic generation
defaults (which are set in `key_slot.py` per-provider).  `AIRequest`
callers can override them freely; the gateway passes them through without
modification.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AIRequest:
    """A structured request to be sent to an AI provider.

    This is a plain class (not Pydantic) to avoid import overhead in the
    hot path.  All fields are set at construction time and never mutated.

    Args:
        system_prompt:   The system / instruction prompt.  Describes the
                         AI's role and output format for this request type.
        user_message:    The user-turn content — the actual question,
                         document chunk, or instruction for this call.
        response_schema: Optional JSON Schema dict for structured output.
                         When provided, Gemini uses `responseSchema`; Groq
                         uses `json_object` mode with schema hints in the
                         system prompt.  When None, free-form text is returned.
        temperature:     Sampling temperature.  Default 0.7 (more focused than
                         mnemonic generation's 1.15 — appropriate for factual
                         tasks like Q&A and quiz generation).
        max_tokens:      Maximum tokens in the response.  Default 2048.
        request_type:    Optional tag for logging/analytics (e.g. "chat",
                         "rag", "quiz").  Never sent to the provider.
    """

    __slots__ = (
        "system_prompt",
        "user_message",
        "response_schema",
        "temperature",
        "max_tokens",
        "request_type",
    )

    def __init__(
        self,
        *,
        system_prompt: str,
        user_message: str,
        response_schema: dict[str, Any] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        request_type: str = "generic",
    ) -> None:
        self.system_prompt = system_prompt
        self.user_message = user_message
        self.response_schema = response_schema
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.request_type = request_type

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<AIRequest type={self.request_type!r} "
            f"temp={self.temperature} max_tokens={self.max_tokens} "
            f"schema={'yes' if self.response_schema else 'no'}>"
        )


class AIResponse:
    """A structured response from an AI provider.

    Returned by `AIRouter.complete()`.  The caller is responsible for
    parsing `raw_text` into its domain type (e.g. `json.loads()` then
    `QuizPayload.model_validate()`).

    Args:
        raw_text:      The full text content of the response.  If the
                       request had a `response_schema`, this should be
                       valid JSON.  If not, it is free-form text.
        provider_name: Which provider produced this response, e.g. "gemini".
        model_name:    Which model produced this response, e.g.
                       "gemini-2.5-flash".
        latency_ms:    Round-trip latency in milliseconds (measured by the
                       key slot, not the gateway — network time only).
        tokens_used:   Total tokens consumed, if the provider returns this.
                       None when unavailable (Gemini does not always return
                       token counts for all response types).
    """

    __slots__ = ("raw_text", "provider_name", "model_name", "latency_ms", "tokens_used")

    def __init__(
        self,
        *,
        raw_text: str,
        provider_name: str,
        model_name: str,
        latency_ms: float,
        tokens_used: int | None = None,
    ) -> None:
        self.raw_text = raw_text
        self.provider_name = provider_name
        self.model_name = model_name
        self.latency_ms = latency_ms
        self.tokens_used = tokens_used

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<AIResponse provider={self.provider_name!r} "
            f"model={self.model_name!r} latency={self.latency_ms:.0f}ms "
            f"len={len(self.raw_text)}>"
        )


class AIRouter(ABC):
    """Abstract interface for sending a generic request to an AI provider.

    Every class that implements this interface automatically benefits from
    all Gateway routing, key rotation, health tracking, and tier separation
    — because `AIGateway` implements both `MnemonicProvider` and `AIRouter`.

    The only concrete implementations are:
      - `AIGateway`     — production; full routing through all configured pools.
      - `TierProxy`     — per-request tier view; delegates to `AIGateway.complete_routed()`.
      - `MockAIRouter`  — offline; returns a fixed `AIResponse` for dev/testing.

    Future provider-specific implementations (e.g. `GeminiRouter`,
    `GroqRouter`) follow if the codebase ever moves away from the Gateway
    pattern, but they are NOT needed today.
    """

    @abstractmethod
    async def complete(
        self,
        request: AIRequest,
        *,
        is_premium: bool = False,
    ) -> AIResponse:
        """Send `request` to an AI model and return the structured response.

        Args:
            request:    The fully-constructed `AIRequest` to send.
            is_premium: Whether to route through the premium tier (faster
                        models, higher quota).  Ignored by `TierProxy` (it
                        already knows its tier); honoured by `AIGateway`
                        and `MockAIRouter`.

        Returns:
            An `AIResponse` with `raw_text` containing the model's reply.

        Raises:
            app.core.exceptions.AIProviderError: if all providers / keys are
                exhausted, or the gateway is in maintenance mode.
        """
        raise NotImplementedError


class MockAIRouter(AIRouter):
    """Offline `AIRouter` for unit tests and development without API keys.

    Returns a configurable fixed `AIResponse`.  The default `raw_text` is
    a minimal valid JSON object so that callers that `json.loads()` the
    response don't crash in test mode.

    Usage::

        router = MockAIRouter(raw_text='{"answer": "Paris"}')
        response = await router.complete(AIRequest(system_prompt="...", user_message="..."))
        assert response.raw_text == '{"answer": "Paris"}'
    """

    def __init__(
        self,
        *,
        raw_text: str = '{"mock": true}',
        provider_name: str = "mock",
        model_name: str = "mock-model",
        latency_ms: float = 1.0,
    ) -> None:
        self._raw_text = raw_text
        self._provider_name = provider_name
        self._model_name = model_name
        self._latency_ms = latency_ms

    async def complete(
        self,
        request: AIRequest,
        *,
        is_premium: bool = False,
    ) -> AIResponse:
        return AIResponse(
            raw_text=self._raw_text,
            provider_name=self._provider_name,
            model_name=self._model_name,
            latency_ms=self._latency_ms,
        )
