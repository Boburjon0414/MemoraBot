"""Runtime configuration — admin-changeable settings persisted to JSON.

Lets admins enable/disable providers, reorder priority, and toggle
maintenance mode WITHOUT restarting the bot. Changes take effect on
the next incoming request (no reload needed).

Storage: `gateway_runtime.json` in the working directory (same place as
the SQLite database). A missing file is not an error — defaults are used
and the file is created on the first admin action.

Thread/async safety: every write takes an asyncio.Lock and immediately
flushes to disk. Reads access the in-memory dict directly (CPython dict
reads are atomic for simple key lookups).
"""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_FILE = Path("gateway_runtime.json")

_DEFAULTS: dict = {
    "provider_priority": ["gemini", "groq"],
    "enabled_providers": ["gemini", "groq"],
    "maintenance_mode": False,
    # Persisted per-key overrides — format: "provider:tier:index" → bool
    "disabled_keys": {},
    "paused_keys": {},
}


class RuntimeConfig:
    """Persistent, in-memory runtime configuration for the AI gateway."""

    def __init__(self, path: Path = _DEFAULT_FILE) -> None:
        self._path = path
        self._lock = asyncio.Lock()
        import copy
        self._data: dict = copy.deepcopy(_DEFAULTS)

    # ── Lifecycle ──────────────────────────────────────────────────────── #

    async def load(self) -> None:
        """Load persisted config from disk. Call once at bot startup."""
        if not self._path.exists():
            logger.info(
                "gateway_runtime.json not found — using defaults "
                "(will be created on first admin action)"
            )
            return
        try:
            raw = self._path.read_text(encoding="utf-8")
            loaded: dict = json.loads(raw)
            # Merge rather than replace, so new keys get their defaults
            for k, v in loaded.items():
                self._data[k] = v
            logger.info("Loaded runtime config from %s", self._path)
        except Exception:
            logger.exception(
                "Failed to parse gateway_runtime.json — using defaults"
            )

    async def _save(self) -> None:
        """Write current in-memory state to disk (must hold _lock before calling)."""
        try:
            self._path.write_text(
                json.dumps(self._data, indent=2, default=str),
                encoding="utf-8",
            )
        except Exception:
            logger.exception("Failed to persist gateway_runtime.json")

    # ── Read-only accessors (no lock required — see module docstring) ─── #

    @property
    def provider_priority(self) -> list[str]:
        return list(self._data.get("provider_priority", _DEFAULTS["provider_priority"]))

    @property
    def enabled_providers(self) -> list[str]:
        return list(self._data.get("enabled_providers", _DEFAULTS["enabled_providers"]))

    @property
    def maintenance_mode(self) -> bool:
        return bool(self._data.get("maintenance_mode", False))

    def is_key_disabled(self, provider: str, tier: str, index: int) -> bool:
        key = f"{provider}:{tier}:{index}"
        return bool(self._data.get("disabled_keys", {}).get(key, False))

    def is_key_paused(self, provider: str, tier: str, index: int) -> bool:
        key = f"{provider}:{tier}:{index}"
        return bool(self._data.get("paused_keys", {}).get(key, False))

    def to_dict(self) -> dict:
        """Full snapshot for the admin panel."""
        return dict(self._data)

    # ── Write actions (async — acquire lock, mutate, then save) ──────── #

    async def enable_provider(self, name: str) -> None:
        async with self._lock:
            enabled: set[str] = set(self._data.get("enabled_providers", []))
            enabled.add(name)
            self._data["enabled_providers"] = list(enabled)
            await self._save()
        logger.info("Provider '%s' enabled (runtime)", name)

    async def disable_provider(self, name: str) -> None:
        async with self._lock:
            enabled: set[str] = set(self._data.get("enabled_providers", []))
            enabled.discard(name)
            self._data["enabled_providers"] = list(enabled)
            await self._save()
        logger.info("Provider '%s' disabled (runtime)", name)

    async def set_provider_priority(self, priority: list[str]) -> None:
        async with self._lock:
            self._data["provider_priority"] = list(priority)
            await self._save()
        logger.info("Provider priority set to %s (runtime)", priority)

    async def set_maintenance_mode(self, enabled: bool) -> None:
        async with self._lock:
            self._data["maintenance_mode"] = enabled
            await self._save()
        logger.info("Maintenance mode %s (runtime)", "ON" if enabled else "OFF")

    async def set_key_disabled(
        self, provider: str, tier: str, index: int, disabled: bool
    ) -> None:
        key = f"{provider}:{tier}:{index}"
        async with self._lock:
            bucket: dict = self._data.setdefault("disabled_keys", {})
            if disabled:
                bucket[key] = True
            else:
                bucket.pop(key, None)
            await self._save()
        action = "disabled" if disabled else "enabled"
        logger.info(
            "%s Key #%d (%s/%s) %s (runtime)",
            provider.title(), index, tier, "key", action,
        )

    async def set_key_paused(
        self, provider: str, tier: str, index: int, paused: bool
    ) -> None:
        key = f"{provider}:{tier}:{index}"
        async with self._lock:
            bucket: dict = self._data.setdefault("paused_keys", {})
            if paused:
                bucket[key] = True
            else:
                bucket.pop(key, None)
            await self._save()
        action = "paused" if paused else "resumed"
        logger.info(
            "%s Key #%d (%s/%s) %s (runtime)",
            provider.title(), index, tier, "key", action,
        )
