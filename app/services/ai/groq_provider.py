"""`AIProvider` implementation backed by Groq's OpenAI-compatible API.

Groq's API is structurally identical to OpenAI's chat completions endpoint,
making it straightforward to integrate. Key differences from GeminiProvider:

  - Endpoint: https://api.groq.com/openai/v1/chat/completions
  - Auth:     Authorization: Bearer {api_key}  (not x-goog-api-key)
  - Schema:   response_format={"type": "json_object"} (OpenAI-style, no
              native responseSchema enforcement — we rely on the system
              prompt to guarantee field names and types)
  - Response: OpenAI chat-completion shape (choices[0].message.content)

This standalone provider targets single-key, single-model usage.
For multi-key pooling and automatic failover, the gateway layer
(app/services/ai/gateway/) uses GatewayKeySlot internally instead.
"""
from __future__ import annotations

import json
import logging

import aiohttp

from app.core.exceptions import AIProviderError
from app.services.ai.base import AIProvider
from app.services.ai.knowledge_engine.exceptions import KnowledgeEngineError
from app.services.ai.mnemonic_prompt import build_mnemonic_prompt
from app.services.ai.schemas import MnemonicResult

logger = logging.getLogger(__name__)

_GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
_REQUEST_TIMEOUT_SECONDS = 30
_TEMPERATURE = 1.1
_MAX_TOKENS = 1024

_SYSTEM_PROMPT = (
    "You are an expert Uzbek-English language educator specialised in mnemonic "
    "learning techniques. Generate mnemonic learning aids following the exact "
    "specifications the user provides.\n\n"
    "CRITICAL: Respond ONLY with a single valid JSON object. "
    "No markdown fences, no explanation, no preamble. "
    "Required keys: word, meaning, uzbek_pronunciation, mnemonic_story, "
    "example_sentence, difficulty (one of A1/A2/B1/B2/C1/C2)."
)


def _strip_fences(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.lower().startswith("json"):
            s = s[4:]
    return s.strip()


class GroqProvider(AIProvider):
    """Generates mnemonics via Groq's OpenAI-compatible chat completions API."""

    def __init__(
        self,
        api_key: str,
        model: str,
        prompt_version: str = "v1",
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._prompt_version = prompt_version

    @property
    def name(self) -> str:
        return f"groq:{self._model}"

    @property
    def prompt_version(self) -> str:
        return self._prompt_version

    async def generate_mnemonic(
        self, word: str, avoid: list[str] | None = None
    ) -> MnemonicResult:
        try:
            prompt_text = await build_mnemonic_prompt(
                word, avoid=avoid, version=self._prompt_version
            )
        except KnowledgeEngineError as exc:
            logger.exception("Failed to build mnemonic prompt for word=%s", word)
            raise AIProviderError("Failed to build the AI prompt") from exc

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt_text},
            ],
            "temperature": _TEMPERATURE,
            "response_format": {"type": "json_object"},
            "max_tokens": _MAX_TOKENS,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            timeout = aiohttp.ClientTimeout(total=_REQUEST_TIMEOUT_SECONDS)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    _GROQ_ENDPOINT, json=payload, headers=headers
                ) as response:
                    body = await response.text()
                    if response.status != 200:
                        logger.error(
                            "Groq API error %s for word=%s: %s",
                            response.status, word, body[:300],
                        )
                        raise AIProviderError(
                            f"Groq API returned status {response.status}"
                        )
        except (aiohttp.ClientError, TimeoutError) as exc:
            logger.exception("Network error while calling Groq API for word=%s", word)
            raise AIProviderError("Failed to reach Groq API") from exc

        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            logger.exception("Groq returned a non-JSON HTTP body for word=%s", word)
            raise AIProviderError("Groq API returned an invalid response") from exc

        return self._parse_response(data, word)

    def _parse_response(self, data: dict, word: str) -> MnemonicResult:
        try:
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(_strip_fences(content))
            return MnemonicResult.model_validate(parsed)
        except (KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
            logger.exception(
                "Failed to parse Groq response for word=%s: %s", word, data
            )
            raise AIProviderError("Could not parse Groq API response") from exc
