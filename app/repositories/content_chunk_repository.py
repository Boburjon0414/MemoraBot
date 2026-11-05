"""Data-access layer for the `content_chunks` table."""

from __future__ import annotations

import logging
from typing import Sequence

from sqlalchemy import delete, select

from app.database.models.content_chunk import ContentChunk
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ContentChunkRepository(BaseRepository[ContentChunk]):
    """Repository for bulk creation and retrieval of content chunks."""

    model = ContentChunk

    async def create_bulk(self, chunks: list[ContentChunk]) -> list[ContentChunk]:
        """Insert a list of ContentChunk rows and return them with IDs populated.

        Uses a single session.add_all() + flush() for efficiency — avoids
        N individual INSERT round-trips for a 200-chunk document.
        """
        if not chunks:
            return []
        self._session.add_all(chunks)
        await self._session.flush()
        for chunk in chunks:
            await self._session.refresh(chunk)
        return chunks

    async def get_by_source(self, source_id: int) -> Sequence[ContentChunk]:
        """Return all chunks for `source_id`, ordered by chunk_index."""
        result = await self._session.execute(
            select(ContentChunk)
            .where(ContentChunk.source_id == source_id)
            .order_by(ContentChunk.chunk_index)
        )
        return result.scalars().all()

    async def delete_by_source(self, source_id: int) -> int:
        """Delete all chunk rows for `source_id`.  Returns count deleted.

        Called when a ContentSource is deleted (via service, not cascade,
        for explicit control) or when re-indexing requires a clean slate.
        """
        result = await self._session.execute(
            delete(ContentChunk)
            .where(ContentChunk.source_id == source_id)
        )
        await self._session.flush()
        deleted = result.rowcount or 0
        logger.debug(
            "ContentChunkRepository: deleted %d chunks for source_id=%s",
            deleted, source_id,
        )
        return deleted

    async def count_by_source(self, source_id: int) -> int:
        """Count chunks for `source_id` (useful for progress checks)."""
        from sqlalchemy import func
        result = await self._session.execute(
            select(func.count(ContentChunk.id))
            .where(ContentChunk.source_id == source_id)
        )
        return result.scalar_one() or 0
