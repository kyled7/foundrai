"""AgentRuntime — executes agent LLM interaction loops."""

from __future__ import annotations

import json
import re
import time
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
        token_store: Any | None = None,
        budget_manager: Any | None = None,
        trace_store: Any | None = None,
        agent_role: str = "",
        sprint_id: str = "",
        project_id: str = "",
        task_id: str | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.event_log = event_log
        self.max_iterations = max_iterations
        self.token_store = token_store
        self.budget_manager = budget_manager
        self.trace_store = trace_store
        self.agent_role = agent_role
        self.sprint_id = sprint_id
        self.project_id = project_id
        self.task_id = task_id

    async def run(
        self,
        messages: list[dict],
        tools: list[Any] | None = None,
        response_format: str | None = None,
    ) -> RuntimeResult:
        """Execute the ReAct loop."""
        # Budget check before LLM call
        if self.budget_manager and self.sprint_id:
            allowed = await self.budget_manager.enforce_budget(
                self.sprint_id, self.agent_role or None
            )
            if not allowed:
                return RuntimeResult(
                    output="Budget exceeded. Cannot proceed.",
                    parsed=None,
                    artifacts=[],
                    tokens_used=0,
                    success=False,
                )

        # For simple cases (no tools), just call LLM directly
        _start_time = time.monotonic()
        response = await self.llm_client.completion(messages)
        _duration_ms = int((time.monotonic() - _start_time) * 1000)

        # Record token usage if token_store is available
        if self.token_store and self.agent_role:
            try:
                from foundrai.models.token_usage import TokenUsage

                usage = TokenUsage(
                    task_id=self.task_id,
                    sprint_id=self.sprint_id or None,
                    project_id=self.project_id or None,
                    agent_role=self.agent_role,
                    model=getattr(self.llm_client, "model", "unknown"),
                    prompt_tokens=getattr(response, "prompt_tokens", 0),
                    completion_tokens=getattr(response, "completion_tokens", 0),
                    total_tokens=response.total_tokens,
                    cost_usd=getattr(response, "cost_usd", 0.0),
                )
                await self.token_store.record_usage(usage)
            except Exception:
                pass  # Don't break execution if tracking fails

        # Record decision trace if trace_store is available
        if self.trace_store and self.agent_role:
            try:
                from foundrai.models.decision_trace import DecisionTrace

                prompt_text = json.dumps(messages) if messages else ""
                trace = DecisionTrace(
                    task_id=self.task_id,
                    sprint_id=self.sprint_id or None,
                    agent_role=self.agent_role,
                    model=getattr(self.llm_client, "model", "unknown"),
                    prompt=prompt_text,
                    response=response.content,
                    thinking=getattr(response, "thinking", None),
                    tool_calls=getattr(response, "tool_calls", []) or [],
                    tokens_used=response.total_tokens,
                    cost_usd=getattr(response, "cost_usd", 0.0),
                    duration_ms=_duration_ms,
                )
                await self.trace_store.record_trace(trace)
            except Exception:
                pass  # Don't break execution if tracing fails

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
