"""Assembles a final prompt string from a versioned knowledge base.

`PromptBuilder` is completely generic: it has no idea what "mnemonic" or
"word" or "avoid" mean, and no idea a Gemini provider exists. Any future
feature that needs an AI prompt reuses this unchanged; only a thin,
feature-specific adapter (see `app/services/ai/mnemonic_prompt.py`) needs to
know the feature-specific details.
"""

from __future__ import annotations

import logging
from string import Template

from app.services.ai.knowledge_engine.loader import KnowledgeLoader
from app.services.ai.knowledge_engine.validator import KnowledgeValidator

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Loads, validates, and assembles a versioned knowledge set into one string."""

    def __init__(self, loader: KnowledgeLoader, validator: KnowledgeValidator) -> None:
        self._loader = loader
        self._validator = validator

    async def build(
        self,
        version: str,
        *,
        extra: list[str] | None = None,
        **context: str,
    ) -> str:
        """Load, validate, and assemble a prompt.

        Args:
            version: e.g. "v1" — a folder under `app/knowledge/`.
            extra: additional component filenames to load and append, in the
                given order, *after* the ones declared in manifest.yaml.
                This is how request-specific templates (e.g. a file that
                inserts the word being asked about) get spliced in without
                the engine needing to know they exist — see
                `mnemonic_prompt.py` for how this is used.
            **context: values substituted into every loaded component via
                `$name` placeholders (Python's `string.Template`). Deliberately
                NOT `str.format()`/`{name}`: `RESPONSE_SPECIFICATION.md`
                contains literal JSON full of `{` and `}`, which `.format()`
                would try to parse as placeholders and crash on. `$name`
                doesn't collide with that. Missing/unused placeholders are
                left as literal text rather than raising.

        Returns:
            The fully assembled prompt, ready to hand to any AIProvider.

        Raises:
            app.services.ai.knowledge_engine.exceptions.KnowledgeEngineError:
                (or a subclass) if any file is missing, empty, the
                configuration is invalid, or a version mismatch is found.
        """
        manifest = await self._loader.load_manifest(version)
        self._validator.validate_manifest(manifest, requested_version=version)

        component_names = list(manifest.prompt_components) + list(extra or [])

        components: dict[str, str] = {}
        for name in component_names:
            components[name] = await self._loader.load_component(version, name)

        self._validator.validate_components(components)

        rendered = [Template(components[name]).safe_substitute(**context) for name in component_names]
        final_prompt = "\n\n".join(part.strip() for part in rendered if part.strip())

        logger.debug(
            "Built prompt version=%s from %d component(s), %d chars total",
            version,
            len(component_names),
            len(final_prompt),
        )
        return final_prompt
