"""`AIProvider` implementation backed by Google's Gemini API.

Talks to Gemini directly over HTTP with aiohttp (already a dependency of
aiogram) instead of a synchronous SDK, so the whole call chain stays
natively async and the dependency footprint stays small. Endpoint, header,
and payload shape follow the public Gemini API reference
(https://ai.google.dev/api).

V1.1 changes (mnemonic-quality pass):
- `avoid` is threaded through to the prompt builder for the regenerate flow.
- `temperature` raised from 0.9 -> 1.15 for funnier, more memorable stories.
- Added `responseSchema` alongside `responseMimeType`, enforcing the
  structural contract at the API level, not just via prompt text.

V1.2 changes (knowledge-driven architecture): the prompt itself now comes
from `mnemonic_prompt.build_mnemonic_prompt`, which assembles it from
versioned Markdown documents in `app/knowledge/` instead of a hardcoded
Python string. This class still has zero knowledge of where those files
live or how many there are — it just awaits a function that returns a
string. `prompt_version` is injected the same way `model` already was.
The `difficulty` schema enum is now the CEFR scale (A1-C2), per
`app/knowledge/v1/RESPONSE_SPECIFICATION.md`.
"""

from __future__ import annotations

import json
import logging

import aiohttp

from app.core.exceptions import AIProviderError
from app.services.ai.base import MnemonicProvider
from app.services.ai.knowledge_engine.exceptions import KnowledgeEngineError
from app.services.ai.mnemonic_prompt import build_mnemonic_prompt
from app.services.ai.schemas import MnemonicResult

logger = logging.getLogger(__name__)

_GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_REQUEST_TIMEOUT_SECONDS = 30
_TEMPERATURE = 1.15

_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "word": {"type": "string"},
        "meaning": {"type": "string"},
        "uzbek_pronunciation": {"type": "string"},
        "mnemonic_story": {"type": "string"},
        "example_sentence": {"type": "string"},
        "difficulty": {"type": "string", "enum": ["A1", "A2", "B1", "B2", "C1", "C2"]},
    },
    "required": [
        "word",
        "meaning",
        "uzbek_pronunciation",
        "mnemonic_story",
        "example_sentence",
        "difficulty",
    ],
    "propertyOrdering": [
        "word",
        "meaning",
        "uzbek_pronunciation",
        "mnemonic_story",
        "example_sentence",
        "difficulty",
    ],
}


def _strip_markdown_fences(text: str) -> str:
    """Defensively strip ```json ... ``` fences, in case the model adds them
    despite being asked for raw JSON via `responseMimeType`/`responseSchema`.
    """
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:]
    return stripped.strip()


class GeminiProvider(MnemonicProvider):
    """Generates mnemonics using a Gemini model via the `generateContent` REST endpoint."""

    def __init__(self, api_key: str, model: str, prompt_version: str = "v1") -> None:
        self._api_key = api_key
        self._model = model
        self._prompt_version = prompt_version

    @property
    def name(self) -> str:
        return f"gemini:{self._model}"

    @property
    def prompt_version(self) -> str:
        return self._prompt_version

    async def generate_mnemonic(self, word: str, avoid: list[str] | None = None) -> MnemonicResult:
        try:
            prompt_text = await build_mnemonic_prompt(word, avoid=avoid, version=self._prompt_version)
        except KnowledgeEngineError as exc:
            logger.exception("Failed to build the mnemonic prompt for word=%s", word)
            raise AIProviderError("Failed to build the AI prompt") from exc

        url = _GEMINI_ENDPOINT.format(model=self._model)
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt_text}]}],
            "generationConfig": {
                "temperature": _TEMPERATURE,
                "responseMimeType": "application/json",
                "responseSchema": _RESPONSE_SCHEMA,
            },
        }
        headers = {"x-goog-api-key": self._api_key, "Content-Type": "application/json"}

        try:
            timeout = aiohttp.ClientTimeout(total=_REQUEST_TIMEOUT_SECONDS)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    body = await response.text()
                    if response.status != 200:
                        logger.error("Gemini API error %s for word=%s: %s", response.status, word, body)
                        raise AIProviderError(f"Gemini API returned status {response.status}")
        except (aiohttp.ClientError, TimeoutError) as exc:
            logger.exception("Network error while calling Gemini API for word=%s", word)
            raise AIProviderError("Failed to reach Gemini API") from exc

        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            logger.exception("Gemini API returned a non-JSON HTTP body for word=%s", word)
            raise AIProviderError("Gemini API returned an invalid response") from exc

        return self._parse_response(data, word)

    def _parse_response(self, data: dict, word: str) -> MnemonicResult:
        """Extract and validate the structured mnemonic from a Gemini response body."""
        try:
            candidates = data["candidates"]
            raw_text = candidates[0]["content"]["parts"][0]["text"]
            parsed = json.loads(_strip_markdown_fences(raw_text))
            return MnemonicResult.model_validate(parsed)
        except (KeyError, IndexError, ValueError) as exc:
            logger.exception("Failed to parse Gemini response for word=%s: %s", word, data)
            raise AIProviderError("Could not parse Gemini API response") from exc
