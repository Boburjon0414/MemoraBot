"""GatewayKeySlot — the atomic routing unit inside the AI Gateway.

One slot = one API key + an ordered list of models to try + one reused
aiohttp.ClientSession + one KeyHealth tracker.

The slot is responsible for:
  1. Building the mnemonic prompt (shared across providers via mnemonic_prompt).
  2. Trying each model in order until one succeeds.
  3. Raising the correct gateway-internal exception so the gateway knows
     how to route (rotate key, rotate provider, disable key, etc.).
  4. Reusing a single long-lived aiohttp.ClientSession to avoid the TCP
     handshake overhead of recreating a session on every request.

Nothing in this module is imported outside the gateway/ package.
API keys are NEVER logged — only the 1-based index label is used.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time

import aiohttp

from app.services.ai.gateway.errors import (
    KeyInvalidError,
    ModelUnavailableError,
    ProviderUnavailableError,
    QuotaExceededError,
    TransientError,
)
from app.services.ai.gateway.key_health import KeyHealth
from app.services.ai.knowledge_engine.exceptions import KnowledgeEngineError
from app.services.ai.mnemonic_prompt import build_mnemonic_prompt
from app.services.ai.router import AIRequest, AIResponse
from app.services.ai.schemas import MnemonicResult

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT_SECONDS = 30

# ── Gemini constants ───────────────────────────────────────────────────────── #

_GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com"
    "/v1beta/models/{model}:generateContent"
)
_GEMINI_TEMPERATURE = 1.15
_GEMINI_RESPONSE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "word": {"type": "string"},
        "meaning": {"type": "string"},
        "uzbek_pronunciation": {"type": "string"},
        "mnemonic_story": {"type": "string"},
        "example_sentence": {"type": "string"},
        "difficulty": {
            "type": "string",
            "enum": ["A1", "A2", "B1", "B2", "C1", "C2"],
        },
    },
    "required": [
        "word", "meaning", "uzbek_pronunciation",
        "mnemonic_story", "example_sentence", "difficulty",
    ],
    "propertyOrdering": [
        "word", "meaning", "uzbek_pronunciation",
        "mnemonic_story", "example_sentence", "difficulty",
    ],
}

# ── Groq constants ─────────────────────────────────────────────────────────── #

_GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_TEMPERATURE = 1.1
_GROQ_MAX_TOKENS = 1024
_GROQ_SYSTEM_MSG = (
    "You are an expert Uzbek-English language educator specialised in mnemonic "
    "learning techniques. Generate mnemonic learning aids following the exact "
    "specifications the user provides.\n\n"
    "CRITICAL: Respond ONLY with a single valid JSON object. "
    "No markdown fences, no explanation, no preamble. "
    "Required keys: word, meaning, uzbek_pronunciation, mnemonic_story, "
    "example_sentence, difficulty (one of A1/A2/B1/B2/C1/C2)."
)


# ── Helpers ────────────────────────────────────────────────────────────────── #

def _strip_fences(text: str) -> str:
    """Defensively strip ```json … ``` fences that some models add."""
    s = text.strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.lower().startswith("json"):
            s = s[4:]
    return s.strip()


# ── Main class ─────────────────────────────────────────────────────────────── #

class GatewayKeySlot:
    """One API key with an ordered model list, health tracking, and HTTP reuse.

    Public interface:
        await slot.generate(word, avoid)  → MnemonicResult
        await slot.close()                → graceful shutdown
        slot.health                       → KeyHealth (read-only from outside)
        slot.label                        → "Gemini Key #2 (premium)"
    """

    def __init__(
        self,
        *,
        provider_name: str,
        key_index: int,
        tier: str,
        api_key: str,
        models: list[str],
        prompt_version: str,
        request_timeout: float = _REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self.provider_name = provider_name
        self.key_index = key_index
        self.tier = tier
        self._api_key = api_key       # NEVER log this value
        self._models = models
        self._prompt_version = prompt_version
        self._timeout = aiohttp.ClientTimeout(total=request_timeout)

        self.health = KeyHealth(
            key_index=key_index,
            provider_name=provider_name,
            tier=tier,
        )

        # Long-lived session — created lazily on first use, reused thereafter.
        self._session: aiohttp.ClientSession | None = None
        self._session_lock = asyncio.Lock()

    @property
    def label(self) -> str:
        """Safe human-readable identifier — never contains the API key."""
        return self.health.label

    # ── HTTP session lifecycle ─────────────────────────────────────────── #

    async def _session_get(self) -> aiohttp.ClientSession:
        """Return the shared session, creating it on first call."""
        async with self._session_lock:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self._session

    async def close(self) -> None:
        """Gracefully close the HTTP session. Called at bot shutdown."""
        async with self._session_lock:
            if self._session and not self._session.closed:
                await self._session.close()
                self._session = None

    # ── Public generation entry point ──────────────────────────────────── #

    async def generate(
        self,
        word: str,
        avoid: list[str] | None = None,
    ) -> MnemonicResult:
        """Try each model in order. Return on first success.

        Raises (gateway-internal — never reach MnemonicService):
            QuotaExceededError      — 429; rotate to the next API key.
            KeyInvalidError         — 401/403; disable this key.
            ProviderUnavailableError— network/503; mark provider degraded.
            ModelUnavailableError   — all models exhausted on this key.
            KnowledgeEngineError    — prompt build failed; not a provider issue.
        """
        try:
            prompt_text = await build_mnemonic_prompt(
                word, avoid=avoid, version=self._prompt_version
            )
        except KnowledgeEngineError:
            raise  # config problem — bubble up unchanged

        last_exc: Exception | None = None

        for model in self._models:
            try:
                t0 = time.monotonic()
                result = await self._call(prompt_text, model, word)
                latency_ms = (time.monotonic() - t0) * 1000
                await self.health.record_success(latency_ms)
                logger.info(
                    "✅ %s model=%s word=%r %.0fms",
                    self.label, model, word, latency_ms,
                )
                return result

            except (QuotaExceededError, KeyInvalidError):
                # Key-level failure — stop trying other models on this key
                await self.health.record_failure()
                raise

            except ProviderUnavailableError as exc:
                await self.health.record_failure(cooldown_seconds=30)
                logger.warning("⚠️  %s model=%s provider unreachable", self.label, model)
                raise  # escalate immediately — other keys on this provider may also be down

            except TransientError as exc:
                last_exc = exc
                await self.health.record_failure(cooldown_seconds=5)
                logger.warning(
                    "⚠️  %s model=%s transient HTTP %s — trying next model",
                    self.label, model, exc.status,
                )
                continue  # next model

            except ModelUnavailableError as exc:
                last_exc = exc
                logger.warning(
                    "⚠️  %s model=%s unavailable — trying next model",
                    self.label, model,
                )
                continue  # next model

        raise ModelUnavailableError(
            f"All models exhausted on {self.label}"
        ) from last_exc

    async def complete_request(self, request: AIRequest) -> AIResponse:
        """Send a generic `AIRequest` through this key slot, trying each model.

        This is the generic sibling of `generate()`.  It uses the same HTTP
        session, the same error classification, and the same model cascade
        logic — but accepts any system_prompt / user_message instead of the
        mnemonic-specific prompt.

        Raises the same gateway-internal exceptions as `generate()` so the
        gateway's `_exhaust_pool_generic()` method can route around failures
        exactly as it does for mnemonic generation.
        """
        last_exc: Exception | None = None

        for model in self._models:
            try:
                t0 = time.monotonic()
                raw_text = await self._call_generic(request, model)
                latency_ms = (time.monotonic() - t0) * 1000
                await self.health.record_success(latency_ms)
                logger.info(
                    "✅ %s model=%s type=%r %.0fms",
                    self.label, model, request.request_type, latency_ms,
                )
                return AIResponse(
                    raw_text=raw_text,
                    provider_name=self.provider_name,
                    model_name=model,
                    latency_ms=latency_ms,
                )

            except (QuotaExceededError, KeyInvalidError):
                await self.health.record_failure()
                raise

            except ProviderUnavailableError:
                await self.health.record_failure(cooldown_seconds=30)
                logger.warning(
                    "⚠️  %s model=%s provider unreachable (generic request)",
                    self.label, model,
                )
                raise

            except TransientError as exc:
                last_exc = exc
                await self.health.record_failure(cooldown_seconds=5)
                logger.warning(
                    "⚠️  %s model=%s transient HTTP %s — trying next model",
                    self.label, model, exc.status,
                )
                continue

            except ModelUnavailableError as exc:
                last_exc = exc
                logger.warning(
                    "⚠️  %s model=%s unavailable — trying next model",
                    self.label, model,
                )
                continue

        raise ModelUnavailableError(
            f"All models exhausted on {self.label} (generic request)"
        ) from last_exc

    # ── Provider dispatch ──────────────────────────────────────────────── #

    async def _call(
        self, prompt_text: str, model: str, word: str
    ) -> MnemonicResult:
        if self.provider_name == "gemini":
            return await self._call_gemini(prompt_text, model, word)
        if self.provider_name == "groq":
            return await self._call_groq(prompt_text, model, word)
        raise NotImplementedError(
            f"Unknown provider in GatewayKeySlot: {self.provider_name!r}"
        )

    async def _call_generic(self, request: AIRequest, model: str) -> str:
        """Send an `AIRequest` to the provider and return the raw text reply.

        Dispatches to the provider-specific implementation.  Returns the
        raw response string; the caller (complete_request) wraps it in
        `AIResponse`.  Raises the same gateway-internal exceptions as `_call`.
        """
        if self.provider_name == "gemini":
            return await self._call_gemini_generic(request, model)
        if self.provider_name == "groq":
            return await self._call_groq_generic(request, model)
        raise NotImplementedError(
            f"Unknown provider in GatewayKeySlot._call_generic: {self.provider_name!r}"
        )

    # ── Gemini ─────────────────────────────────────────────────────────── #

    async def _call_gemini(
        self, prompt_text: str, model: str, word: str
    ) -> MnemonicResult:
        url = _GEMINI_ENDPOINT.format(model=model)
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt_text}]}],
            "generationConfig": {
                "temperature": _GEMINI_TEMPERATURE,
                "responseMimeType": "application/json",
                "responseSchema": _GEMINI_RESPONSE_SCHEMA,
            },
        }
        headers = {
            "x-goog-api-key": self._api_key,
            "Content-Type": "application/json",
        }

        session = await self._session_get()
        try:
            async with session.post(url, json=payload, headers=headers) as resp:
                body = await resp.text()
                _raise_for_gemini_status(resp.status, body)
        except (aiohttp.ClientConnectorError, aiohttp.ServerConnectionError) as exc:
            raise ProviderUnavailableError(f"Gemini DNS/network error: {exc}") from exc
        except asyncio.TimeoutError as exc:
            raise ProviderUnavailableError("Gemini request timed out") from exc
        except GatewayRoutingError:  # type: ignore[misc]  # re-raise internal
            raise
        except aiohttp.ClientError as exc:
            raise ProviderUnavailableError(f"Gemini client error: {exc}") from exc

        return _parse_gemini_body(body, word)

    async def _call_gemini_generic(self, request: AIRequest, model: str) -> str:
        """Send a generic AIRequest to Gemini and return the raw text reply.

        Uses a `system_instruction` field (Gemini's preferred way to supply
        a system prompt) alongside a single user turn.  When `response_schema`
        is set, it is passed through to `generationConfig.responseSchema` for
        structured JSON output; otherwise `responseMimeType` is omitted so
        the model can return free-form text.
        """
        url = _GEMINI_ENDPOINT.format(model=model)

        generation_config: dict = {
            "temperature": request.temperature,
            "maxOutputTokens": request.max_tokens,
        }
        if request.response_schema is not None:
            generation_config["responseMimeType"] = "application/json"
            generation_config["responseSchema"] = request.response_schema

        payload: dict = {
            "system_instruction": {
                "parts": [{"text": request.system_prompt}]
            },
            "contents": [
                {"role": "user", "parts": [{"text": request.user_message}]}
            ],
            "generationConfig": generation_config,
        }
        headers = {
            "x-goog-api-key": self._api_key,
            "Content-Type": "application/json",
        }

        session = await self._session_get()
        try:
            async with session.post(url, json=payload, headers=headers) as resp:
                body = await resp.text()
                _raise_for_gemini_status(resp.status, body)
        except (aiohttp.ClientConnectorError, aiohttp.ServerConnectionError) as exc:
            raise ProviderUnavailableError(f"Gemini DNS/network error: {exc}") from exc
        except asyncio.TimeoutError as exc:
            raise ProviderUnavailableError("Gemini request timed out") from exc
        except GatewayRoutingError:  # type: ignore[misc]
            raise
        except aiohttp.ClientError as exc:
            raise ProviderUnavailableError(f"Gemini client error: {exc}") from exc

        # Extract the raw text from the Gemini response envelope
        try:
            import json as _json
            data = _json.loads(body)
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, _json.JSONDecodeError) as exc:
            raise ModelUnavailableError(
                f"Gemini returned unparseable generic response"
            ) from exc

    # ── Groq ───────────────────────────────────────────────────────────── #

    async def _call_groq(
        self, prompt_text: str, model: str, word: str
    ) -> MnemonicResult:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": _GROQ_SYSTEM_MSG},
                {"role": "user", "content": prompt_text},
            ],
            "temperature": _GROQ_TEMPERATURE,
            "response_format": {"type": "json_object"},
            "max_tokens": _GROQ_MAX_TOKENS,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        session = await self._session_get()
        try:
            async with session.post(
                _GROQ_ENDPOINT, json=payload, headers=headers
            ) as resp:
                body = await resp.text()
                _raise_for_groq_status(resp.status, body)
        except (aiohttp.ClientConnectorError, aiohttp.ServerConnectionError) as exc:
            raise ProviderUnavailableError(f"Groq DNS/network error: {exc}") from exc
        except asyncio.TimeoutError as exc:
            raise ProviderUnavailableError("Groq request timed out") from exc
        except GatewayRoutingError:  # type: ignore[misc]
            raise
        except aiohttp.ClientError as exc:
            raise ProviderUnavailableError(f"Groq client error: {exc}") from exc

        return _parse_groq_body(body, word)

    async def _call_groq_generic(self, request: AIRequest, model: str) -> str:
        """Send a generic AIRequest to Groq and return the raw text reply.

        Groq uses the OpenAI-compatible messages format with a system role.
        When `response_schema` is set, `response_format: json_object` is
        enabled — Groq does not support the full JSON Schema constraint, but
        the schema is embedded as a description in the system prompt by
        convention (callers should include schema hints in `system_prompt`).
        """
        import json as _json

        messages = [
            {"role": "system", "content": request.system_prompt},
            {"role": "user", "content": request.user_message},
        ]

        payload: dict = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if request.response_schema is not None:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        session = await self._session_get()
        try:
            async with session.post(
                _GROQ_ENDPOINT, json=payload, headers=headers
            ) as resp:
                body = await resp.text()
                _raise_for_groq_status(resp.status, body)
        except (aiohttp.ClientConnectorError, aiohttp.ServerConnectionError) as exc:
            raise ProviderUnavailableError(f"Groq DNS/network error: {exc}") from exc
        except asyncio.TimeoutError as exc:
            raise ProviderUnavailableError("Groq request timed out") from exc
        except GatewayRoutingError:  # type: ignore[misc]
            raise
        except aiohttp.ClientError as exc:
            raise ProviderUnavailableError(f"Groq client error: {exc}") from exc

        try:
            data = _json.loads(body)
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, _json.JSONDecodeError) as exc:
            raise ModelUnavailableError(
                "Groq returned unparseable generic response"
            ) from exc


# ── Status-code → exception mapping (module-level to keep classes thin) ───── #

def _raise_for_gemini_status(status: int, body: str) -> None:
    if status == 200:
        return
    if status == 429:
        raise QuotaExceededError()
    if status in (401, 403):
        raise KeyInvalidError(f"Gemini rejected key (HTTP {status})")
    if status == 404:
        raise ModelUnavailableError(f"Gemini model not found (HTTP 404)")
    if status in (500, 503, 529):
        raise TransientError(status)
    raise ProviderUnavailableError(f"Gemini unexpected HTTP {status}: {body[:300]}")


def _raise_for_groq_status(status: int, body: str) -> None:
    if status == 200:
        return
    if status == 429:
        raise QuotaExceededError()
    if status in (401, 403):
        raise KeyInvalidError(f"Groq rejected key (HTTP {status})")
    if status == 404:
        raise ModelUnavailableError(f"Groq model not found (HTTP 404)")
    if status in (500, 503):
        raise TransientError(status)
    raise ProviderUnavailableError(f"Groq unexpected HTTP {status}: {body[:300]}")


# ── Response parsers ───────────────────────────────────────────────────────── #

def _parse_gemini_body(body: str, word: str) -> MnemonicResult:
    try:
        data = json.loads(body)
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(_strip_fences(raw))
        return MnemonicResult.model_validate(parsed)
    except (KeyError, IndexError, json.JSONDecodeError, ValueError) as exc:
        raise ModelUnavailableError(
            f"Gemini returned unparseable response for word={word!r}"
        ) from exc


def _parse_groq_body(body: str, word: str) -> MnemonicResult:
    try:
        data = json.loads(body)
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(_strip_fences(content))
        return MnemonicResult.model_validate(parsed)
    except (KeyError, IndexError, json.JSONDecodeError, ValueError) as exc:
        raise ModelUnavailableError(
            f"Groq returned unparseable response for word={word!r}"
        ) from exc
