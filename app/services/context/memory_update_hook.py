"""MemoryUpdateHook: detects persistent facts in user messages and updates UserMemory.

Policy
------
Only persist facts the user EXPLICITLY states.
Never infer permanent facts from temporary conversation.

Examples of what gets persisted:
  "My level is B2"           → english_level = "B2"
  "I'm B1"                   → english_level = "B1"
  "My goal is IELTS"         → learning_goal = "IELTS"
  "I'm studying for TOEFL"   → learning_goal = "TOEFL"
  "I struggle with conditionals" → weak_words: add "conditionals"
  "I love programming"        → topic_interests: add "programming"
  "I'm interested in science" → topic_interests: add "science"

Examples of what does NOT get persisted:
  "What does ephemeral mean?" → no update (transient question)
  "Can you quiz me?"          → no update (action request)
  "I think B2 is hard"        → no update (opinion, not self-identification)

Implementation
--------------
Pattern matching is intentionally simple — lowercase substring checks.
This avoids dependency on an NLP library while being reliable enough for
the explicit self-identification phrases users actually type.

A second AI call for extraction is deliberately NOT used — that would add
latency, cost, and a failure point for every single chat turn.  Simple
pattern matching is fast, free, and explainable.

This hook is called AFTER the AI has already responded — it runs in the
background and never blocks or delays the reply to the user.
"""

from __future__ import annotations

import logging
import re

from app.services.user_memory_service import UserMemoryService

logger = logging.getLogger(__name__)

# ── CEFR level patterns ────────────────────────────────────────────────── #

_CEFR_PATTERNS = [
    # "my level is B2", "I'm at B2 level", "I am B2", "level B2"
    r"\bmy (?:english )?level is ([a-c][1-2])\b",
    r"\bi[' ]?m (?:at )?([a-c][1-2])(?: level)?\b",
    r"\bi am (?:at )?([a-c][1-2])(?: level)?\b",
    r"\blevel[: ]+([a-c][1-2])\b",
    r"\b([a-c][1-2]) level\b",
]

# ── Learning goal patterns ─────────────────────────────────────────────── #

_GOAL_PATTERNS = [
    # "my goal is IELTS", "I'm studying for TOEFL", "I want to pass IELTS"
    r"(?:my goal is|i[' ]?m (?:studying|preparing) for|i want to (?:pass|take|prepare for))\s+(.{3,40}?)(?:\.|,|$)",
    r"(?:goal|aim|objective)[: ]+(.{3,40}?)(?:\.|,|$)",
]

# ── Weakness / struggle patterns ───────────────────────────────────────── #

_STRUGGLE_PATTERNS = [
    # "I struggle with conditionals", "I find articles difficult", "I'm bad at tenses"
    r"(?:i (?:struggle|find it hard|have trouble|have difficulty)|i[' ]?m (?:bad at|weak in|not good at)) (?:with |at |in )?(.{3,40}?)(?:\.|,|$)",
    r"(?:my weakness is|i[' ]?m weak (?:at|in|with)) (.{3,40}?)(?:\.|,|$)",
]

# ── Topic interest patterns ────────────────────────────────────────────── #

_INTEREST_PATTERNS = [
    # "I love programming", "I'm interested in science", "I like business"
    r"(?:i love|i[' ]?m interested in|i like|i enjoy|i[' ]?m passionate about) (.{3,40}?)(?:\.|,|$)",
    r"(?:my (?:hobby|interest|passion) is) (.{3,40}?)(?:\.|,|$)",
]

_VALID_CEFR = {"A1", "A2", "B1", "B2", "C1", "C2"}


class MemoryUpdateHook:
    """Scans a user message for explicit self-identification and updates UserMemory.

    Designed to be called fire-and-forget after every chat turn.
    All failures are logged as warnings — never propagated to the caller.
    """

    def __init__(self, memory_service: UserMemoryService) -> None:
        self._memory = memory_service

    async def process(self, user_id: int, user_message: str) -> None:
        """Scan `user_message` for persistent facts and persist them.

        Args:
            user_id:      Internal users.id PK.
            user_message: The raw text the user typed this turn.
        """
        text = user_message.lower().strip()

        try:
            await self._maybe_update_level(user_id, text)
        except Exception:
            logger.warning("MemoryUpdateHook: level update failed uid=%s", user_id, exc_info=True)

        try:
            await self._maybe_update_goal(user_id, text)
        except Exception:
            logger.warning("MemoryUpdateHook: goal update failed uid=%s", user_id, exc_info=True)

        try:
            await self._maybe_update_struggles(user_id, text)
        except Exception:
            logger.warning("MemoryUpdateHook: struggle update failed uid=%s", user_id, exc_info=True)

        try:
            await self._maybe_update_interests(user_id, text)
        except Exception:
            logger.warning("MemoryUpdateHook: interest update failed uid=%s", user_id, exc_info=True)

    # ── Private matchers ───────────────────────────────────────────────── #

    async def _maybe_update_level(self, user_id: int, text: str) -> None:
        for pattern in _CEFR_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                candidate = m.group(1).strip().upper()
                if candidate in _VALID_CEFR:
                    result = await self._memory.set_english_level(user_id, candidate)
                    if result:
                        logger.info(
                            "MemoryUpdateHook: set english_level=%r for uid=%s",
                            candidate, user_id,
                        )
                    return  # only process first match

    async def _maybe_update_goal(self, user_id: int, text: str) -> None:
        for pattern in _GOAL_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                goal = m.group(1).strip().rstrip(".,!?").strip()
                if 3 <= len(goal) <= 80:
                    # Restore title-case for proper nouns (IELTS, TOEFL, etc.)
                    goal = goal.title() if goal.isupper() or goal.islower() else goal
                    result = await self._memory.set_learning_goal(user_id, goal)
                    if result:
                        logger.info(
                            "MemoryUpdateHook: set learning_goal=%r for uid=%s",
                            goal, user_id,
                        )
                    return

    async def _maybe_update_struggles(self, user_id: int, text: str) -> None:
        for pattern in _STRUGGLE_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                weakness = m.group(1).strip().rstrip(".,!?").strip()
                if 2 <= len(weakness) <= 60:
                    await self._memory.record_weak_word(user_id, weakness)
                    logger.info(
                        "MemoryUpdateHook: recorded weakness=%r for uid=%s",
                        weakness, user_id,
                    )
                    return

    async def _maybe_update_interests(self, user_id: int, text: str) -> None:
        for pattern in _INTEREST_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                interest = m.group(1).strip().rstrip(".,!?").strip()
                if 2 <= len(interest) <= 60:
                    await self._memory.set_active_topic(user_id, interest)
                    logger.info(
                        "MemoryUpdateHook: set active_topic=%r for uid=%s",
                        interest, user_id,
                    )
                    return
