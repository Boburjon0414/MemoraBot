"""AI Gateway — production-grade facade for the entire AI provider infrastructure.

Public interface (what the rest of the application sees):
  - AIGateway implements AIProvider, so it drops in wherever a provider is expected.
  - AIGateway.for_tier(is_premium) returns a TierProxy — a thin wrapper that
    routes to the correct Free/Premium pool without exposing any internals.
  - ServicesMiddleware calls gateway.for_tier(is_premium) once per request and
    hands the resulting TierProxy to MnemonicService; MnemonicService calls the
    standard generate_mnemonic() — completely unaware of the gateway.

Internal routing (hidden from callers):
  generate_mnemonic_routed(word, avoid, is_premium)
    → pick tier pool (free | premium)
    → iterate providers in priority order (e.g. gemini → groq)
      → for each provider, ask the load balancer for the next healthy key slot
        → the slot tries its models in order (gemini-2.5-flash → gemini-2.5-flash-lite)
          → success  → record, return
          → quota    → rotate to next key slot
          → invalid  → disable key, rotate
          → network  → put on cooldown, try next provider
          → all keys exhausted on provider → fall through to next provider
    → all providers exhausted → raise AIProviderError

Mental-model test: 100 simultaneous users
  - Each coroutine picks a healthy slot via the atomic round-robin balancer.
  - No two coroutines touch the same lock simultaneously (one lock per pool).
  - Failed keys are marked unhealthy and excluded from picks until recovery.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from app.core.exceptions import AIProviderError
from app.services.ai.base import MnemonicProvider
from app.services.ai.gateway.errors import (
    KeyInvalidError,
    ModelUnavailableError,
    ProviderUnavailableError,
    QuotaExceededError,
)
from app.services.ai.gateway.key_health import KeyHealth
from app.services.ai.gateway.key_slot import GatewayKeySlot
from app.services.ai.gateway.load_balancer import RoundRobinLoadBalancer
from app.services.ai.gateway.runtime_config import RuntimeConfig
from app.services.ai.router import AIRequest, AIResponse, AIRouter
from app.services.ai.schemas import MnemonicResult

logger = logging.getLogger(__name__)


# ── Internal data structures ───────────────────────────────────────────────── #

@dataclass
class _ProviderPool:
    """All key slots for one provider in one tier (free or premium)."""
    provider_name: str
    tier: str  # "free" | "premium"
    slots: list[GatewayKeySlot] = field(default_factory=list)
    load_balancer: RoundRobinLoadBalancer = field(default_factory=RoundRobinLoadBalancer)

    def healthy_slots(self) -> list[GatewayKeySlot]:
        return [s for s in self.slots if s.health.is_healthy]


# ── Tier proxy ─────────────────────────────────────────────────────────────── #

class TierProxy(MnemonicProvider, AIRouter):
    """Thin AIProvider + AIRouter wrapper that locks the gateway into a specific tier.

    ServicesMiddleware creates one of these per request:
        proxy = gateway.for_tier(is_premium=True)
        MnemonicService(proxy, mnemonic_repo)

    MnemonicService calls proxy.generate_mnemonic(word, avoid) and never
    knows whether it's talking to Gemini, Groq, or a fallback chain.

    AIChatService, RAGService, QuizService etc. call proxy.complete(request)
    and likewise never know which provider responded.
    """

    def __init__(self, gateway: "AIGateway", is_premium: bool) -> None:
        self._gateway = gateway
        self._is_premium = is_premium

    @property
    def name(self) -> str:
        tier = "premium" if self._is_premium else "free"
        return f"ai-gateway/{tier}"

    @property
    def prompt_version(self) -> str:
        return self._gateway.prompt_version

    async def generate_mnemonic(
        self, word: str, avoid: list[str] | None = None
    ) -> MnemonicResult:
        return await self._gateway.generate_mnemonic_routed(
            word, avoid=avoid, is_premium=self._is_premium
        )

    async def complete(
        self,
        request: AIRequest,
        *,
        is_premium: bool = False,  # ignored — TierProxy already knows its tier
    ) -> AIResponse:
        """Route a generic AIRequest through this proxy's tier."""
        return await self._gateway.complete_routed(
            request, is_premium=self._is_premium
        )


# ── Main gateway ───────────────────────────────────────────────────────────── #

class AIGateway(MnemonicProvider, AIRouter):
    """Production AI Gateway with free/premium pools, load balancing, and failover.

    Implements both `MnemonicProvider` (for mnemonic generation) and `AIRouter`
    (for all other AI features: chat, RAG, quiz, summary, presentations).
    Both interfaces route through the same pool machinery, key rotation,
    health tracking, and tier separation — zero duplication.
    """

    def __init__(
        self,
        *,
        prompt_version: str = "v1",
        runtime_config: RuntimeConfig,
    ) -> None:
        self._prompt_version = prompt_version
        self._runtime = runtime_config

        # pools[tier][provider_name] → _ProviderPool
        self._pools: dict[str, dict[str, _ProviderPool]] = {
            "free": {},
            "premium": {},
        }

        # Gateway-level analytics (non-persisted; reset on restart)
        self._total_requests: int = 0
        self._total_errors: int = 0
        self._quota_failures: int = 0
        self._fallback_count: int = 0
        self._free_requests: int = 0
        self._premium_requests: int = 0
        self._analytics_lock = asyncio.Lock()

    # ── AIProvider interface ───────────────────────────────────────────── #

    @property
    def name(self) -> str:
        return "ai-gateway"

    @property
    def prompt_version(self) -> str:
        return self._prompt_version

    async def generate_mnemonic(
        self, word: str, avoid: list[str] | None = None
    ) -> MnemonicResult:
        """Backward-compatible entry point — routes to the FREE tier."""
        return await self.generate_mnemonic_routed(word, avoid=avoid, is_premium=False)

    def for_tier(self, is_premium: bool) -> TierProxy:
        """Return a tier-locked AIProvider view for use by MnemonicService."""
        return TierProxy(self, is_premium=is_premium)

    # ── Core routing ───────────────────────────────────────────────────── #

    async def generate_mnemonic_routed(
        self,
        word: str,
        avoid: list[str] | None = None,
        is_premium: bool = False,
    ) -> MnemonicResult:
        """Full failover routing through the configured provider pools."""
        async with self._analytics_lock:
            self._total_requests += 1
            if is_premium:
                self._premium_requests += 1
            else:
                self._free_requests += 1

        if self._runtime.maintenance_mode:
            async with self._analytics_lock:
                self._total_errors += 1
            raise AIProviderError(
                "The AI service is temporarily in maintenance mode. "
                "Please try again in a few minutes."
            )

        tier = "premium" if is_premium else "free"
        tier_pools = self._pools.get(tier, {})

        # Build the ordered list of providers to attempt
        providers_to_try = [
            p for p in self._runtime.provider_priority
            if p in self._runtime.enabled_providers and p in tier_pools
        ]

        if not providers_to_try:
            async with self._analytics_lock:
                self._total_errors += 1
            raise AIProviderError(
                f"No AI providers are currently available for {'premium' if is_premium else 'free'} "
                f"users. Please try again later."
            )

        fallback_recorded = False

        for provider_idx, provider_name in enumerate(providers_to_try):
            if provider_idx > 0 and not fallback_recorded:
                async with self._analytics_lock:
                    self._fallback_count += 1
                fallback_recorded = True

            pool = tier_pools[provider_name]
            healthy = pool.healthy_slots()

            if not healthy:
                logger.warning(
                    "All %s %s keys are unhealthy — skipping to next provider",
                    provider_name, tier,
                )
                continue

            result = await self._exhaust_pool(
                pool=pool,
                healthy=healthy,
                word=word,
                avoid=avoid,
            )
            if result is not None:
                return result

        # All providers exhausted
        async with self._analytics_lock:
            self._total_errors += 1
        raise AIProviderError(
            f"All AI providers are unavailable right now. "
            f"Please try again in a few minutes."
        )

    async def _exhaust_pool(
        self,
        pool: _ProviderPool,
        healthy: list[GatewayKeySlot],
        word: str,
        avoid: list[str] | None,
    ) -> MnemonicResult | None:
        """Try every healthy slot in the pool (round-robin), return result or None."""
        remaining = list(healthy)  # mutable working copy for this routing pass

        while remaining:
            slot = await pool.load_balancer.pick(remaining)
            if slot is None:
                break

            # Remove from remaining so we don't retry the same slot twice
            remaining = [s for s in remaining if s.key_index != slot.key_index]

            try:
                return await slot.generate(word, avoid=avoid)

            except QuotaExceededError:
                async with self._analytics_lock:
                    self._quota_failures += 1
                logger.warning("💸 Quota exceeded on %s — rotating key", slot.label)

            except KeyInvalidError:
                logger.error("🔑 Invalid key on %s — disabling permanently", slot.label)
                await slot.health.disable()

            except ProviderUnavailableError:
                logger.warning("🔌 Provider unreachable via %s — skipping pool", slot.label)
                # If the provider itself is down, other keys on it will fail too
                break

            except ModelUnavailableError:
                logger.warning("🤖 All models exhausted on %s — skipping key", slot.label)

            except Exception:
                logger.exception("Unexpected error on %s", slot.label)

        return None

    # ── AIRouter interface ─────────────────────────────────────────────── #

    async def complete(
        self,
        request: AIRequest,
        *,
        is_premium: bool = False,
    ) -> AIResponse:
        """Entry point for generic AI requests — routes to the free tier by default.

        Prefer calling this via a `TierProxy` obtained from `for_tier()` so
        the tier is determined once per request by `ServicesMiddleware`, not
        per-call by each service.
        """
        return await self.complete_routed(request, is_premium=is_premium)

    async def complete_routed(
        self,
        request: AIRequest,
        is_premium: bool = False,
    ) -> AIResponse:
        """Full failover routing for a generic AIRequest through configured pools.

        Mirrors `generate_mnemonic_routed()` exactly — same analytics tracking,
        same maintenance-mode check, same provider priority ordering, same
        pool exhaustion logic — but calls `slot.complete_request()` instead of
        `slot.generate()`.
        """
        async with self._analytics_lock:
            self._total_requests += 1
            if is_premium:
                self._premium_requests += 1
            else:
                self._free_requests += 1

        if self._runtime.maintenance_mode:
            async with self._analytics_lock:
                self._total_errors += 1
            raise AIProviderError(
                "The AI service is temporarily in maintenance mode. "
                "Please try again in a few minutes."
            )

        tier = "premium" if is_premium else "free"
        tier_pools = self._pools.get(tier, {})

        providers_to_try = [
            p for p in self._runtime.provider_priority
            if p in self._runtime.enabled_providers and p in tier_pools
        ]

        if not providers_to_try:
            async with self._analytics_lock:
                self._total_errors += 1
            raise AIProviderError(
                f"No AI providers are currently available for "
                f"{'premium' if is_premium else 'free'} users. Please try again later."
            )

        fallback_recorded = False

        for provider_idx, provider_name in enumerate(providers_to_try):
            if provider_idx > 0 and not fallback_recorded:
                async with self._analytics_lock:
                    self._fallback_count += 1
                fallback_recorded = True

            pool = tier_pools[provider_name]
            healthy = pool.healthy_slots()

            if not healthy:
                logger.warning(
                    "All %s %s keys are unhealthy — skipping to next provider",
                    provider_name, tier,
                )
                continue

            result = await self._exhaust_pool_generic(
                pool=pool,
                healthy=healthy,
                request=request,
            )
            if result is not None:
                return result

        async with self._analytics_lock:
            self._total_errors += 1
        raise AIProviderError(
            "All AI providers are unavailable right now. "
            "Please try again in a few minutes."
        )

    async def _exhaust_pool_generic(
        self,
        pool: _ProviderPool,
        healthy: list[GatewayKeySlot],
        request: AIRequest,
    ) -> AIResponse | None:
        """Try every healthy slot in the pool for a generic request, return result or None."""
        remaining = list(healthy)

        while remaining:
            slot = await pool.load_balancer.pick(remaining)
            if slot is None:
                break

            remaining = [s for s in remaining if s.key_index != slot.key_index]

            try:
                return await slot.complete_request(request)

            except QuotaExceededError:
                async with self._analytics_lock:
                    self._quota_failures += 1
                logger.warning("💸 Quota exceeded on %s — rotating key", slot.label)

            except KeyInvalidError:
                logger.error("🔑 Invalid key on %s — disabling permanently", slot.label)
                await slot.health.disable()

            except ProviderUnavailableError:
                logger.warning("🔌 Provider unreachable via %s — skipping pool", slot.label)
                break

            except ModelUnavailableError:
                logger.warning("🤖 All models exhausted on %s — skipping key", slot.label)

            except Exception:
                logger.exception("Unexpected error on %s (generic request)", slot.label)

        return None

    # ── Slot registration (called by factory at startup) ──────────────── #

    def register_slot(self, slot: GatewayKeySlot) -> None:
        """Register one key slot into the correct pool. Called once per key."""
        tier = slot.tier
        provider = slot.provider_name
        if provider not in self._pools[tier]:
            self._pools[tier][provider] = _ProviderPool(
                provider_name=provider, tier=tier
            )
        # Apply persisted runtime overrides
        if self._runtime.is_key_disabled(provider, tier, slot.key_index):
            slot.health.is_enabled = False
        if self._runtime.is_key_paused(provider, tier, slot.key_index):
            slot.health.is_paused = True

        self._pools[tier][provider].slots.append(slot)
        logger.debug(
            "Registered %s → %s/%s pool (models: %s)",
            slot.label,
            tier,
            provider,
            ", ".join(slot._models),
        )

    # ── Lifecycle ──────────────────────────────────────────────────────── #

    async def close(self) -> None:
        """Gracefully close every HTTP session. Call at bot shutdown."""
        for tier_pools in self._pools.values():
            for pool in tier_pools.values():
                for slot in pool.slots:
                    await slot.close()
        logger.info("AI Gateway shut down — all HTTP sessions closed")

    # ── Introspection for admin panel ──────────────────────────────────── #

    def get_all_key_health(self) -> list[KeyHealth]:
        result: list[KeyHealth] = []
        for tier_pools in self._pools.values():
            for pool in tier_pools.values():
                for slot in pool.slots:
                    result.append(slot.health)
        return result

    def get_provider_stats(self) -> list[dict]:
        stats: list[dict] = []
        for tier in ("free", "premium"):
            tier_pools = self._pools.get(tier, {})
            for provider_name, pool in tier_pools.items():
                total = len(pool.slots)
                healthy = len(pool.healthy_slots())
                reqs = sum(s.health.requests_served for s in pool.slots)
                errs = sum(s.health.failure_count for s in pool.slots)
                active = [s for s in pool.slots if s.health.success_count > 0]
                avg_lat = (
                    sum(s.health.avg_latency_ms for s in active) / len(active)
                    if active else 0.0
                )
                stats.append({
                    "provider": provider_name,
                    "tier": tier,
                    "total_keys": total,
                    "healthy_keys": healthy,
                    "requests": reqs,
                    "errors": errs,
                    "avg_latency_ms": round(avg_lat, 1),
                    "status": "🟢 Online" if healthy > 0 else "🔴 Down",
                    "priority": (
                        self._runtime.provider_priority.index(provider_name) + 1
                        if provider_name in self._runtime.provider_priority
                        else 99
                    ),
                })
        return sorted(stats, key=lambda x: (x["tier"], x["priority"]))

    def get_gateway_analytics(self) -> dict:
        all_health = self.get_all_key_health()
        return {
            "total_requests": self._total_requests,
            "total_errors": self._total_errors,
            "quota_failures": self._quota_failures,
            "fallback_count": self._fallback_count,
            "free_requests": self._free_requests,
            "premium_requests": self._premium_requests,
            "healthy_keys": sum(1 for h in all_health if h.is_healthy),
            "total_keys": len(all_health),
            "enabled_providers": self._runtime.enabled_providers,
            "maintenance_mode": self._runtime.maintenance_mode,
        }

    # ── Admin key management ───────────────────────────────────────────── #

    def _find_slot(
        self, provider: str, tier: str, key_index: int
    ) -> GatewayKeySlot | None:
        pool = self._pools.get(tier, {}).get(provider)
        if not pool:
            return None
        return next((s for s in pool.slots if s.key_index == key_index), None)

    async def admin_enable_key(
        self, provider: str, tier: str, key_index: int
    ) -> bool:
        slot = self._find_slot(provider, tier, key_index)
        if not slot:
            return False
        await slot.health.enable()
        await self._runtime.set_key_disabled(provider, tier, key_index, False)
        return True

    async def admin_disable_key(
        self, provider: str, tier: str, key_index: int
    ) -> bool:
        slot = self._find_slot(provider, tier, key_index)
        if not slot:
            return False
        await slot.health.disable()
        await self._runtime.set_key_disabled(provider, tier, key_index, True)
        return True

    async def admin_pause_key(
        self, provider: str, tier: str, key_index: int
    ) -> bool:
        slot = self._find_slot(provider, tier, key_index)
        if not slot:
            return False
        await slot.health.pause()
        await self._runtime.set_key_paused(provider, tier, key_index, True)
        return True

    async def admin_resume_key(
        self, provider: str, tier: str, key_index: int
    ) -> bool:
        slot = self._find_slot(provider, tier, key_index)
        if not slot:
            return False
        await slot.health.resume()
        await self._runtime.set_key_paused(provider, tier, key_index, False)
        return True

    async def admin_test_key(
        self, provider: str, tier: str, key_index: int
    ) -> tuple[bool, str]:
        """Live test a specific key with a harmless word. Returns (ok, message)."""
        slot = self._find_slot(provider, tier, key_index)
        if not slot:
            return False, f"Key not found: {provider}/{tier}/#{key_index}"
        try:
            await slot.generate("apple")  # harmless test word
            return True, f"✅ {slot.label} responded correctly"
        except Exception as exc:
            return False, f"❌ {slot.label} failed: {type(exc).__name__}: {exc}"

    async def admin_enable_provider(self, name: str) -> None:
        await self._runtime.enable_provider(name)

    async def admin_disable_provider(self, name: str) -> None:
        await self._runtime.disable_provider(name)

    async def admin_set_maintenance(self, enabled: bool) -> None:
        await self._runtime.set_maintenance_mode(enabled)

    async def admin_set_priority(self, priority: list[str]) -> None:
        await self._runtime.set_provider_priority(priority)
