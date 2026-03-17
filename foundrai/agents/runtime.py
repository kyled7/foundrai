"""AgentRuntime — executes agent LLM interaction loops with ReAct tool use."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from foundrai.utils.retry import retry_async

logger = logging.getLogger(__name__)


class RuntimeResult(BaseModel):
    """Result of a single AgentRuntime execution."""

    output: str
    parsed: dict | list | None = None
    artifacts: list[Any] = Field(default_factory=list)
    tokens_used: int = 0
    success: bool = True


class AgentRuntime:
    """Executes an agent's LLM interaction loop using a ReAct pattern with tool use."""

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
        timeout: float | None = None,
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
        self.timeout = timeout

    async def run(
        self,
        messages: list[dict],
        tools: list[Any] | None = None,
        response_format: str | None = None,
    ) -> RuntimeResult:
        """Execute the ReAct loop with optional tool use.

        When tools are provided, the agent can call tools iteratively up to
        max_iterations times. Each iteration:
        1. Call LLM with messages + tool schemas
        2. If LLM returns tool_calls, execute them and append results
        3. Repeat until LLM returns a final text response (no tool_calls)
        """
        # Apply timeout if configured
        if self.timeout is not None:
            try:
                return await asyncio.wait_for(
                    self._run_internal(messages, tools, response_format),
                    timeout=self.timeout,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "Agent %s execution timed out after %s seconds for task %s",
                    self.agent_role, self.timeout, self.task_id,
                )
                return RuntimeResult(
                    output=f"Task execution timed out after {self.timeout} seconds.",
                    parsed=None,
                    artifacts=[],
                    tokens_used=0,
                    success=False,
                )
        else:
            return await self._run_internal(messages, tools, response_format)

    async def _run_internal(
        self,
        messages: list[dict],
        tools: list[Any] | None = None,
        response_format: str | None = None,
    ) -> RuntimeResult:
        """Internal execution logic for the ReAct loop."""
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

        # Build tool schemas for the LLM if tools are provided
        tool_map: dict[str, Any] = {}
        tool_schemas: list[dict] | None = None
        if tools:
            tool_map = {t.name: t for t in tools}
            tool_schemas = [self._tool_to_schema(t) for t in tools]

        total_tokens = 0
        all_tool_calls: list[dict] = []
        artifacts: list[Any] = []
        working_messages = list(messages)
        final_content = ""

        for iteration in range(self.max_iterations):
            _start_time = time.monotonic()
            # Wrap LLM call with retry logic for transient failures
            response = await retry_async(
                lambda: self.llm_client.completion(working_messages, tools=tool_schemas),
                max_retries=3,
                backoff_base=1.0,
                auto_classify_retryable=True,
            )
            _duration_ms = int((time.monotonic() - _start_time) * 1000)
            total_tokens += response.total_tokens

            # Record per-iteration token usage
            await self._record_token_usage(response)

            # Check for tool calls in the response
            response_tool_calls = getattr(response, "tool_calls", None) or []

            if not response_tool_calls or not tool_map:
                # No tool calls — this is the final response
                final_content = response.content
                await self._record_trace(
                    working_messages, response, all_tool_calls, _duration_ms, total_tokens
                )
                break

            # Process tool calls
            # Append assistant message with tool calls
            working_messages.append({
                "role": "assistant",
                "content": response.content or "",
                "tool_calls": response_tool_calls,
            })

            for tc in response_tool_calls:
                is_dict = isinstance(tc, dict)
                tool_name = tc.get("name", "") if is_dict else getattr(tc, "name", "")
                tool_args = tc.get("arguments", {}) if is_dict else getattr(tc, "arguments", {})
                fallback_id = f"call_{iteration}"
                tool_id = tc.get("id", fallback_id) if is_dict else getattr(tc, "id", fallback_id)

                all_tool_calls.append({"name": tool_name, "arguments": tool_args})

                if tool_name in tool_map:
                    tool = tool_map[tool_name]
                    try:
                        tool_input = tool.input_schema(**tool_args)
                        tool_result = await tool.execute(tool_input)
                        if tool_result.success:
                            result_text = tool_result.output
                            artifacts.extend(
                                self._extract_tool_artifacts(tool_name, tool_args, tool_result)
                            )
                        else:
                            result_text = f"Error: {tool_result.error}"
                    except Exception as e:
                        result_text = f"Tool execution error: {e}"
                        logger.warning("Tool %s failed: %s", tool_name, e)
                else:
                    result_text = f"Unknown tool: {tool_name}"

                # Append tool result
                working_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": result_text,
                })

                # Log tool usage event
                await self._emit_tool_event(tool_name, tool_args, result_text)
        else:
            # Max iterations reached
            final_content = response.content if response else "Max tool iterations reached."
            logger.warning(
                "Agent %s hit max iterations (%d) for task %s",
                self.agent_role, self.max_iterations, self.task_id,
            )

        parsed = None
        if response_format == "json":
            parsed = self._parse_json(final_content)

        return RuntimeResult(
            output=final_content,
            parsed=parsed,
            artifacts=artifacts,
            tokens_used=total_tokens,
            success=True,
        )

    async def _record_token_usage(self, response: Any) -> None:
        """Record token usage for a single LLM call."""
        if not self.token_store or not self.agent_role:
            return
        try:
            from foundrai.models.token_usage import TokenUsage

            model = getattr(self.llm_client, "model", "unknown")
            prompt_tokens = getattr(response, "prompt_tokens", 0)
            completion_tokens = getattr(response, "completion_tokens", 0)

            # Calculate cost if cost_calculator is available
            cost_usd = 0.0
            try:
                from foundrai.orchestration.cost_calculator import calculate_cost
                cost_usd = calculate_cost(model, prompt_tokens, completion_tokens)
            except ImportError:
                cost_usd = getattr(response, "cost_usd", 0.0)

            usage = TokenUsage(
                task_id=self.task_id,
                sprint_id=self.sprint_id or None,
                project_id=self.project_id or None,
                agent_role=self.agent_role,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=response.total_tokens,
                cost_usd=cost_usd,
            )
            await self.token_store.record_usage(usage)
        except Exception:
            pass  # Don't break execution if tracking fails

    async def _record_trace(
        self,
        messages: list[dict],
        response: Any,
        tool_calls: list[dict],
        duration_ms: int,
        total_tokens: int,
    ) -> None:
        """Record a decision trace for the full interaction."""
        if not self.trace_store or not self.agent_role:
            return
        try:
            from foundrai.models.decision_trace import DecisionTrace

            model = getattr(self.llm_client, "model", "unknown")
            prompt_tokens = getattr(response, "prompt_tokens", 0)
            completion_tokens = getattr(response, "completion_tokens", 0)

            cost_usd = 0.0
            try:
                from foundrai.orchestration.cost_calculator import calculate_cost
                cost_usd = calculate_cost(model, prompt_tokens, completion_tokens)
            except ImportError:
                cost_usd = getattr(response, "cost_usd", 0.0)

            prompt_text = json.dumps(messages) if messages else ""
            trace = DecisionTrace(
                task_id=self.task_id,
                sprint_id=self.sprint_id or None,
                agent_role=self.agent_role,
                model=model,
                prompt=prompt_text,
                response=response.content,
                thinking=getattr(response, "thinking", None),
                tool_calls=tool_calls,
                tokens_used=total_tokens,
                cost_usd=cost_usd,
                duration_ms=duration_ms,
            )
            await self.trace_store.record_trace(trace)
        except Exception:
            pass  # Don't break execution if tracing fails

    async def _emit_tool_event(self, tool_name: str, args: dict, result: str) -> None:
        """Emit an event when a tool is used."""
        try:
            await self.event_log.append("agent.tool_used", {
                "agent_role": self.agent_role,
                "task_id": self.task_id,
                "sprint_id": self.sprint_id,
                "tool": tool_name,
                "arguments": {k: str(v)[:200] for k, v in args.items()},
                "result_preview": result[:500],
            })
        except Exception:
            pass

    @staticmethod
    def _tool_to_schema(tool: Any) -> dict:
        """Convert a BaseTool to an LLM-compatible tool schema."""
        if hasattr(tool.input_schema, "model_json_schema"):
            schema = tool.input_schema.model_json_schema()
        else:
            schema = {}
        # Remove title/description clutter from Pydantic schema
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    @staticmethod
    def _extract_tool_artifacts(tool_name: str, args: dict, result: Any) -> list:
        """Extract artifacts from tool results (e.g., files written)."""
        artifacts = []
        if tool_name == "file_manager" and args.get("action") == "write" and result.success:
            artifacts.append({
                "type": "file",
                "path": args.get("path", ""),
                "tool": tool_name,
            })
        return artifacts

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
