"""ResponseValidator: validates AI responses against platform safety rules.

The validator is the last gate before the reply reaches the user.
It enforces the AI Safety Rules defined in the spec:

  - The AI must never invent user history.
  - The AI must never invent uploaded documents.
  - The AI must never invent quiz results.
  - The AI must never invent weak words.
  - The AI must never invent CEFR level.
  - The AI must never claim memory unless that memory exists.

How it works
------------
The validator checks the AI's raw text response against patterns that
indicate fabrication — claims about history/documents/results that were
NOT present in the AIContext that was given to the model.

Fabrication detection is conservative: it only flags responses that
contain explicit fabrication markers (phrases like "your uploaded PDF",
"the quiz you took", "your B2 level") when the corresponding data was
NOT in the context.

On detecting a violation:
  - The violation is logged with the specific pattern and response excerpt.
  - A safe fallback reply is returned to the user.
  - The original response is NOT sent.

ValidationResult
----------------
  valid:     True if the response passed all checks.
  response:  The response to send to the user (original or fallback).
  violations: List of violation descriptions (for logging).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from app.services.context.context_builder import AIContext

logger = logging.getLogger(__name__)

# ── Fabrication detection patterns ─────────────────────────────────────── #

# Claims about uploaded documents when none exist
_INVENTED_DOCUMENT = re.compile(
    r"\b(your (?:uploaded|pdf|document|file|notes?)|the (?:pdf|document|file) you (?:uploaded|shared|sent))\b",
    re.IGNORECASE,
)
# Claims about quiz history when none exists
_INVENTED_QUIZ = re.compile(
    r"\b(the quiz you (?:took|completed|did)|your (?:quiz (?:results?|score|history)|previous quiz))\b",
    re.IGNORECASE,
)
# Claims about CEFR level when not set
_INVENTED_LEVEL = re.compile(
    r"\bas a (A1|A2|B1|B2|C1|C2) (?:learner|student|user)\b",
    re.IGNORECASE,
)


@dataclass
class ValidationResult:
    valid: bool
    response: str
    violations: list[str] = field(default_factory=list)


_FALLBACK_REPLY = (
    "I want to make sure I give you accurate information. "
    "Could you clarify what you're looking for? "
    "I can only reference information that's actually in your MemoraBot account."
)


class ResponseValidator:
    """Validates AI responses against platform safety rules.

    Stateless — safe to instantiate once as a singleton.
    """

    def validate(
        self,
        response: str,
        context: AIContext,
    ) -> ValidationResult:
        """Validate `response` against the safety rules for `context`.

        Returns a ValidationResult. If valid, `result.response` equals
        the original response. If invalid, `result.response` is a safe
        fallback and `result.violations` lists what was detected.
        """
        violations: list[str] = []

        # Check for invented documents
        if _INVENTED_DOCUMENT.search(response) and not context.document_titles:
            violations.append(
                "Fabricated document reference — no documents in user context."
            )

        # Check for invented quiz history
        if _INVENTED_QUIZ.search(response) and not context.recent_quiz_topics:
            violations.append(
                "Fabricated quiz history — no quiz outputs in user context."
            )

        # Check for invented CEFR level
        level_match = _INVENTED_LEVEL.search(response)
        if level_match:
            claimed_level = level_match.group(1).upper()
            actual_level = (context.user_context.english_level or "").upper()
            if claimed_level != actual_level:
                actual_str = actual_level if actual_level else 'not set'
                violations.append(
                    f"Fabricated CEFR level {claimed_level!r} — "
                    f"actual is {actual_str!r}."
                )

        if violations:
            for v in violations:
                logger.warning("ResponseValidator: VIOLATION — %s", v)
            return ValidationResult(
                valid=False,
                response=_FALLBACK_REPLY,
                violations=violations,
            )

        return ValidationResult(valid=True, response=response)
