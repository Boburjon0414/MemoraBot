"""Reads a knowledge-base version's manifest and component files from disk.

`KnowledgeLoader` delegates version->directory resolution to
`KnowledgeVersionManager` and knows nothing else about the project — it
doesn't validate content (`KnowledgeValidator`'s job) or assemble anything
(`PromptBuilder`'s job). Single responsibility, matching the rest of the
codebase's layering.

File reads are wrapped in `asyncio.to_thread` to stay consistent with
MemoraBot's "everything is async" rule, even though local Markdown files
are small enough that the blocking cost is negligible on its own.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import yaml

from app.services.ai.knowledge_engine.exceptions import (
    KnowledgeFileNotFoundError,
    KnowledgeManifestError,
)
from app.services.ai.knowledge_engine.version_manager import (
    MANIFEST_FILENAME,
    KnowledgeVersionManager,
)


@dataclass(frozen=True)
class KnowledgeManifest:
    """Parsed contents of one version's `manifest.yaml`."""

    version: str
    description: str
    prompt_components: list[str] = field(default_factory=list)
    reference_only: list[str] = field(default_factory=list)


class KnowledgeLoader:
    """Reads a knowledge-base version's manifest and component files from disk."""

    def __init__(self, version_manager: KnowledgeVersionManager) -> None:
        self._version_manager = version_manager

    async def load_manifest(self, version: str) -> KnowledgeManifest:
        """Load and parse `manifest.yaml` for `version`.

        Raises:
            KnowledgeVersionNotFoundError: if the version directory or its
                manifest.yaml doesn't exist (raised by the version manager).
            KnowledgeManifestError: if it isn't valid YAML, isn't a mapping,
                or is missing the required `version`/`prompt_components` keys.
        """
        path = self._version_manager.require_version_path(version) / MANIFEST_FILENAME

        raw_text = await asyncio.to_thread(path.read_text, encoding="utf-8")
        try:
            raw = yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            raise KnowledgeManifestError(f"Malformed YAML in {path}: {exc}") from exc

        if not isinstance(raw, dict):
            raise KnowledgeManifestError(
                f"{path} must contain a YAML mapping at the top level, got {type(raw).__name__}"
            )

        try:
            prompt_components = raw["prompt_components"]
            manifest_version = raw["version"]
        except KeyError as exc:
            raise KnowledgeManifestError(f"{path} is missing required key: {exc}") from exc

        if not isinstance(prompt_components, list) or not all(
            isinstance(c, str) for c in prompt_components
        ):
            raise KnowledgeManifestError(f"{path}: 'prompt_components' must be a list of filenames")

        reference_only = raw.get("reference_only", [])
        if not isinstance(reference_only, list):
            reference_only = []

        return KnowledgeManifest(
            version=str(manifest_version),
            description=str(raw.get("description", "")),
            prompt_components=list(prompt_components),
            reference_only=[str(r) for r in reference_only],
        )

    async def load_component(self, version: str, filename: str) -> str:
        """Read one component file's raw text.

        Raises:
            KnowledgeFileNotFoundError: if `filename` doesn't exist for this version.
        """
        path = self._version_manager.require_version_path(version) / filename
        if not path.exists():
            raise KnowledgeFileNotFoundError(
                f"Knowledge component {filename!r} not found for version={version!r} "
                f"(expected at {path})"
            )
        return await asyncio.to_thread(path.read_text, encoding="utf-8")
