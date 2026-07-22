"""Concurrency-safe Round-Robin load balancer for API key selection.

Uses an asyncio.Lock to guard a shared counter so that 100 simultaneous
coroutines each get a different key in their "turn" — no two coroutines
ever read the same counter value at the same instant.

Usage:
    lb = RoundRobinLoadBalancer()
    slot = await lb.pick(healthy_slots)

The counter is unbounded (never resets) so it works correctly even when
the healthy-slot list shrinks mid-flight: `counter % len(candidates)`
always lands on a valid index regardless of the counter's magnitude.

Future extensibility: swap this class for WeightedRoundRobin or
LeastConnectionsBalancer by changing the factory in gateway.py — the
_ProviderPool just holds a reference to `LoadBalancer` by protocol.
"""
from __future__ import annotations

import asyncio
from typing import TypeVar

T = TypeVar("T")


class RoundRobinLoadBalancer:
    """Thread-safe (asyncio-safe) atomic round-robin picker."""

    __slots__ = ("_counter", "_lock")

    def __init__(self) -> None:
        self._counter: int = 0
        self._lock = asyncio.Lock()

    async def pick(self, candidates: list[T]) -> T | None:
        """Return the next candidate in strict round-robin order.

        Returns None if the candidate list is empty.
        Increments the counter under the lock so no two concurrent
        callers get the same position in the same cycle.
        """
        if not candidates:
            return None
        async with self._lock:
            idx = self._counter % len(candidates)
            self._counter += 1
        return candidates[idx]

    def reset(self) -> None:
        """Reset counter (useful in tests; not needed in production)."""
        self._counter = 0
