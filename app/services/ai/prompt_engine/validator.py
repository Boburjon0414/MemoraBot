"""Validates a loaded prompt set before `PromptBuilder` assembles it.

Pure, synchronous, in-memory checks only — no I/O happens here (that's
`PromptLoader`'s job). Splitting it out like this means the rules for "is
this prompt set sane" can be tested and reasoned about with zero disk or
async concerns at all.
"""

from __future__ import annotations

import logging
import re

from app.services.ai.prompt_engine.exceptions import PromptValidationError
from app.services.ai.prompt_engine.loader import PromptMetadata

logger = logging.getLogger(__name__)

# Matches Markdown ATX headers, e.g. "# Identity" or "## Hard rules for the story".
_HEADER_PATTERN = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)


class PromptValidator:
    """Checks metadata sanity and component content before assembly.

    Covers everything the task asked for: missing/duplicate/empty entries in
    the component list (invalid configuration), a version mismatch between
    what was requested and what metadata.yaml itself declares (invalid
    version), empty component files, and duplicate Markdown sections across
    the whole set (a realistic copy-paste mistake when hand-editing prompt
    files).
    """

    def validate_metadata(self, metadata: PromptMetadata, requested_version: str) -> None:
        if not metadata.components:
            raise PromptValidationError("metadata.yaml declares zero components")

        if len(metadata.components) != len(set(metadata.components)):
            raise PromptValidationError(
                f"metadata.yaml lists a duplicate component filename: {metadata.components}"
            )

        if metadata.version != requested_version:
            raise PromptValidationError(
                f"Invalid version: metadata.yaml declares version={metadata.version!r} but "
                f"{requested_version!r} was requested. Did you copy a version folder without "
                "updating the 'version' field inside its metadata.yaml?"
            )

        logger.debug("metadata.yaml for version=%s is valid (%d components)", requested_version, len(metadata.components))

    def validate_components(self, components: dict[str, str]) -> None:
        for filename, text in components.items():
            if not text.strip():
                raise PromptValidationError(f"Prompt component {filename!r} is empty")

        seen_headers: dict[str, str] = {}
        for filename, text in components.items():
            for raw_header in _HEADER_PATTERN.findall(text):
                key = raw_header.strip().lower()
                if key in seen_headers and seen_headers[key] != filename:
                    raise PromptValidationError(
                        f"Duplicate section '{raw_header.strip()}' found in both "
                        f"{seen_headers[key]!r} and {filename!r} — likely a copy-paste mistake"
                    )
                seen_headers[key] = filename

        logger.debug("Validated %d prompt component(s), no issues found", len(components))
