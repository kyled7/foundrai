"""Tool registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from foundrai.agents.roles import AgentRole
    from foundrai.tools.base import BaseTool


class ToolRegistry:
    """Maps tool names to tool instances."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        """Get a tool by name."""
        if name not in self._tools:
            raise KeyError(f"Tool not found: {name}")
        return self._tools[name]

    def get_tools_for_role(self, role: AgentRole) -> list[BaseTool]:
        """Return tool instances matching the role's tool list."""
        return [self._tools[name] for name in role.tools if name in self._tools]
