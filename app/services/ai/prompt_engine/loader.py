"""Reads prompt metadata and component files from disk.

`PromptLoader` knows exactly one thing: the on-disk convention
`<base_dir>/<prompt_set>/versions/<version>/<file>`. It has no idea what a
"mnemonic" is, doesn't validate content, and doesn't assemble anything —
that's `PromptValidator` and `PromptBuilder`'s job respectively. This keeps
each class honest to a single responsibility.

File reads are wrapped in `asyncio.to_thread` so this stays consistent with
the rest of MemoraBot's "everything is async" rule, even though local
Markdown files are small enough that the blocking cost is negligible on its
own — see `builder.py` for why this matters once `PromptBuilder.build()` is
awaited from `GeminiProvider`.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from app.services.ai.prompt_engine.exceptions import (
    PromptFileNotFoundError,
    PromptMetadataError,
)


@dataclass(frozen=True)
class PromptMetadata:
    """Parsed contents of one prompt set version's `metadata.yaml`."""

    version: str
    description: str
    components: list[str] = field(default_factory=list)


class PromptLoader:
    """Reads a prompt set version's metadata and component files from disk."""

    METADATA_FILENAME = "metadata.yaml"

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    def _version_dir(self, prompt_set: str, version: str) -> Path:
        return self._base_dir / prompt_set / "versions" / version

    async def load_metadata(self, prompt_set: str, version: str) -> PromptMetadata:
        """Load and parse `metadata.yaml` for `prompt_set`/`version`.

        Raises:
            PromptFileNotFoundError: if metadata.yaml doesn't exist.
            PromptMetadataError: if it isn't valid YAML, isn't a mapping, or
                is missing the required `version`/`components` keys.
        """
        path = self._version_dir(prompt_set, version) / self.METADATA_FILENAME
        if not path.exists():
            raise PromptFileNotFoundError(
                f"metadata.yaml not found for prompt_set={prompt_set!r} version={version!r} "
                f"(expected at {path})"
            )

        raw_text = await asyncio.to_thread(path.read_text, encoding="utf-8")
        try:
            raw = yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            raise PromptMetadataError(f"Malformed YAML in {path}: {exc}") from exc

        if not isinstance(raw, dict):
            raise PromptMetadataError(
                f"{path} must contain a YAML mapping at the top level, got {type(raw).__name__}"
            )

        try:
            components = raw["components"]
            metadata_version = raw["version"]
        except KeyError as exc:
            raise PromptMetadataError(f"{path} is missing required key: {exc}") from exc

        if not isinstance(components, list) or not all(isinstance(c, str) for c in components):
            raise PromptMetadataError(f"{path}: 'components' must be a list of filenames")

        return PromptMetadata(
            version=str(metadata_version),
            description=str(raw.get("description", "")),
            components=list(components),
        )

    async def load_component(self, prompt_set: str, version: str, filename: str) -> str:
        """Read one component file's raw text.

        Raises:
            PromptFileNotFoundError: if `filename` doesn't exist for this
                prompt_set/version.
        """
        path = self._version_dir(prompt_set, version) / filename
        if not path.exists():
            raise PromptFileNotFoundError(
                f"Prompt component {filename!r} not found for prompt_set={prompt_set!r} "
                f"version={version!r} (expected at {path})"
            )
        return await asyncio.to_thread(path.read_text, encoding="utf-8")
