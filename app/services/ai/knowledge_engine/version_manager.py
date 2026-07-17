"""Resolves which knowledge-base version is active and enumerates the
versions available on disk.

This is the one place that knows knowledge-base versions are subdirectories
under `app/knowledge/` (currently just `v1/`). `PromptLoader` asks it for a
version's directory instead of constructing paths itself, so if the
on-disk convention ever changes, this is the only class that needs to know.
"""

from __future__ import annotations

from pathlib import Path

from app.services.ai.knowledge_engine.exceptions import KnowledgeVersionNotFoundError

MANIFEST_FILENAME = "manifest.yaml"


class KnowledgeVersionManager:
    """Resolves and lists knowledge-base versions under a base directory."""

    def __init__(self, knowledge_dir: Path) -> None:
        self._knowledge_dir = knowledge_dir

    def version_path(self, version: str) -> Path:
        """Return the directory for `version` (e.g. "v1"), without checking it exists."""
        return self._knowledge_dir / version

    def version_exists(self, version: str) -> bool:
        """True if `version`'s directory and manifest.yaml both exist."""
        path = self.version_path(version)
        return path.is_dir() and (path / MANIFEST_FILENAME).exists()

    def require_version_path(self, version: str) -> Path:
        """Like `version_path`, but raises if the version doesn't exist.

        Raises:
            KnowledgeVersionNotFoundError: if there's no directory (or no
                manifest.yaml inside it) for `version`.
        """
        path = self.version_path(version)
        if not self.version_exists(version):
            raise KnowledgeVersionNotFoundError(
                f"Knowledge base version {version!r} not found (expected {path}/{MANIFEST_FILENAME})"
            )
        return path

    def list_versions(self) -> list[str]:
        """List every version directory that has a manifest.yaml, sorted.

        Useful for a future Admin Panel's "Prompt Version Information" screen
        (see project documentation) without needing any new machinery.
        """
        if not self._knowledge_dir.is_dir():
            return []
        return sorted(
            entry.name
            for entry in self._knowledge_dir.iterdir()
            if entry.is_dir() and (entry / MANIFEST_FILENAME).exists()
        )
