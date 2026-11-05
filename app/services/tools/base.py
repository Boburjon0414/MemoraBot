"""Shared contracts for the Tool Calling Layer.

Every tool in the registry implements `PlatformTool` and returns a `ToolResult`.
No tool accesses repositories directly — each tool receives a `ToolContext`
that contains the session-scoped repositories it is allowed to use.

Design principles
-----------------
1. Tools are READ-ONLY. No tool modifies the database. Writes happen through
   the service layer, not through tools.
2. Tools are provider-independent. Neither the tool interface nor the registry
   knows about Gemini, Groq, or any other model.
3. Tools are self-describing. Each tool defines its own `definition` property
   so the registry can expose a catalogue to the planner and, in future, to
   the LLM itself as function-calling schemas.
4. Tools are independently guarded. A failure in one tool never fails the
   whole request — it returns an empty `ToolResult` with the error captured
   in `error`.

ToolContext
-----------
A value object injected by ServicesMiddleware into every tool call.
It carries the same session-scoped repositories that handlers already use,
so tools never open their own DB sessions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.repositories.activity_repository import ActivityRepository
    from app.repositories.content_repository import ContentRepository
    from app.repositories.content_chunk_repository import ContentChunkRepository
    from app.repositories.feature_output_repository import FeatureOutputRepository
    from app.repositories.grammar_topic_repository import GrammarTopicRepository
    from app.repositories.user_grammar_progress_repository import UserGrammarProgressRepository
    from app.repositories.user_memory_repository import UserMemoryRepository
    from app.repositories.vocabulary_repository import VocabularyRepository
    from app.services.activity_service import ActivityService
    from app.services.context.user_context import UserContext
    from app.services.content.content_service import ContentService
    from app.services.content.embedding_store import EmbeddingStore
    from app.services.content.embedder import Embedder


@dataclass
class ToolContext:
    """Session-scoped dependencies injected into every tool call.

    Tools read from these repositories; they never import or construct
    repositories themselves. This keeps tools testable with mock contexts.
    """
    user_id: int
    user_context: "UserContext"
    activity_repo: "ActivityRepository"
    vocabulary_repo: "VocabularyRepository"
    feature_output_repo: "FeatureOutputRepository"
    memory_repo: "UserMemoryRepository"
    content_repo: "ContentRepository"
    content_chunk_repo: "ContentChunkRepository"
    activity_service: "ActivityService"
    grammar_topic_repo: "GrammarTopicRepository | None" = None       # Feature: Grammar
    grammar_progress_repo: "UserGrammarProgressRepository | None" = None  # Feature: Grammar
    embedder: "Embedder | None" = None
    embedding_store: "EmbeddingStore | None" = None


@dataclass
class ToolResult:
    """The return type of every tool call.

    `data` is the payload — a dict of key → value pairs that ContextBuilder
    merges into AIContext. Callers check `success` before reading `data`.

    `error` is a human-readable description of what went wrong (if anything).
    It is NEVER injected into AI prompts — it is only for internal logging.

    `tool_name` is set by the registry after execution for traceability.
    """
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    tool_name: str = ""

    @classmethod
    def ok(cls, tool_name: str, **data: Any) -> "ToolResult":
        return cls(success=True, data=dict(data), tool_name=tool_name)

    @classmethod
    def empty(cls, tool_name: str) -> "ToolResult":
        """Successful call that returned no data (e.g. no words this week)."""
        return cls(success=True, data={}, tool_name=tool_name)

    @classmethod
    def fail(cls, tool_name: str, error: str) -> "ToolResult":
        return cls(success=False, data={}, error=error, tool_name=tool_name)


@dataclass(frozen=True)
class ToolParameter:
    """Describes one parameter a tool accepts."""
    name: str
    type: str          # "int" | "str" | "float" | "bool" | "list[str]"
    description: str
    required: bool = True
    default: Any = None


@dataclass(frozen=True)
class ToolDefinition:
    """Self-description of a tool — used by the planner and future LLM schemas.

    `features` lists which platform features use this tool.  Used by the
    planner to filter the tool set for a given feature context.
    """
    name: str
    description: str
    parameters: list[ToolParameter]
    return_description: str
    features: list[str] = field(default_factory=list)
    # e.g. ["chat", "quiz", "flashcards", "summary", "presentation"]


class PlatformTool(ABC):
    """Abstract base class every MemoraBot tool must implement.

    A tool is stateless. Instantiated once at startup (stored in
    ToolRegistry), called many times with different ToolContexts.

    execute() receives only what is in ToolContext + kwargs. It MUST NOT:
      - Import repositories itself.
      - Open DB sessions.
      - Call other tools directly (the planner orchestrates tool chains).
      - Modify any database row.
      - Raise exceptions to the caller — catch and return ToolResult.fail().
    """

    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Return the self-description of this tool."""
        raise NotImplementedError

    @abstractmethod
    async def execute(
        self,
        context: ToolContext,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute the tool and return a ToolResult.

        Never raises. Catches all exceptions and returns ToolResult.fail().
        """
        raise NotImplementedError
