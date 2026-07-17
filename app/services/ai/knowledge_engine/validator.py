"""Validates a loaded knowledge set before `PromptBuilder` assembles it.

Pure, synchronous, in-memory checks only — no I/O happens here (that's
`KnowledgeLoader`'s job).
"""

from __future__ import annotations

import logging
import re

from app.services.ai.knowledge_engine.exceptions import KnowledgeValidationError
from app.services.ai.knowledge_engine.loader import KnowledgeManifest

logger = logging.getLogger(__name__)

# Matches Markdown ATX headers, e.g. "# Identity" or "## Hard rules for the story".
_HEADER_PATTERN = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)


class KnowledgeValidator:
    """Checks manifest sanity and component content before assembly.

    Only files actually loaded into a prompt (manifest's
    `prompt_components`, plus any per-request `extra` files) are checked
    here — `reference_only` files are tracked in the manifest for
    documentation purposes but are never loaded or validated, so they're
    free to stay a work in progress (see EVALUATION_GUIDE.md / TEST_CASES.md).
    """

    def validate_manifest(self, manifest: KnowledgeManifest, requested_version: str) -> None:
        if not manifest.prompt_components:
            raise KnowledgeValidationError("manifest.yaml declares zero prompt_components")

        if len(manifest.prompt_components) != len(set(manifest.prompt_components)):
            raise KnowledgeValidationError(
                f"manifest.yaml lists a duplicate component filename: {manifest.prompt_components}"
            )

        if manifest.version != requested_version:
            raise KnowledgeValidationError(
                f"Invalid version: manifest.yaml declares version={manifest.version!r} but "
                f"{requested_version!r} was requested. Did you copy a version folder without "
                "updating the 'version' field inside its manifest.yaml?"
            )

        logger.debug(
            "manifest.yaml for version=%s is valid (%d prompt components)",
            requested_version,
            len(manifest.prompt_components),
        )

    def validate_components(self, components: dict[str, str]) -> None:
        for filename, text in components.items():
            if not text.strip():
                raise KnowledgeValidationError(f"Knowledge component {filename!r} is empty")

        # Duplicate-header detection is scoped to WITHIN a single file only.
        # Checking *across* files would false-positive on knowledge bases
        # that intentionally use a consistent structure (e.g. every document
        # here starts with "## Purpose") — that's good documentation
        # hygiene, not a mistake. Catching an accidental double-paste of the
        # same section within one file is still worth doing.
        for filename, text in components.items():
            seen_in_file: set[str] = set()
            for raw_header in _HEADER_PATTERN.findall(text):
                key = raw_header.strip().lower()
                if key in seen_in_file:
                    raise KnowledgeValidationError(
                        f"Duplicate section '{raw_header.strip()}' found twice within "
                        f"{filename!r} — likely a copy-paste mistake"
                    )
                seen_in_file.add(key)

        logger.debug("Validated %d knowledge component(s), no issues found", len(components))
