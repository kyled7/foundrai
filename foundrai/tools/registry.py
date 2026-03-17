"""Tool registry."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from foundrai.agents.roles import AgentRole
    from foundrai.config import FoundrAIConfig
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


def create_tool_registry(config: FoundrAIConfig, project_path: str | Path) -> ToolRegistry:
    """Create and populate a tool registry based on configuration.

    Args:
        config: FoundrAI configuration containing sandbox settings
        project_path: Path to the project directory

    Returns:
        ToolRegistry: Registry with FileManager and CodeExecutor tools registered
    """
    from foundrai.tools.code_executor import get_code_executor
    from foundrai.tools.file_manager import FileManager

    registry = ToolRegistry()

    # Register FileManager with project path
    file_manager = FileManager(project_path)
    registry.register(file_manager)

    # Register CodeExecutor with sandbox configuration
    code_executor = get_code_executor(
        provider=config.sandbox.provider,
        timeout=config.sandbox.timeout_seconds,
        max_memory=config.sandbox.max_memory_mb,
    )
    registry.register(code_executor)

    return registry
