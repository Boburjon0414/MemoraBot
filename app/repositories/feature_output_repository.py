"""Data-access layer for the `feature_outputs` table."""

from __future__ import annotations

import logging
from datetime import datetime, UTC
from typing import Sequence

from sqlalchemy import select

from app.database.models.feature_output import FeatureOutput
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class FeatureOutputRepository(BaseRepository[FeatureOutput]):
    """Repository for creating, fetching, and archiving feature outputs."""

    model = FeatureOutput

    async def create(
        self,
        *,
        user_id: int,
        output_type: str,
        payload_json: str,
        title: str | None = None,
        content_source_id: int | None = None,
    ) -> FeatureOutput:
        """Insert a new FeatureOutput row and return it with its PK."""
        output = FeatureOutput(
            user_id=user_id,
            output_type=output_type,
            payload_json=payload_json,
            title=title,
            content_source_id=content_source_id,
        )
        return await self.add(output)

    async def get_by_user(
        self,
        user_id: int,
        *,
        output_type: str | None = None,
        include_archived: bool = False,
    ) -> Sequence[FeatureOutput]:
        """Return feature outputs for `user_id`, newest first.

        Args:
            user_id:          Filter by owner.
            output_type:      Optional — restrict to one artifact type.
            include_archived: If False (default), hides archived outputs.
        """
        stmt = (
            select(FeatureOutput)
            .where(FeatureOutput.user_id == user_id)
            .order_by(FeatureOutput.created_at.desc())
        )
        if output_type is not None:
            stmt = stmt.where(FeatureOutput.output_type == output_type)
        if not include_archived:
            stmt = stmt.where(FeatureOutput.is_archived.is_(False))

        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_by_id_and_user(
        self,
        output_id: int,
        user_id: int,
    ) -> FeatureOutput | None:
        """Fetch by PK, scoped to `user_id`. Returns None if not found
        or if the row belongs to a different user."""
        result = await self._session.execute(
            select(FeatureOutput)
            .where(FeatureOutput.id == output_id)
            .where(FeatureOutput.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_payload(
        self,
        output_id: int,
        *,
        payload_json: str,
        title: str | None = None,
    ) -> FeatureOutput | None:
        """Replace the payload of an existing output (e.g. appending a new
        Q&A turn to a QASessionPayload) and bump updated_at."""
        output = await self.get_by_id(output_id)
        if output is None:
            logger.warning(
                "FeatureOutputRepository.update_payload: id=%s not found", output_id
            )
            return None
        output.payload_json = payload_json
        if title is not None:
            output.title = title
        output.updated_at = datetime.now(UTC).replace(tzinfo=None)
        await self._session.flush()
        await self._session.refresh(output)
        return output

    async def archive(self, output_id: int, user_id: int) -> bool:
        """Soft-delete an output by setting is_archived=True.

        Returns True if the row was found and updated, False otherwise.
        Scoped to `user_id` so users can only archive their own outputs.
        """
        output = await self.get_by_id_and_user(output_id, user_id)
        if output is None:
            return False
        output.is_archived = True
        output.updated_at = datetime.now(UTC).replace(tzinfo=None)
        await self._session.flush()
        return True

    async def get_recent_by_type(
        self,
        user_id: int,
        output_type: str,
        *,
        limit: int = 5,
        include_archived: bool = False,
    ) -> list[FeatureOutput]:
        """Return the most recent outputs of a specific type for `user_id`.

        Used by ContextBuilder to inject prior quiz/flashcard/summary/chat
        context into AI prompts without loading full payloads unnecessarily.
        """
        stmt = (
            select(FeatureOutput)
            .where(FeatureOutput.user_id == user_id)
            .where(FeatureOutput.output_type == output_type)
            .order_by(FeatureOutput.created_at.desc())
            .limit(limit)
        )
        if not include_archived:
            stmt = stmt.where(FeatureOutput.is_archived.is_(False))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_type(
        self,
        user_id: int,
        output_type: str | None = None,
    ) -> int:
        """Count outputs for `user_id`, optionally filtered by type."""
        from sqlalchemy import func
        stmt = (
            select(func.count(FeatureOutput.id))
            .where(FeatureOutput.user_id == user_id)
            .where(FeatureOutput.is_archived.is_(False))
        )
        if output_type is not None:
            stmt = stmt.where(FeatureOutput.output_type == output_type)
        result = await self._session.execute(stmt)
        return result.scalar_one() or 0

    async def count_by_user(
        self,
        user_id: int,
        output_type: str | None = None,
    ) -> int:
        """Alias of count_by_type — backward-compatible name for FeatureOutputService."""
        return await self.count_by_type(user_id, output_type)
