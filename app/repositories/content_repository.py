"""Data-access layer for the `content_sources` table.

All SQL lives here.  ContentService contains the business rules
(when to process, what status transitions are valid); this repository
just executes the queries.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Sequence

from sqlalchemy import select

from app.database.models.content_source import ContentSource, ContentSourceStatus
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ContentRepository(BaseRepository[ContentSource]):
    """Repository for creating and querying content sources."""

    model = ContentSource

    async def create(
        self,
        *,
        user_id: int,
        source_type: str,
        title: str | None = None,
        extracted_text: str | None = None,
        raw_storage_key: str | None = None,
        original_filename: str | None = None,
        status: str = ContentSourceStatus.PENDING.value,
    ) -> ContentSource:
        """Insert and return a new ContentSource row."""
        source = ContentSource(
            user_id=user_id,
            source_type=source_type,
            title=title,
            extracted_text=extracted_text,
            raw_storage_key=raw_storage_key,
            original_filename=original_filename,
            status=status,
        )
        return await self.add(source)

    async def get_by_user(
        self,
        user_id: int,
        *,
        status: str | None = None,
    ) -> Sequence[ContentSource]:
        """Return all sources for `user_id`, optionally filtered by status.

        Results are ordered newest-first so the "My Sources" list always
        shows the most recently added source at the top.
        """
        stmt = (
            select(ContentSource)
            .where(ContentSource.user_id == user_id)
            .order_by(ContentSource.created_at.desc())
        )
        if status is not None:
            stmt = stmt.where(ContentSource.status == status)

        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_by_id_and_user(
        self,
        source_id: int,
        user_id: int,
    ) -> ContentSource | None:
        """Fetch a source by PK, but only if it belongs to `user_id`.

        Returns None both when the row doesn't exist and when it belongs
        to a different user — callers should not distinguish these cases
        (avoids user enumeration).
        """
        result = await self._session.execute(
            select(ContentSource)
            .where(ContentSource.id == source_id)
            .where(ContentSource.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        source_id: int,
        *,
        status: str,
        extracted_text: str | None = None,
        error_message: str | None = None,
        title: str | None = None,
        chunk_count: int | None = None,
        processed_at: datetime | None = None,
    ) -> ContentSource | None:
        """Update processing-state fields on an existing source.

        Only the fields explicitly passed (non-None kwargs) are written —
        passing None for a field leaves its current DB value unchanged.
        Returns the refreshed row, or None if the source doesn't exist.
        """
        source = await self.get_by_id(source_id)
        if source is None:
            logger.warning(
                "ContentRepository.update_status: source_id=%s not found", source_id
            )
            return None

        source.status = status
        if extracted_text is not None:
            source.extracted_text = extracted_text
        if error_message is not None:
            source.error_message = error_message
        if title is not None:
            source.title = title
        if chunk_count is not None:
            source.chunk_count = chunk_count
        if processed_at is not None:
            source.processed_at = processed_at

        await self._session.flush()
        await self._session.refresh(source)
        return source

    async def count_by_user(self, user_id: int) -> int:
        """Count all sources owned by `user_id`."""
        from sqlalchemy import func
        result = await self._session.execute(
            select(func.count(ContentSource.id))
            .where(ContentSource.user_id == user_id)
        )
        return result.scalar_one() or 0
