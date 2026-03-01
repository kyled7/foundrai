"""AgentRuntime — executes agent LLM interaction loops."""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field


class RuntimeResult(BaseModel):
    """Result of a single AgentRuntime execution."""

    output: str
    parsed: dict | list | None = None
    artifacts: list[Any] = Field(default_factory=list)
    tokens_used: int = 0
    success: bool = True


class AgentRuntime:
    """Executes an agent's LLM interaction loop using LangGraph ReAct pattern."""

    def __init__(
        self,
        llm_client: Any,
        event_log: Any,
        max_iterations: int = 10,
    ) -> None:
        self.llm_client = llm_client
        self.event_log = event_log
        self.max_iterations = max_iterations

    async def run(
        self,
        messages: list[dict],
        tools: list[Any] | None = None,
        response_format: str | None = None,
    ) -> RuntimeResult:
        """Execute the ReAct loop."""
        # For simple cases (no tools), just call LLM directly
        response = await self.llm_client.completion(messages)

        parsed = None
        if response_format == "json":
            parsed = self._parse_json(response.content)

        return RuntimeResult(
            output=response.content,
            parsed=parsed,
            artifacts=[],
            tokens_used=response.total_tokens,
            success=True,
        )

    def _to_langchain_messages(self, messages: list[dict]) -> list:  # noqa: ANN201
        """Convert dict messages to LangChain message objects."""
        mapping: dict[str, type] = {
            "system": SystemMessage,
            "user": HumanMessage,
            "assistant": AIMessage,
        }
        return [mapping[m["role"]](content=m["content"]) for m in messages]

    def _parse_json(self, content: str) -> dict | list | None:
        """Extract JSON from LLM response (handles markdown code blocks)."""
        # Try direct parse
        try:
            return json.loads(content)  # type: ignore[no-any-return]
        except json.JSONDecodeError:
            pass
        # Try extracting from ```json ... ``` or ``` ... ``` block
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))  # type: ignore[no-any-return]
            except json.JSONDecodeError:
                pass
        return None

    def _extract_token_usage(self, result: dict) -> int:
        """Extract total token usage from LangGraph result."""
        total = 0
        for msg in result.get("messages", []):
            usage = getattr(msg, "usage_metadata", None)
            if usage and isinstance(usage, dict):
                total += usage.get("total_tokens", 0)
        return total

    def _collect_artifacts(self, result: dict) -> list:  # noqa: ANN201
        """Collect artifacts from tool call results."""
        return []
