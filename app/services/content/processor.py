"""The `ContentProcessor` abstraction: one processor per `ContentSourceType`.

Each concrete processor knows how to extract plain text and metadata from
one specific input format.  The `ContentProcessorRegistry` maps source types
to processors and is the only place that decides which processor handles
which type — `ContentService.process()` calls `registry.get(source.source_type)`
and never contains an if/elif chain.

Adding a new format
-------------------
1. Create a new processor class (e.g. `PDFProcessor`) in
   `app/services/content/processors/pdf_processor.py`.
2. Register it in `PlatformContainer.initialize()`:
       self._content_processor_registry.register(PDFProcessor())
That's it — zero changes to ContentService, ContentSource, or any handler.

Current concrete processors (Step 5)
--------------------------------------
  PlainTextProcessor — handles ContentSourceType.TEXT; returns text unchanged.

Future processors
-----------------
  PDFProcessor         — pdfminer.six / pypdf             (Step 7/G)
  ImageOCRProcessor    — pytesseract or AIRouter vision    (Step 7/G)
  URLScraperProcessor  — httpx + html-to-text              (Feature F)
  AudioProcessor       — Groq Whisper transcription        (Feature H)
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from app.database.models.content_source import ContentSource, ContentSourceType

logger = logging.getLogger(__name__)


class ContentProcessor(ABC):
    """Abstract base class every content processor must implement.

    A processor is stateless and can be safely shared as a singleton
    across all requests — it holds no per-request state.
    """

    @property
    @abstractmethod
    def supported_type(self) -> ContentSourceType:
        """The one `ContentSourceType` this processor handles."""
        raise NotImplementedError

    @abstractmethod
    async def extract_text(self, source: ContentSource) -> str:
        """Extract and return plain text from `source`.

        The caller (`ContentService.process()`) stores the result in
        `source.extracted_text`.  Processors should not write to the
        model themselves — they are pure extraction functions.

        Args:
            source: The `ContentSource` row.  For file-based sources,
                    `source.raw_storage_key` contains the path to the file.
                    For text sources, `source.extracted_text` already has
                    the content (PlainTextProcessor returns it unchanged).

        Returns:
            The full extracted text as a single UTF-8 string.

        Raises:
            ContentProcessingError: if extraction fails for any reason.
                ContentService catches this and sets status="failed".
        """
        raise NotImplementedError

    @abstractmethod
    async def extract_metadata(self, source: ContentSource) -> dict[str, str]:
        """Extract display metadata from `source`.

        Returns a flat dict of string → string.  Known keys:
            "title"        — document title or page title
            "page_count"   — for PDFs
            "language"     — detected language code (e.g. "en", "uz")
            "author"       — document author (if available)
            "url"          — canonical URL (for URL sources)

        Processors that cannot extract a particular field simply omit it.
        Returning an empty dict is always valid.

        Does NOT raise — metadata extraction failure is non-fatal.
        """
        raise NotImplementedError


class ContentProcessingError(Exception):
    """Raised by a `ContentProcessor` when text extraction fails.

    Caught by `ContentService.process()` which sets the source status
    to "failed" and stores the error message.  Never propagates to handlers.
    """


class ContentProcessorRegistry:
    """Maps `ContentSourceType` values to `ContentProcessor` instances.

    A single registry instance lives in `PlatformContainer`.
    `ContentService` receives it at construction time.

    Thread-safety: `register()` is called only during
    `PlatformContainer.initialize()` (single-threaded startup),
    so no locking is needed.
    """

    def __init__(self) -> None:
        self._processors: dict[str, ContentProcessor] = {}

    def register(self, processor: ContentProcessor) -> None:
        """Register `processor` for its `supported_type`.

        Overwrites any previously registered processor for the same type
        (allows test overrides with mock processors).
        """
        key = processor.supported_type.value
        self._processors[key] = processor
        logger.debug(
            "ContentProcessorRegistry: registered %s for type=%r",
            type(processor).__name__,
            key,
        )

    def get(self, source_type: str) -> ContentProcessor | None:
        """Return the processor for `source_type`, or None if not registered.

        `ContentService.process()` checks for None and sets status="failed"
        with a descriptive error message when no processor is available.
        """
        return self._processors.get(source_type)

    @property
    def supported_types(self) -> list[str]:
        """List of all currently registered source type strings."""
        return list(self._processors.keys())
