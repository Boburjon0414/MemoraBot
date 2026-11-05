"""Document tools — read ContentSources and ContentChunks."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.database.models.content_source import ContentSourceStatus
from app.services.tools.base import (
    PlatformTool, ToolContext, ToolDefinition, ToolParameter, ToolResult,
)

logger = logging.getLogger(__name__)


class GetUploadedDocumentsTool(PlatformTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_uploaded_documents",
            description="Return the list of documents the user has uploaded (title, source_type, status).",
            parameters=[],
            return_description="Dict with key: documents (list of dicts with id, title, source_type, status).",
            features=["chat", "summary", "presentation"],
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            sources = await context.content_repo.get_by_user(
                context.user_id, status=ContentSourceStatus.READY.value
            )
            docs = [
                {
                    "id": s.id,
                    "title": s.title or f"Document {s.id}",
                    "source_type": s.source_type,
                    "chunk_count": s.chunk_count,
                }
                for s in sources
            ]
            return ToolResult.ok("get_uploaded_documents", documents=docs)
        except Exception as exc:
            logger.warning("get_uploaded_documents failed: %s", exc)
            return ToolResult.fail("get_uploaded_documents", str(exc))


class GetRecentDocumentTool(PlatformTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_recent_document",
            description="Return the most recently uploaded and processed document for the user.",
            parameters=[],
            return_description="Dict with keys: id, title, source_type, chunk_count, excerpt (first 500 chars of text).",
            features=["chat", "summary", "presentation"],
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            sources = await context.content_repo.get_by_user(
                context.user_id, status=ContentSourceStatus.READY.value
            )
            if not sources:
                return ToolResult.empty("get_recent_document")
            latest = sources[0]  # already ordered newest first
            excerpt = (latest.extracted_text or "")[:500]
            return ToolResult.ok(
                "get_recent_document",
                id=latest.id,
                title=latest.title or f"Document {latest.id}",
                source_type=latest.source_type,
                chunk_count=latest.chunk_count,
                excerpt=excerpt,
            )
        except Exception as exc:
            logger.warning("get_recent_document failed: %s", exc)
            return ToolResult.fail("get_recent_document", str(exc))


class GetDocumentChunksTool(PlatformTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_document_chunks",
            description="Return the text chunks of a specific document by its ID.",
            parameters=[
                ToolParameter("document_id", "int", "The ContentSource.id of the document."),
                ToolParameter("limit", "int", "Max chunks to return.", required=False, default=10),
            ],
            return_description="Dict with key: chunks (list of dicts with chunk_index, text, token_count).",
            features=["chat", "summary", "presentation"],
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            doc_id = int(kwargs.get("document_id", 0))
            limit = int(kwargs.get("limit", 10))

            # Verify ownership
            source = await context.content_repo.get_by_id_and_user(doc_id, context.user_id)
            if source is None:
                return ToolResult.fail("get_document_chunks", f"Document {doc_id} not found.")

            chunks = await context.content_chunk_repo.get_by_source(doc_id)
            chunk_list = [
                {
                    "chunk_index": c.chunk_index,
                    "text": c.text,
                    "token_count": c.token_count,
                    "page_number": c.page_number,
                }
                for c in list(chunks)[:limit]
            ]
            return ToolResult.ok("get_document_chunks", chunks=chunk_list, document_id=doc_id)
        except Exception as exc:
            logger.warning("get_document_chunks failed: %s", exc)
            return ToolResult.fail("get_document_chunks", str(exc))


class SearchDocumentChunksTool(PlatformTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="search_document_chunks",
            description="Semantic search over the user's uploaded document chunks. Returns the most relevant passages for a given query.",
            parameters=[
                ToolParameter("query", "str", "The search query to find relevant document passages."),
                ToolParameter("document_ids", "list[str]", "Optional list of document IDs to search (empty = all documents).", required=False, default=[]),
                ToolParameter("top_k", "int", "Number of results to return.", required=False, default=5),
            ],
            return_description="Dict with key: chunks (list of dicts with text, score, document_id, chunk_index).",
            features=["chat", "summary", "presentation"],
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            query = str(kwargs.get("query", ""))
            top_k = int(kwargs.get("top_k", 5))
            doc_ids_raw = kwargs.get("document_ids", [])

            if not query:
                return ToolResult.fail("search_document_chunks", "query parameter is required.")

            if not context.embedder or not context.embedding_store:
                return ToolResult.fail(
                    "search_document_chunks",
                    "Semantic search not configured (embedder/embedding_store unavailable)."
                )

            # Resolve source_ids: if none given, use all ready docs for this user
            if doc_ids_raw:
                source_ids = [int(d) for d in doc_ids_raw]
            else:
                sources = await context.content_repo.get_by_user(
                    context.user_id, status=ContentSourceStatus.READY.value
                )
                source_ids = [s.id for s in sources]

            if not source_ids:
                return ToolResult.empty("search_document_chunks")

            query_embedding = await context.embedder.embed(query)
            results = await context.embedding_store.search(
                query_embedding,
                source_ids=source_ids,
                top_k=top_k,
                min_similarity=0.0,
            )

            chunks = [
                {
                    "text": chunk.text,
                    "score": round(score, 4),
                    "document_id": chunk.source_id,
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number,
                }
                for chunk, score in results
            ]
            return ToolResult.ok("search_document_chunks", chunks=chunks, query=query)
        except Exception as exc:
            logger.warning("search_document_chunks failed: %s", exc)
            return ToolResult.fail("search_document_chunks", str(exc))
