"""FeatureOutputService: saves, loads, and manages AI-generated artifacts.

This is the only layer allowed to touch `payload_json` — callers always
work with typed Pydantic models, never raw JSON strings.

Core contract
-------------
  save()          — serialise a Pydantic payload → persist → return row.
  load()          — fetch row → deserialise → validate against schema → return typed model.
  update_payload()— replace an existing payload (e.g. append a Q&A turn).
  list_for_user() — list outputs, optionally filtered by type.
  archive()       — soft-delete.

Error handling
--------------
  save() raises ValueError for invalid payloads (Pydantic validation).
  load() returns None for missing rows OR for rows whose payload fails
         schema validation (logged as warning, never raised to caller).
  All repository errors propagate unchanged — they are genuine infrastructure
  failures the caller should handle.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, UTC
from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError

from app.database.models.feature_output import FeatureOutput, OutputType
from app.repositories.feature_output_repository import FeatureOutputRepository
from app.services.outputs.schemas import (
    ChatSessionPayload,
    FlashcardPayload,
    PresentationOutlinePayload,
    QASessionPayload,
    QuizPayload,
    SummaryPayload,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Map OutputType → its canonical Pydantic schema.
# Used by load() when no explicit schema is provided.
_DEFAULT_SCHEMAS: dict[str, type[BaseModel]] = {
    OutputType.QUIZ.value: QuizPayload,
    OutputType.FLASHCARD_SET.value: FlashcardPayload,
    OutputType.SUMMARY.value: SummaryPayload,
    OutputType.QA_SESSION.value: QASessionPayload,
    OutputType.CHAT_SESSION.value: ChatSessionPayload,
    OutputType.PRESENTATION_OUTLINE.value: PresentationOutlinePayload,
}


class FeatureOutputService:
    """Domain service for AI-generated artifact persistence."""

    def __init__(self, repo: FeatureOutputRepository) -> None:
        self._repo = repo

    # ── Write ──────────────────────────────────────────────────────────── #

    async def save(
        self,
        user_id: int,
        output_type: OutputType,
        payload: BaseModel,
        *,
        title: str | None = None,
        content_source_id: int | None = None,
    ) -> FeatureOutput:
        """Serialise `payload` and persist a new FeatureOutput row.

        Args:
            user_id:           Owner of the artifact.
            output_type:       The OutputType enum value for this artifact.
            payload:           A Pydantic model instance (QuizPayload, etc.).
            title:             Optional display title; auto-generated if None.
            content_source_id: FK to ContentSource if from a document.

        Returns:
            The persisted FeatureOutput row with its generated id.

        Raises:
            ValueError: if `payload` is not a valid Pydantic model.
        """
        if not isinstance(payload, BaseModel):
            raise ValueError(
                f"FeatureOutputService.save: payload must be a Pydantic BaseModel, "
                f"got {type(payload).__name__}"
            )

        payload_json = payload.model_dump_json()
        display_title = title or _auto_title(output_type, payload)

        output = await self._repo.create(
            user_id=user_id,
            output_type=output_type.value,
            payload_json=payload_json,
            title=display_title,
            content_source_id=content_source_id,
        )
        logger.debug(
            "FeatureOutputService.save: user_id=%s type=%r id=%s title=%r",
            user_id, output_type.value, output.id, display_title,
        )
        return output

    async def update_payload(
        self,
        output_id: int,
        payload: BaseModel,
        *,
        title: str | None = None,
    ) -> FeatureOutput | None:
        """Replace the payload of an existing output (e.g. append a Q&A turn).

        Returns the updated row, or None if output_id not found.
        """
        updated = await self._repo.update_payload(
            output_id,
            payload_json=payload.model_dump_json(),
            title=title,
        )
        if updated:
            logger.debug(
                "FeatureOutputService.update_payload: id=%s updated", output_id
            )
        return updated

    async def archive(self, user_id: int, output_id: int) -> bool:
        """Soft-delete an output.  Returns True if found and archived."""
        result = await self._repo.archive(output_id, user_id)
        if result:
            logger.debug(
                "FeatureOutputService.archive: user_id=%s id=%s archived",
                user_id, output_id,
            )
        return result

    # ── Read ───────────────────────────────────────────────────────────── #

    async def load(
        self,
        user_id: int,
        output_id: int,
        schema: Type[T],
    ) -> T | None:
        """Fetch an output by ID and deserialise its payload into `schema`.

        Returns:
            A validated instance of `schema`, or None when:
              - The row doesn't exist / belongs to another user.
              - The payload fails schema validation (logged as warning).

        Never raises for schema validation errors — callers can treat
        None as "not found or incompatible" and handle gracefully.
        """
        output = await self._repo.get_by_id_and_user(output_id, user_id)
        if output is None:
            return None
        return _parse_payload(output, schema)

    async def load_raw(
        self,
        user_id: int,
        output_id: int,
    ) -> FeatureOutput | None:
        """Fetch the raw FeatureOutput row without deserialising payload.

        Useful when the caller needs row metadata (created_at, title) and
        will handle payload parsing itself.
        """
        return await self._repo.get_by_id_and_user(output_id, user_id)

    async def list_for_user(
        self,
        user_id: int,
        output_type: OutputType | None = None,
        *,
        include_archived: bool = False,
    ) -> list[FeatureOutput]:
        """Return all outputs for `user_id`, newest first.

        Args:
            user_id:          Owner filter.
            output_type:      Optional type filter.
            include_archived: Whether to include archived (soft-deleted) rows.
        """
        rows = await self._repo.get_by_user(
            user_id,
            output_type=output_type.value if output_type else None,
            include_archived=include_archived,
        )
        return list(rows)

    async def list_typed(
        self,
        user_id: int,
        output_type: OutputType,
        schema: Type[T],
        *,
        include_archived: bool = False,
    ) -> list[tuple[FeatureOutput, T]]:
        """Return outputs with their parsed payloads.

        Returns a list of (FeatureOutput, parsed_payload) pairs.
        Rows whose payload fails schema validation are skipped (with a
        warning log) rather than crashing the whole list.
        """
        rows = await self._repo.get_by_user(
            user_id,
            output_type=output_type.value,
            include_archived=include_archived,
        )
        result: list[tuple[FeatureOutput, T]] = []
        for row in rows:
            parsed = _parse_payload(row, schema)
            if parsed is not None:
                result.append((row, parsed))
        return result

    async def count(
        self,
        user_id: int,
        output_type: OutputType | None = None,
    ) -> int:
        """Count non-archived outputs for `user_id`."""
        return await self._repo.count_by_user(
            user_id,
            output_type=output_type.value if output_type else None,
        )


# ── Private helpers ────────────────────────────────────────────────────── #

def _parse_payload(output: FeatureOutput, schema: Type[T]) -> T | None:
    """Deserialise and validate output.payload_json against `schema`.

    Returns None (with a warning) if the JSON is malformed or fails
    schema validation — never raises.
    """
    try:
        data = json.loads(output.payload_json)
        return schema.model_validate(data)
    except (json.JSONDecodeError, ValidationError, Exception) as exc:
        logger.warning(
            "_parse_payload: failed to parse output id=%s as %s — %s",
            output.id, schema.__name__, exc,
        )
        return None


def _auto_title(output_type: OutputType, payload: BaseModel) -> str:
    """Generate a short display title from the output type and payload."""
    now_str = datetime.now(UTC).strftime("%b %d %H:%M")

    # Type-specific title extraction
    if hasattr(payload, "topic") and payload.topic:  # type: ignore[union-attr]
        topic = payload.topic  # type: ignore[union-attr]
        label = {
            OutputType.QUIZ: "Quiz",
            OutputType.FLASHCARD_SET: "Flashcards",
            OutputType.SUMMARY: "Summary",
        }.get(output_type, output_type.value.replace("_", " ").title())
        return f"{label}: {topic}"

    if hasattr(payload, "title") and payload.title:  # type: ignore[union-attr]
        return payload.title  # type: ignore[union-attr]

    label = output_type.value.replace("_", " ").title()
    return f"{label} — {now_str}"
