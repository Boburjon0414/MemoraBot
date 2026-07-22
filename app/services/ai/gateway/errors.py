"""Gateway-internal exception hierarchy for routing decisions.

These are NEVER exposed outside the gateway layer — every exception here is
caught and translated into AIProviderError before reaching MnemonicService.
The gateway uses them to decide:
  - QuotaExceededError   → rotate to the next API key
  - KeyInvalidError      → permanently disable the key, rotate
  - ModelUnavailableError→ skip to the next model on the same key
  - ProviderUnavailableError → skip to the next provider
  - TransientError       → retry once, then rotate
"""
from __future__ import annotations


class GatewayRoutingError(Exception):
    """Base for all gateway-internal routing exceptions."""


class QuotaExceededError(GatewayRoutingError):
    """HTTP 429 — quota or rate-limit exhausted.

    Signals the gateway to rotate to the next API key immediately.
    The key is not disabled; it may recover after a cooldown.
    """
    def __init__(self, retry_after: float = 0.0) -> None:
        self.retry_after = retry_after
        super().__init__(f"Quota exceeded (retry_after={retry_after:.0f}s)")


class KeyInvalidError(GatewayRoutingError):
    """HTTP 401 or 403 — this API key is invalid or revoked.

    Signals the gateway to permanently disable the key so it is never
    retried in this session (admin must re-enable it manually).
    """


class ModelUnavailableError(GatewayRoutingError):
    """Model not found, deprecated, or returned a non-parseable response.

    Signals the key slot to try the next model in its ordered list.
    If all models are exhausted, the key is skipped.
    """


class ProviderUnavailableError(GatewayRoutingError):
    """Network error, DNS failure, or HTTP 503.

    Signals the gateway to put the key/provider on a short cooldown
    and move on to the next provider in the priority list.
    """


class TransientError(GatewayRoutingError):
    """Temporary server error (HTTP 500 / 529).

    Signals the key slot to try the next model; if all models fail with
    transient errors the gateway rotates to the next key.
    """
    def __init__(self, status: int) -> None:
        self.status = status
        super().__init__(f"Transient HTTP {status}")
