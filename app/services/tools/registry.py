"""ToolRegistry: the single source of truth for all MemoraBot platform tools.

New tools are added by calling `registry.register(MyTool())` in
`PlatformContainer.initialize()`. Nothing else changes — AIPlanner,
AIChatService, and every future AI feature read from the same registry.

Extensibility contract
----------------------
Adding a new tool requires:
  1. Create a class that inherits from `PlatformTool` in `app/services/tools/`.
  2. Call `registry.register(MyTool())` in `PlatformContainer.initialize()`.
  3. Done. No changes to AIPlanner, ToolRegistry, or any existing code.

The registry provides:
  - `get(name)` — fetch a tool by its canonical name.
  - `list_for_feature(feature)` — all tools available to a given feature.
  - `catalogue()` — human-readable summary of all tools (for logging/debug).
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.tools.base import PlatformTool, ToolContext, ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Holds all registered platform tools.

    Instantiated once in PlatformContainer. Thread-safe for concurrent
    reads (all writes happen during single-threaded startup).
    """

    def __init__(self) -> None:
        self._tools: dict[str, PlatformTool] = {}

    def register(self, tool: PlatformTool) -> None:
        """Register `tool` under its canonical name.

        Overwrites any previously registered tool with the same name —
        allows test overrides with mock tools.
        """
        name = tool.definition.name
        self._tools[name] = tool
        logger.debug("ToolRegistry: registered %r (%s)", name, type(tool).__name__)

    def get(self, name: str) -> PlatformTool | None:
        """Return the tool with `name`, or None if not registered."""
        return self._tools.get(name)

    def list_for_feature(self, feature: str) -> list[PlatformTool]:
        """Return all tools whose `definition.features` includes `feature`.

        Used by AIPlanner to build the candidate tool set for a request.
        An empty `features` list means the tool is available to all features.
        """
        result = []
        for tool in self._tools.values():
            f = tool.definition.features
            if not f or feature in f:
                result.append(tool)
        return result

    def all_tools(self) -> list[PlatformTool]:
        """Return every registered tool."""
        return list(self._tools.values())

    def catalogue(self) -> str:
        """Return a human-readable summary of all registered tools.

        Used for logging at startup and for debugging planner decisions.
        """
        if not self._tools:
            return "ToolRegistry: (empty)"
        lines = ["ToolRegistry:"]
        for name, tool in sorted(self._tools.items()):
            d = tool.definition
            features = ", ".join(d.features) if d.features else "all"
            lines.append(f"  [{name}] — {d.description} (features: {features})")
        return "\n".join(lines)

    async def execute(
        self,
        name: str,
        context: ToolContext,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute a named tool and return its result.

        Returns ToolResult.fail() if the tool is not registered.
        Never raises — all exceptions are captured in ToolResult.fail().
        """
        tool = self.get(name)
        if tool is None:
            return ToolResult.fail(name, f"Tool {name!r} is not registered.")
        try:
            result = await tool.execute(context, **kwargs)
            result.tool_name = name
            return result
        except Exception as exc:
            logger.exception("ToolRegistry: unexpected error in tool %r", name)
            return ToolResult.fail(name, str(exc))
