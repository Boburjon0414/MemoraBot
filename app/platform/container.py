"""PlatformContainer — owns every application-lifetime singleton resource.

Lifecycle
---------
1. `bot.py` calls `PlatformContainer(settings)`.
2. `bot.py` calls `await platform.initialize()` — builds all singletons.
3. `bot.py` passes `platform` to `ServicesMiddleware(platform=platform, ...)`.
4. `ServicesMiddleware.__call__()` reads `platform.ai_provider` and
   `platform.ai_router` per-request (cheap attribute reads, not construction).
5. `bot.py`'s `finally` block calls `await platform.shutdown()` — closes
   every resource in dependency order (reverse of construction order).

Adding a new singleton (e.g. vector store in Step 6)
-----------------------------------------------------
1. Add a private attribute (`self._vector_store: VectorStore | None = None`).
2. In `initialize()`, construct it after any dependencies it has.
3. Expose it via a `@property`.
4. In `shutdown()`, close it before any resources it depends on.
5. Pass it into `ServicesMiddleware.__init__()` as a new parameter.

Nothing in `ServicesMiddleware.__call__()` or any handler changes — they
always receive services, never raw singletons directly.

Current singletons (Step 4)
----------------------------
  ai_provider  (MnemonicProvider) — the gateway or single-provider instance
  ai_router    (AIRouter | None)  — the same object when gateway mode,
                                    None when single-provider legacy mode
"""

from __future__ import annotations

import logging

from app.config import Settings
from app.services.ai.base import MnemonicProvider
from app.services.ai.factory import create_ai_provider
from app.services.ai.gateway import AIGateway
from app.services.ai.router import AIRouter
from app.services.content.embedder import Embedder, MockEmbedder           # Step 6
from app.services.content.processor import ContentProcessorRegistry        # Step 5
from app.services.content.processors.plain_text_processor import PlainTextProcessor  # Step 5
from app.services.tools.registry import ToolRegistry                       # Feature A.2
from app.services.tools.user_tools import (                                # Feature A.2
    GetUserProfileTool, GetLearningGoalTool, GetCEFRLevelTool, GetActiveTopicTool,
)
from app.services.tools.vocabulary_tools import (                          # Feature A.2
    GetRecentWordsTool, GetSavedWordsTool, GetWeakWordsTool, GetRecentMnemonicsTool,
    GetVocabularyQuizWordsTool,                                            # Feature C.1
)
from app.services.tools.activity_tools import (                            # Feature A.2
    GetRecentActivityTool, GetActivityByTypeTool, GetStreakTool,
    GetLearningStatisticsTool, GetProgressSummaryTool,
)
from app.services.tools.output_tools import (                              # Feature A.2
    GetRecentQuizzesTool, GetRecentFlashcardsTool, GetRecentSummariesTool,
    GetRecentPresentationsTool, GetRecentChatSessionsTool,
)
from app.services.tools.document_tools import (                            # Feature A.2
    GetUploadedDocumentsTool, GetRecentDocumentTool,
    GetDocumentChunksTool, SearchDocumentChunksTool,
)
from app.services.tools.grammar_tools import (                             # Feature: Grammar
    GetStudiedGrammarTopicsTool, GetGrammarProgressTool, GetActiveGrammarTopicsTool,
)

logger = logging.getLogger(__name__)


class PlatformContainer:
    """Holds and manages application-lifetime singleton resources.

    Constructed once in `bot.py`.  All public properties are available
    after `await initialize()` returns.  Accessing them before that raises
    `RuntimeError` to catch ordering bugs early.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

        # Singletons — populated by initialize(), never by __init__.
        # Typed as Optional so the RuntimeError guard below can detect
        # uninitialised access instead of giving a confusing AttributeError.
        self._ai_provider: MnemonicProvider | None = None
        self._content_processor_registry: ContentProcessorRegistry | None = None  # Step 5
        self._embedder: Embedder | None = None                                     # Step 6
        self._tool_registry: ToolRegistry | None = None                            # Feature A.2
        self._is_initialized: bool = False

    # ── Lifecycle ──────────────────────────────────────────────────────── #

    async def initialize(self) -> None:
        """Construct all singletons in dependency order.

        Must be awaited before the bot starts polling.  Idempotent: calling
        it a second time is a no-op with a warning log (prevents accidental
        double-initialisation in test setups).
        """
        if self._is_initialized:
            logger.warning(
                "PlatformContainer.initialize() called more than once — ignoring."
            )
            return

        logger.info("PlatformContainer: initializing singletons…")

        # ── 1. AI provider (MnemonicProvider + optionally AIRouter) ───── #
        self._ai_provider = await create_ai_provider(self._settings)
        logger.info(
            "PlatformContainer: AI provider ready — %s (gateway=%s, router=%s)",
            self._ai_provider.name,
            isinstance(self._ai_provider, AIGateway),
            isinstance(self._ai_provider, AIRouter),
        )

        # ── 2. Content processor registry (Step 5) ────────────────────── #
        self._content_processor_registry = ContentProcessorRegistry()
        self._content_processor_registry.register(PlainTextProcessor())
        logger.info(
            "PlatformContainer: ContentProcessorRegistry ready — types=%s",
            self._content_processor_registry.supported_types,
        )

        # ── 3. Embedder (Step 6) ───────────────────────────────────────── #
        # Default: MockEmbedder (deterministic, no API keys required).
        # To switch to a real embedding model, replace MockEmbedder() here
        # with AIRouterEmbedder(self.ai_router) or a dedicated client.
        # The EMBEDDER_TYPE setting (future) will drive this selection.
        self._embedder = MockEmbedder()
        logger.info(
            "PlatformContainer: Embedder ready — model=%r dimensions=%d",
            self._embedder.model_name,
            self._embedder.dimensions,
        )

        # ── 4. Tool Registry (Feature A.2) ────────────────────────────── #
        self._tool_registry = ToolRegistry()
        for tool in [
            GetUserProfileTool(), GetLearningGoalTool(), GetCEFRLevelTool(), GetActiveTopicTool(),
            GetRecentWordsTool(), GetSavedWordsTool(), GetWeakWordsTool(), GetRecentMnemonicsTool(),
            GetVocabularyQuizWordsTool(),                                   # Feature C.1
            GetRecentActivityTool(), GetActivityByTypeTool(), GetStreakTool(),
            GetLearningStatisticsTool(), GetProgressSummaryTool(),
            GetRecentQuizzesTool(), GetRecentFlashcardsTool(), GetRecentSummariesTool(),
            GetRecentPresentationsTool(), GetRecentChatSessionsTool(),
            GetUploadedDocumentsTool(), GetRecentDocumentTool(),
            GetDocumentChunksTool(), SearchDocumentChunksTool(),
            GetStudiedGrammarTopicsTool(), GetGrammarProgressTool(),   # Feature: Grammar
            GetActiveGrammarTopicsTool(),                              # Feature: Grammar
        ]:
            self._tool_registry.register(tool)
        logger.info(
            "PlatformContainer: ToolRegistry ready — %d tools",
            len(self._tool_registry.all_tools()),
        )

        # ── Future singletons go here, in dependency order: ────────────── #
        #
        # Step 6 (ContentChunk + EmbeddingStore):
        #   self._embedder = MockEmbedder()   # or AIRouterEmbedder(self.ai_router)
        #   self._embedding_store = SQLiteEmbeddingStore()
        #
        # Each addition follows the same pattern: construct here, expose
        # via @property below, pass into ServicesMiddleware, close in shutdown().

        self._is_initialized = True
        logger.info("PlatformContainer: all singletons ready.")

    async def shutdown(self) -> None:
        """Close all singletons in reverse dependency order.

        Called by `bot.py`'s `finally` block.  Safe to call even if
        `initialize()` was never called (all attributes will be None).

        Shutdown errors are logged but do not re-raise — the process is
        exiting anyway, and we want every resource to get its close call
        regardless of whether a previous one fails.
        """
        logger.info("PlatformContainer: shutting down…")

        # ── Future resources closed first (reverse of init order) ─────── #
        # Step 6: await self._embedding_store.close()   (if it has a close)
        # Step 5: (no close needed for processor registry)

        # ── 1. AI provider last (other resources may have used it) ───── #
        if self._ai_provider is not None and isinstance(self._ai_provider, AIGateway):
            try:
                await self._ai_provider.close()
                logger.info("PlatformContainer: AI Gateway HTTP sessions closed.")
            except Exception:
                logger.exception(
                    "PlatformContainer: error closing AI Gateway — continuing shutdown."
                )

        self._is_initialized = False
        logger.info("PlatformContainer: shutdown complete.")

    # ── Properties (read-only access for ServicesMiddleware) ──────────── #

    def _require_initialized(self, name: str) -> None:
        if not self._is_initialized:
            raise RuntimeError(
                f"PlatformContainer.{name} accessed before initialize() was called. "
                "Call `await platform.initialize()` in bot.py before registering "
                "middlewares."
            )

    @property
    def ai_provider(self) -> MnemonicProvider:
        """The `MnemonicProvider` singleton (AIGateway or single-provider).

        Passed to `ServicesMiddleware` which derives a per-request
        `TierProxy` from it (in gateway mode) or uses it directly (legacy).
        """
        self._require_initialized("ai_provider")
        assert self._ai_provider is not None  # proven by _require_initialized
        return self._ai_provider

    @property
    def ai_router(self) -> AIRouter | None:
        """The `AIRouter` singleton, or None in legacy single-provider mode.

        This is the same object as `ai_provider` when running in gateway
        mode (because `AIGateway` implements both interfaces).  It is None
        when running with a `GeminiProvider`, `GroqProvider`, or
        `MockProvider` directly — those do not implement `AIRouter`.

        `ServicesMiddleware` injects this as `data["ai_router"]`.  Services
        that require `AIRouter` (AIChatService, RAGService, QuizService, …)
        should raise a clear error if they receive None rather than silently
        falling back to degraded behaviour.
        """
        self._require_initialized("ai_router")
        assert self._ai_provider is not None
        return self._ai_provider if isinstance(self._ai_provider, AIRouter) else None

    @property
    def is_gateway_mode(self) -> bool:
        """True when the AI provider is an `AIGateway`."""
        self._require_initialized("is_gateway_mode")
        assert self._ai_provider is not None
        return isinstance(self._ai_provider, AIGateway)

    @property
    def tool_registry(self) -> ToolRegistry:
        """The `ToolRegistry` singleton (Feature A.2)."""
        self._require_initialized("tool_registry")
        assert self._tool_registry is not None
        return self._tool_registry

    @property
    def embedder(self) -> Embedder:
        """The `Embedder` singleton (Step 6).

        Passed to `ContentService` and future `RAGService` / `QuizService`.
        The same instance is used for both indexing and querying — this is
        required for cosine similarity to be meaningful.
        """
        self._require_initialized("embedder")
        assert self._embedder is not None
        return self._embedder

    @property
    def content_processor_registry(self) -> ContentProcessorRegistry:
        """The `ContentProcessorRegistry` singleton (Step 5).

        Passed to `ContentService` at construction time.
        """
        self._require_initialized("content_processor_registry")
        assert self._content_processor_registry is not None
        return self._content_processor_registry

    @property
    def settings(self) -> Settings:
        """The application `Settings` singleton (always available, even pre-init)."""
        return self._settings
