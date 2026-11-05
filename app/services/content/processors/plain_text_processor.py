"""PlainTextProcessor: handles ContentSourceType.TEXT sources.

Plain text is the simplest case — the user pastes text directly, and the
'processor' simply returns it unchanged.  The value of going through the
processor abstraction even here is consistency: ContentService.process()
always goes through the registry and never special-cases TEXT, so adding
the first real processor (PDF, image) requires zero changes to ContentService.
"""

from __future__ import annotations

from app.database.models.content_source import ContentSource, ContentSourceType
from app.services.content.processor import (
    ContentProcessingError,
    ContentProcessor,
)


class PlainTextProcessor(ContentProcessor):
    """Processor for ContentSourceType.TEXT.

    For plain text sources the user-provided text is stored in
    `source.extracted_text` at creation time by ContentService.create_source().
    This processor simply validates that the text is present and returns it,
    acting as a no-op passthrough.
    """

    @property
    def supported_type(self) -> ContentSourceType:
        return ContentSourceType.TEXT

    async def extract_text(self, source: ContentSource) -> str:
        """Return the already-stored text, or raise if it's missing.

        Plain text sources should always have `extracted_text` populated at
        creation time.  A missing value indicates a bug in ContentService —
        raising here makes that visible immediately rather than silently
        indexing empty content.
        """
        if not source.extracted_text:
            raise ContentProcessingError(
                f"ContentSource id={source.id} has type=TEXT but no extracted_text. "
                "This indicates a bug in ContentService.create_source()."
            )
        return source.extracted_text

    async def extract_metadata(self, source: ContentSource) -> dict[str, str]:
        """Return minimal metadata for a plain text source.

        Plain text has no inherent title or language metadata.  If the user
        provided a title via ContentService.create_source(title=…), it was
        already stored in source.title — we don't need to repeat it here.
        """
        return {}
