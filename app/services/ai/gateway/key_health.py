"""Per-API-key health tracking.

Every GatewayKeySlot owns one KeyHealth instance. The gateway reads
`is_healthy` to decide whether a key is eligible for the next request,
and calls the async mutation helpers (record_success, record_failure, …)
after each outcome.

Design notes:
- All mutation methods take an asyncio.Lock to prevent race conditions
  when 10–100 concurrent users hit the same slot simultaneously.
- `is_healthy` is a pure property — safe to read without a lock because
  Python bool reads are atomic in CPython and we only need approximate
  freshness here.
- Key values are NEVER stored or logged; only the 1-based index is kept.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


@dataclass
class KeyHealth:
    """Mutable health record for one API key slot."""

    # Identification (never the actual key value)
    key_index: int       # 1-based: "Gemini Key #2"
    provider_name: str   # "gemini" | "groq" | …
    tier: str            # "free" | "premium"

    # Admin-controlled flags
    is_enabled: bool = True
    is_paused: bool = False

    # Counters
    success_count: int = 0
    failure_count: int = 0
    consecutive_failures: int = 0
    requests_served: int = 0
    _total_latency_ms: float = field(default=0.0, repr=False)

    # Timestamps
    last_success: datetime | None = None
    last_failure: datetime | None = None
    cooldown_until: datetime | None = None

    # Concurrency guard
    _lock: asyncio.Lock = field(
        default_factory=asyncio.Lock, repr=False, compare=False
    )

    # ── Derived properties (read without lock — see module docstring) ── #

    @property
    def avg_latency_ms(self) -> float:
        if self.success_count == 0:
            return 0.0
        return round(self._total_latency_ms / self.success_count, 1)

    @property
    def is_healthy(self) -> bool:
        """True when the key may receive the next request."""
        if not self.is_enabled or self.is_paused:
            return False
        if self.cooldown_until and _utcnow() < self.cooldown_until:
            return False
        return True

    @property
    def label(self) -> str:
        return f"{self.provider_name.title()} Key #{self.key_index} ({self.tier})"

    # ── Mutation helpers (async, protected by lock) ──────────────────── #

    async def record_success(self, latency_ms: float) -> None:
        async with self._lock:
            self.success_count += 1
            self.requests_served += 1
            self.consecutive_failures = 0
            self.last_success = _utcnow()
            self._total_latency_ms += latency_ms
            self.cooldown_until = None  # clear any active cooldown

    async def record_failure(self, cooldown_seconds: float = 0.0) -> None:
        async with self._lock:
            self.failure_count += 1
            self.requests_served += 1
            self.consecutive_failures += 1
            self.last_failure = _utcnow()
            if cooldown_seconds > 0:
                self.cooldown_until = _utcnow() + timedelta(seconds=cooldown_seconds)

    async def disable(self) -> None:
        """Permanently disable until an admin re-enables."""
        async with self._lock:
            self.is_enabled = False

    async def enable(self) -> None:
        """Re-enable and reset the consecutive-failure streak."""
        async with self._lock:
            self.is_enabled = True
            self.consecutive_failures = 0
            self.cooldown_until = None

    async def pause(self) -> None:
        """Temporarily pause without clearing counters."""
        async with self._lock:
            self.is_paused = True

    async def resume(self) -> None:
        async with self._lock:
            self.is_paused = False

    # ── Serialisation for admin panel ────────────────────────────────── #

    def to_dict(self) -> dict:
        return {
            "key_index": self.key_index,
            "provider": self.provider_name,
            "tier": self.tier,
            "label": self.label,
            "is_enabled": self.is_enabled,
            "is_paused": self.is_paused,
            "is_healthy": self.is_healthy,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "consecutive_failures": self.consecutive_failures,
            "requests_served": self.requests_served,
            "avg_latency_ms": self.avg_latency_ms,
            "last_success": (
                self.last_success.strftime("%H:%M:%S") if self.last_success else "—"
            ),
            "last_failure": (
                self.last_failure.strftime("%H:%M:%S") if self.last_failure else "—"
            ),
            "cooldown_until": (
                self.cooldown_until.strftime("%H:%M:%S") if self.cooldown_until else None
            ),
        }
