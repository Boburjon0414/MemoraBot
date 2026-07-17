"""Assembles a final prompt string from versioned Markdown components.

`PromptBuilder` is completely generic: it has no idea what "mnemonic" or
"word" or "avoid" mean, and no idea a Gemini provider exists. Any prompt set
— mnemonic today, chat/statistics/admin/translation/grammar tomorrow — is
assembled the exact same way. That genericity is what lets every future
AI provider and every future feature reuse this one class unchanged; only a
thin, feature-specific adapter (see `app/services/ai/mnemonic_prompt.py`)
needs to know the feature-specific details.
"""

from __future__ import annotations

import logging
from string import Template

from app.services.ai.prompt_engine.loader import PromptLoader
from app.services.ai.prompt_engine.validator import PromptValidator

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Loads, validates, and assembles a versioned prompt set into one string."""

    def __init__(self, loader: PromptLoader, validator: PromptValidator) -> None:
        self._loader = loader
        self._validator = validator

    async def build(
        self,
        prompt_set: str,
        version: str,
        *,
        extra: list[str] | None = None,
        **context: str,
    ) -> str:
        """Load, validate, and assemble a prompt.

        Args:
            prompt_set: e.g. "mnemonic" — a folder under `prompts/`.
            version: e.g. "v1" — a folder under `prompts/<prompt_set>/versions/`.
            extra: additional component filenames to load and append, in the
                given order, *after* the ones declared in metadata.yaml.
                This is how request-specific templates (e.g. a file that
                inserts the word being asked about) get spliced in without
                the engine needing to know they exist — see
                `mnemonic_prompt.py` for how this is used.
            **context: values substituted into every loaded component via
                `$name` placeholders (Python's `string.Template`). Deliberately
                NOT `str.format()`/`{name}`: prompt content routinely contains
                literal JSON examples full of `{` and `}` (see
                `output_format.md`), which `.format()` would try to parse as
                placeholders and crash on. `$name` doesn't collide with that.
                Missing/unused placeholders are left as literal text rather
                than raising, so most components need no context at all.

        Returns:
            The fully assembled prompt, ready to hand to any AIProvider.

        Raises:
            app.services.ai.prompt_engine.exceptions.PromptEngineError:
                (or a subclass) if any file is missing, empty, the
                configuration is invalid, or a version mismatch is found.
        """
        metadata = await self._loader.load_metadata(prompt_set, version)
        self._validator.validate_metadata(metadata, requested_version=version)

        component_names = list(metadata.components) + list(extra or [])

        components: dict[str, str] = {}
        for name in component_names:
            components[name] = await self._loader.load_component(prompt_set, version, name)

        self._validator.validate_components(components)

        rendered = [Template(components[name]).safe_substitute(**context) for name in component_names]
        final_prompt = "\n\n".join(part.strip() for part in rendered if part.strip())

        logger.debug(
            "Built prompt_set=%s version=%s from %d component(s), %d chars total",
            prompt_set,
            version,
            len(component_names),
            len(final_prompt),
        )
        return final_prompt
