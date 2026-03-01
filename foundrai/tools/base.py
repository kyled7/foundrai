"""Base tool classes."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel


class ToolInput(BaseModel):
    """Base class for tool input schemas."""

    pass


class ToolOutput(BaseModel):
    """Standard tool output."""

    success: bool
    output: str
    error: str | None = None


class BaseTool(ABC):
    """Abstract base for all FoundrAI tools."""

    name: str
    description: str
    input_schema: type[ToolInput]

    @abstractmethod
    async def execute(self, input: ToolInput) -> ToolOutput:  # noqa: A002
        """Execute the tool with validated input."""
        ...

    def to_langchain_tool(self) -> object:
        """Convert to LangChain StructuredTool."""
        from langchain_core.tools import StructuredTool

        return StructuredTool.from_function(
            coroutine=self._execute_wrapper,
            name=self.name,
            description=self.description,
            args_schema=self.input_schema,
        )

    async def _execute_wrapper(self, **kwargs: object) -> str:
        """Wrapper that converts kwargs → ToolInput → ToolOutput → str."""
        tool_input = self.input_schema(**kwargs)
        result = await self.execute(tool_input)
        if result.success:
            return result.output
        else:
            return f"Error: {result.error}"
