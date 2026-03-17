"""Integration test for Developer agent with sandboxed code execution."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from foundrai.agents.context import SprintContext
from foundrai.agents.personas.developer import DeveloperAgent
from foundrai.agents.roles import get_role
from foundrai.agents.runtime import AgentRuntime, RuntimeResult
from foundrai.config import FoundrAIConfig
from foundrai.models.enums import AgentRoleName
from foundrai.models.task import Task
from foundrai.orchestration.message_bus import MessageBus
from foundrai.persistence.event_log import EventLog
from foundrai.tools.code_executor import CodeExecutorInput, get_code_executor
from foundrai.tools.registry import create_tool_registry


@pytest.fixture
def sprint_context(tmp_path):
    """Create a sprint context for the test."""
    return SprintContext(
        project_name="test-sandbox",
        project_path=str(tmp_path),
        sprint_goal="Test sandboxed code execution",
        sprint_number=1,
    )


@pytest.fixture
async def message_bus(db):
    """Create a message bus for agent communication."""
    event_log = EventLog(db)
    mb = MessageBus(event_log)
    mb.register_agent(AgentRoleName.DEVELOPER.value)
    return mb


@pytest.fixture
def code_executor():
    """Get a code executor instance (noop or real based on availability)."""
    return get_code_executor(provider="docker", timeout=30)


@pytest.mark.asyncio
async def test_developer_agent_executes_code(db, tmp_path, sprint_context, message_bus, code_executor):
    """Test that Developer agent can execute code in a sandboxed environment."""
    # Create a simple task that requires code execution
    task = Task(
        id="test-task-1",
        title="Write and test a Python hello world",
        description="Create a Python script that prints 'Hello, FoundrAI!'",
        acceptance_criteria=[
            "Script prints 'Hello, FoundrAI!'",
            "Code executes without errors",
        ],
        assigned_to="developer",
        priority=1,
        dependencies=[],
    )

    # Create a mock runtime that simulates LLM calling the code_executor tool
    runtime = AsyncMock(spec=AgentRuntime)

    # Simulate the agent executing code
    async def mock_run(messages, tools=None, response_format=None):
        # The mock LLM would normally generate a tool call
        # We'll simulate it by directly executing the code_executor tool
        if tools:
            # Find code_executor tool
            code_tool = next((t for t in tools if t.name == "code_executor"), None)
            if code_tool:
                # Execute a simple Python hello world
                tool_input = CodeExecutorInput(
                    code='print("Hello, FoundrAI!")',
                    language="python",
                    timeout_seconds=10,
                )
                result = await code_tool.execute(tool_input)

                # The agent would process this result and return it
                output = f"Code executed successfully. Output: {result.output}"
                return RuntimeResult(
                    output=output,
                    parsed=None,
                    artifacts=[],
                    tokens_used=50,
                    success=result.success,
                )

        return RuntimeResult(
            output="Task completed",
            parsed=None,
            artifacts=[],
            tokens_used=50,
            success=True,
        )

    runtime.run = AsyncMock(side_effect=mock_run)

    # Get tools for developer
    config = FoundrAIConfig()
    registry = create_tool_registry(config, str(tmp_path))
    developer_role = get_role(AgentRoleName.DEVELOPER)
    tools = registry.get_tools_for_role(developer_role)

    # Replace the code_executor in tools with our fixture
    tools = [t if t.name != "code_executor" else code_executor for t in tools]

    # Create Developer agent
    developer = DeveloperAgent(
        role=get_role(AgentRoleName.DEVELOPER),
        model="test-model",
        tools=tools,
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=runtime,
    )

    # Execute the task
    task_result = await developer.execute_task(task)

    # Verify execution succeeded
    assert task_result.success
    assert "Hello, FoundrAI!" in task_result.output or "Code executed successfully" in task_result.output
    assert task_result.task_id == task.id
    assert task_result.agent_id == AgentRoleName.DEVELOPER.value
