"""AI Gateway package.

Public exports:
  AIGateway      — the main gateway class (implements AIProvider).
  TierProxy      — tier-locked AIProvider view returned by AIGateway.for_tier().
  RuntimeConfig  — persistent runtime configuration (provider enable/disable, etc.).
"""

from app.services.ai.gateway.gateway import AIGateway, TierProxy
from app.services.ai.gateway.runtime_config import RuntimeConfig

__all__ = ["AIGateway", "TierProxy", "RuntimeConfig"]
