"""ContentService: orchestrates the content ingestion pipeline.

Responsibilities
----------------
  create_source()  — creates a ContentSource row; stores text immediately for
                     TEXT sources (status → "ready") or marks as "pending" for
                     file-based sources that need async processing.
  process()        — runs the appropriate ContentProcessor on a source,
                     stores extracted text, and updates status to "ready"
                     or "failed".  Always returns the updated source without
                     raising — failures are captured in the row itself.
  index_source()   — chunks extracted_text via TextChunker, embeds each chunk
                     via Embedder, stores ContentChunk rows, updates chunk_count.
  search()         — embeds a query and returns top-K matching chunks across
                     specified source_ids via EmbeddingStore.
  get_for_user()   — lists all sources for a user (newest first).
  get_by_id()      — fetches a single source scoped to a user.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, UTC
from pathlib import Path

from app.database.models.content_chunk import ContentChunk
from app.database.models.content_source import (
    ContentSource,
    ContentSourceStatus,
    ContentSourceType,
)
from app.repositories.content_chunk_repository import ContentChunkRepository
from app.repositories.content_repository import ContentRepository
from app.services.content.chunker import TextChunker
from app.services.content.embedder import Embedder
from app.services.content.embedding_store import EmbeddingStore
from app.services.content.processor import (
    ContentProcessingError,
    ContentProcessorRegistry,
)

logger = logging.getLogger(__name__)

_TEMP_DIR = Path(__file__).parent.parent.parent / "temp"


class ContentService:
    """Domain service for content source lifecycle management."""

    def __init__(
        self,
        content_repo: ContentRepository,
        processor_registry: ContentProcessorRegistry,
        chunk_repo: ContentChunkRepository | None = None,
        embedder: Embedder | None = None,
        embedding_store: EmbeddingStore | None = None,
    ) -> None:
        self._repo = content_repo
        self._registry = processor_registry
        self._chunk_repo = chunk_repo
        self._embedder = embedder
        self._embedding_store = embedding_store
        self._chunker = TextChunker()

    # ── Create ─────────────────────────────────────────────────────────── #

    async def create_source(
        self,
        user_id: int,
        source_type: ContentSourceType,
        *,
        text: str | None = None,
        title: str | None = None,
        filename: str | None = None,
        file_bytes: bytes | None = None,
    ) -> ContentSource:
        """Create a new ContentSource row for `user_id`.

        For TEXT sources:
          - `text` must be provided.
          - The text is stored in `extracted_text` immediately.
          - Status is set to "ready" — no further processing needed.
          - `process()` is a no-op for these (PlainTextProcessor just
            validates and returns the text unchanged).

        For file-based sources (PDF, IMAGE, etc.):
          - `file_bytes` must be provided.
          - The bytes are written to `app/temp/<uuid>_<filename>`.
          - `raw_storage_key` is set to the relative path.
          - Status is "pending"; call `process(source.id)` to extract text.

        Args:
            user_id:     Internal `users.id` PK.
            source_type: The `ContentSourceType` enum value.
            text:        Raw text content (TEXT sources only).
            title:       Optional human-readable title.
            filename:    Original filename (file sources only).
            file_bytes:  Raw file bytes (file sources only).

        Returns:
            The persisted `ContentSource` row.

        Raises:
            ValueError: if the required arguments for the source type are missing.
        """
        if source_type == ContentSourceType.TEXT:
            if not text:
                raise ValueError(
                    "ContentService.create_source: `text` is required for TEXT sources."
                )
            return await self._repo.create(
                user_id=user_id,
                source_type=source_type.value,
                title=title or _auto_title(text),
                extracted_text=text,
                status=ContentSourceStatus.READY.value,
            )

        # File-based source: persist bytes, set to pending
        if not file_bytes:
            raise ValueError(
                f"ContentService.create_source: `file_bytes` is required for "
                f"{source_type.value!r} sources."
            )

        storage_key = await self._save_file(file_bytes, filename or "upload")
        return await self._repo.create(
            user_id=user_id,
            source_type=source_type.value,
            title=title or filename,
            original_filename=filename,
            raw_storage_key=storage_key,
            status=ContentSourceStatus.PENDING.value,
        )

    # ── Process ────────────────────────────────────────────────────────── #

    async def process(self, source_id: int) -> ContentSource | None:
        """Run the registered processor on `source_id` and update its status.

        This method:
          1. Fetches the source.
          2. Looks up the correct processor in the registry.
          3. Calls processor.extract_text() to get the text.
          4. Calls processor.extract_metadata() for display metadata.
          5. Stores the results and sets status="ready".
          6. On any failure: sets status="failed", stores error_message.

        Never raises — all outcomes are captured in the row.

        Returns:
            The updated ContentSource row, or None if source_id not found.
        """
        source = await self._repo.get_by_id(source_id)
        if source is None:
            logger.warning("ContentService.process: source_id=%s not found", source_id)
            return None

        processor = self._registry.get(source.source_type)
        if processor is None:
            error = (
                f"No processor registered for source_type={source.source_type!r}. "
                f"Registered types: {self._registry.supported_types}"
            )
            logger.error("ContentService.process: %s", error)
            return await self._repo.update_status(
                source_id,
                status=ContentSourceStatus.FAILED.value,
                error_message=error,
                processed_at=datetime.now(UTC).replace(tzinfo=None),
            )

        # Mark as processing (prevents duplicate concurrent runs)
        await self._repo.update_status(
            source_id, status=ContentSourceStatus.PROCESSING.value
        )

        try:
            extracted_text = await processor.extract_text(source)
            metadata = await processor.extract_metadata(source)

            title = metadata.get("title") or source.title
            return await self._repo.update_status(
                source_id,
                status=ContentSourceStatus.READY.value,
                extracted_text=extracted_text,
                title=title,
                processed_at=datetime.now(UTC).replace(tzinfo=None),
            )

        except ContentProcessingError as exc:
            logger.warning(
                "ContentService.process: processor failed for source_id=%s — %s",
                source_id, exc,
            )
            return await self._repo.update_status(
                source_id,
                status=ContentSourceStatus.FAILED.value,
                error_message=str(exc),
                processed_at=datetime.now(UTC).replace(tzinfo=None),
            )
        except Exception:
            logger.exception(
                "ContentService.process: unexpected error for source_id=%s", source_id
            )
            return await self._repo.update_status(
                source_id,
                status=ContentSourceStatus.FAILED.value,
                error_message="Unexpected processing error. Please try again.",
                processed_at=datetime.now(UTC).replace(tzinfo=None),
            )

    # ── Read ───────────────────────────────────────────────────────────── #

    async def get_for_user(
        self,
        user_id: int,
        *,
        status: str | None = None,
    ) -> list[ContentSource]:
        """Return all sources for `user_id`, newest first."""
        return list(await self._repo.get_by_user(user_id, status=status))

    async def get_by_id(
        self,
        user_id: int,
        source_id: int,
    ) -> ContentSource | None:
        """Fetch a source by PK, scoped to `user_id`.  Returns None if not found."""
        return await self._repo.get_by_id_and_user(source_id, user_id)

    # ── Step 6: Chunking + Embedding ───────────────────────────────────── #

    async def index_source(self, source_id: int) -> ContentSource | None:
        """Chunk and embed a processed source, storing ContentChunk rows.

        Pipeline:
          1. Fetch the source; verify it is in "ready" status.
          2. Split extracted_text into overlapping windows via TextChunker.
          3. Embed each window via Embedder (batched).
          4. Persist ContentChunk rows via ContentChunkRepository.
          5. Persist embeddings via EmbeddingStore.
          6. Update source.chunk_count.

        Returns the updated ContentSource, or None if not found.
        Sets status="failed" if chunking or embedding fails.

        Requires chunk_repo, embedder, and embedding_store to be provided
        to the constructor.  Logs a clear error and returns None if they
        are missing (prevents crashes in environments without embedding
        support configured).
        """
        if not self._chunk_repo or not self._embedder or not self._embedding_store:
            logger.error(
                "ContentService.index_source: chunk_repo/embedder/embedding_store "
                "not configured — cannot index source_id=%s", source_id
            )
            return None

        source = await self._repo.get_by_id(source_id)
        if source is None:
            logger.warning("ContentService.index_source: source_id=%s not found", source_id)
            return None

        if source.status != ContentSourceStatus.READY.value:
            logger.warning(
                "ContentService.index_source: source_id=%s status=%r — "
                "must be 'ready' before indexing", source_id, source.status
            )
            return source

        if not source.extracted_text:
            logger.warning(
                "ContentService.index_source: source_id=%s has no extracted_text", source_id
            )
            return source

        try:
            # 1. Delete any existing chunks (supports re-indexing)
            await self._chunk_repo.delete_by_source(source_id)

            # 2. Split into windows
            texts = self._chunker.chunk(source.extracted_text)
            if not texts:
                logger.info(
                    "ContentService.index_source: source_id=%s produced 0 chunks "
                    "(text too short or empty after chunking)", source_id
                )
                return await self._repo.update_status(source_id, status=ContentSourceStatus.READY.value, chunk_count=0)

            # 3. Embed all chunks in one batch call
            embeddings = await self._embedder.embed_batch(texts)

            # 4. Build ContentChunk rows
            chunk_rows = [
                ContentChunk(
                    source_id=source_id,
                    chunk_index=i,
                    text=text,
                    token_count=len(text.split()),
                    embedding_model=self._embedder.model_name,
                )
                for i, text in enumerate(texts)
            ]
            persisted = await self._chunk_repo.create_bulk(chunk_rows)

            # 5. Store embeddings on each row
            for chunk, embedding in zip(persisted, embeddings):
                await self._embedding_store.upsert(
                    chunk, embedding, model_name=self._embedder.model_name
                )

            # 6. Update chunk_count on the source
            updated = await self._repo.update_status(
                source_id,
                status=ContentSourceStatus.READY.value,
                chunk_count=len(persisted),
            )
            logger.info(
                "ContentService.index_source: source_id=%s indexed %d chunks "
                "with model=%r", source_id, len(persisted), self._embedder.model_name
            )
            return updated

        except Exception:
            logger.exception(
                "ContentService.index_source: unexpected error for source_id=%s", source_id
            )
            return await self._repo.update_status(
                source_id,
                status=ContentSourceStatus.FAILED.value,
                error_message="Indexing failed unexpectedly. Please try again.",
            )

    async def search(
        self,
        query: str,
        source_ids: list[int],
        top_k: int = 5,
        min_similarity: float = 0.0,
    ) -> list[tuple[ContentChunk, float]]:
        """Embed `query` and return the top-K most similar chunks.

        Args:
            query:          The search query text.
            source_ids:     Restrict search to chunks from these sources only.
            top_k:          Maximum number of results.
            min_similarity: Minimum cosine similarity to include in results.

        Returns:
            List of (ContentChunk, similarity_score) pairs, best first.
            Returns [] if embedder/store not configured or source_ids empty.
        """
        if not self._embedder or not self._embedding_store:
            logger.error(
                "ContentService.search: embedder/embedding_store not configured"
            )
            return []

        if not source_ids:
            return []

        query_embedding = await self._embedder.embed(query)
        return await self._embedding_store.search(
            query_embedding,
            source_ids=source_ids,
            top_k=top_k,
            min_similarity=min_similarity,
        )

    # ── Private helpers ────────────────────────────────────────────────── #

    async def _save_file(self, file_bytes: bytes, filename: str) -> str:
        """Write `file_bytes` to a unique path under app/temp/.

        Returns the relative path string (used as raw_storage_key).
        The write is done in a thread pool to avoid blocking the event loop.
        """
        _TEMP_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = Path(filename).name  # strip any directory components
        storage_key = f"temp/{uuid.uuid4().hex}_{safe_name}"
        abs_path = Path(__file__).parent.parent.parent / storage_key

        await asyncio.to_thread(abs_path.write_bytes, file_bytes)
        logger.debug("ContentService: saved file to %s (%d bytes)", abs_path, len(file_bytes))
        return storage_key


def _auto_title(text: str, max_length: int = 60) -> str:
    """Generate a short title from the first line of `text`."""
    first_line = text.strip().split("\n")[0].strip()
    if len(first_line) <= max_length:
        return first_line or "Untitled"
    return first_line[:max_length].rstrip() + "…"
