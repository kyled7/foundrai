"""Integration tests for retry logic under various failure scenarios."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock

import pytest

from foundrai.agents.context import SprintContext
from foundrai.agents.personas.developer import DeveloperAgent
from foundrai.agents.personas.product_manager import ProductManagerAgent
from foundrai.agents.personas.qa_engineer import QAEngineerAgent
from foundrai.agents.roles import get_role
from foundrai.agents.runtime import RuntimeResult
from foundrai.config import FoundrAIConfig
from foundrai.models.enums import AgentRoleName, SprintStatus, TaskStatus
from foundrai.orchestration.engine import SprintEngine
from foundrai.orchestration.message_bus import MessageBus
from foundrai.orchestration.task_graph import TaskGraph
from foundrai.persistence.artifact_store import ArtifactStore
from foundrai.persistence.event_log import EventLog
from foundrai.persistence.sprint_store import SprintStore

# Test data
SINGLE_TASK_JSON = json.dumps(
    [
        {
            "title": "Build feature",
            "description": "Implement a new feature",
            "acceptance_criteria": ["Feature works", "Tests pass"],
            "dependencies": [],
            "assigned_to": "developer",
            "priority": 1,
        },
    ]
)

QA_PASS_JSON = json.dumps(
    {
        "passed": True,
        "issues": [],
        "suggestions": [],
    }
)


def _make_runtime_mock(response_content: str, response_format: str | None = None) -> AsyncMock:
    """Create a mock runtime that returns a canned response."""
    runtime = AsyncMock()
    parsed = None
    starts_json = response_content.startswith(("[", "{"))
    if response_format == "json" or starts_json:
        try:
            parsed = json.loads(response_content)
        except json.JSONDecodeError:
            pass
    runtime.run = AsyncMock(
        return_value=RuntimeResult(
            output=response_content,
            parsed=parsed,
            artifacts=[],
            tokens_used=100,
            success=True,
        )
    )
    return runtime


@pytest.fixture
def sprint_context(tmp_path):
    """Create a sprint context for testing."""
    return SprintContext(
        project_name="test-project",
        project_path=str(tmp_path),
        sprint_goal="Test retry scenarios",
        sprint_number=1,
    )


@pytest.fixture
async def components(db):
    """Set up all orchestration components."""
    event_log = EventLog(db)
    sprint_store = SprintStore(db)
    artifact_store = ArtifactStore(db)
    message_bus = MessageBus(event_log)
    task_graph = TaskGraph()
    return event_log, sprint_store, artifact_store, message_bus, task_graph


@pytest.mark.asyncio
async def test_retry_on_rate_limit_error(db, tmp_path, sprint_context, components):
    """Test that rate limit errors are automatically retried."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)
    qa_role = get_role(AgentRoleName.QA_ENGINEER)

    pm = ProductManagerAgent(
        role=pm_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(SINGLE_TASK_JSON, "json"),
    )
    qa = QAEngineerAgent(
        role=qa_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(QA_PASS_JSON, "json"),
    )

    # Create dev agent that fails with rate limit twice, then succeeds
    call_count = 0

    async def rate_limit_then_succeed(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise RuntimeError("API rate limit exceeded: 429 too many requests")
        return RuntimeResult(
            output="Feature implemented successfully",
            parsed=None,
            artifacts=[],
            tokens_used=150,
            success=True,
        )

    dev = DeveloperAgent(
        role=dev_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock("Done"),
    )
    dev.runtime.run = AsyncMock(side_effect=rate_limit_then_succeed)

    # Register agents
    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)
    message_bus.register_agent(AgentRoleName.QA_ENGINEER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
        AgentRoleName.QA_ENGINEER.value: qa,
    }

    config = FoundrAIConfig()
    config.sprint.max_task_retries = 3

    engine = SprintEngine(
        config=config,
        agents=agent_map,
        task_graph=task_graph,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
    )

    result = await engine.run_sprint(
        goal="Test rate limit retry",
        project_id="test-project",
    )

    # Should succeed after retries
    assert result["status"] == SprintStatus.COMPLETED
    assert len(result["tasks"]) == 1
    assert result["tasks"][0].status == TaskStatus.DONE
    assert call_count == 3  # Failed twice, succeeded on third


@pytest.mark.asyncio
async def test_retry_on_timeout_error(db, tmp_path, sprint_context, components):
    """Test that timeout errors are automatically retried."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)
    qa_role = get_role(AgentRoleName.QA_ENGINEER)

    pm = ProductManagerAgent(
        role=pm_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(SINGLE_TASK_JSON, "json"),
    )
    qa = QAEngineerAgent(
        role=qa_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(QA_PASS_JSON, "json"),
    )

    # Create dev agent that fails with timeout once, then succeeds
    call_count = 0

    async def timeout_then_succeed(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise TimeoutError("Request timed out after 30 seconds")
        return RuntimeResult(
            output="Feature implemented after timeout",
            parsed=None,
            artifacts=[],
            tokens_used=200,
            success=True,
        )

    dev = DeveloperAgent(
        role=dev_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock("Done"),
    )
    dev.runtime.run = AsyncMock(side_effect=timeout_then_succeed)

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)
    message_bus.register_agent(AgentRoleName.QA_ENGINEER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
        AgentRoleName.QA_ENGINEER.value: qa,
    }

    config = FoundrAIConfig()
    config.sprint.max_task_retries = 3

    engine = SprintEngine(
        config=config,
        agents=agent_map,
        task_graph=task_graph,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
    )

    result = await engine.run_sprint(
        goal="Test timeout retry",
        project_id="test-project",
    )

    # Should succeed after retry
    assert result["status"] == SprintStatus.COMPLETED
    assert len(result["tasks"]) == 1
    assert result["tasks"][0].status == TaskStatus.DONE
    assert call_count == 2  # Failed once, succeeded on second


@pytest.mark.asyncio
async def test_no_retry_on_context_overflow(db, tmp_path, sprint_context, components):
    """Test that context overflow errors are NOT retried."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)

    pm = ProductManagerAgent(
        role=pm_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(SINGLE_TASK_JSON, "json"),
    )

    # Create dev agent that always fails with context overflow
    call_count = 0

    async def context_overflow_error(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise RuntimeError("Context token limit exceeded - maximum 128k tokens allowed")

    dev = DeveloperAgent(
        role=dev_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock("Done"),
    )
    dev.runtime.run = AsyncMock(side_effect=context_overflow_error)

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
    }

    config = FoundrAIConfig()
    config.sprint.max_task_retries = 3

    engine = SprintEngine(
        config=config,
        agents=agent_map,
        task_graph=task_graph,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
    )

    result = await engine.run_sprint(
        goal="Test context overflow no retry",
        project_id="test-project",
    )

    # Should fail without retries (non-retryable error)
    assert result["status"] == SprintStatus.COMPLETED
    assert len(result["tasks"]) == 1
    assert result["tasks"][0].status == TaskStatus.FAILED
    assert call_count == 1  # No retries for non-retryable error


@pytest.mark.asyncio
async def test_no_retry_on_parse_error(db, tmp_path, sprint_context, components):
    """Test that JSON parse errors are NOT retried."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)

    pm = ProductManagerAgent(
        role=pm_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(SINGLE_TASK_JSON, "json"),
    )

    # Create dev agent that always fails with parse error
    call_count = 0

    async def parse_error(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise ValueError("JSON decode error: malformed response")

    dev = DeveloperAgent(
        role=dev_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock("Done"),
    )
    dev.runtime.run = AsyncMock(side_effect=parse_error)

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
    }

    config = FoundrAIConfig()
    config.sprint.max_task_retries = 3

    engine = SprintEngine(
        config=config,
        agents=agent_map,
        task_graph=task_graph,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
    )

    result = await engine.run_sprint(
        goal="Test parse error no retry",
        project_id="test-project",
    )

    # Should fail without retries
    assert result["status"] == SprintStatus.COMPLETED
    assert len(result["tasks"]) == 1
    assert result["tasks"][0].status == TaskStatus.FAILED
    assert call_count == 1  # No retries for parse error


@pytest.mark.asyncio
async def test_max_retries_exhausted(db, tmp_path, sprint_context, components):
    """Test that task fails when max retries is exhausted."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)

    pm = ProductManagerAgent(
        role=pm_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(SINGLE_TASK_JSON, "json"),
    )

    # Create dev agent that always fails with retryable error
    call_count = 0

    async def always_rate_limit(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise RuntimeError("Rate limit exceeded: 429")

    dev = DeveloperAgent(
        role=dev_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock("Done"),
    )
    dev.runtime.run = AsyncMock(side_effect=always_rate_limit)

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
    }

    config = FoundrAIConfig()
    config.sprint.max_task_retries = 2  # Max 2 retries

    engine = SprintEngine(
        config=config,
        agents=agent_map,
        task_graph=task_graph,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
    )

    result = await engine.run_sprint(
        goal="Test max retries exhausted",
        project_id="test-project",
    )

    # Should fail after exhausting retries
    assert result["status"] == SprintStatus.COMPLETED
    assert len(result["tasks"]) == 1
    assert result["tasks"][0].status == TaskStatus.FAILED
    assert call_count == 3  # Initial attempt + 2 retries


@pytest.mark.asyncio
async def test_retry_with_exponential_backoff(db, tmp_path, sprint_context, components):
    """Test that retries use exponential backoff."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)
    qa_role = get_role(AgentRoleName.QA_ENGINEER)

    pm = ProductManagerAgent(
        role=pm_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(SINGLE_TASK_JSON, "json"),
    )
    qa = QAEngineerAgent(
        role=qa_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(QA_PASS_JSON, "json"),
    )

    # Track timing to verify exponential backoff
    call_count = 0
    timestamps = []

    async def rate_limit_with_timing(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        timestamps.append(asyncio.get_event_loop().time())
        if call_count <= 2:
            raise RuntimeError("Rate limit exceeded: 429")
        return RuntimeResult(
            output="Success after backoff",
            parsed=None,
            artifacts=[],
            tokens_used=100,
            success=True,
        )

    dev = DeveloperAgent(
        role=dev_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock("Done"),
    )
    dev.runtime.run = AsyncMock(side_effect=rate_limit_with_timing)

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)
    message_bus.register_agent(AgentRoleName.QA_ENGINEER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
        AgentRoleName.QA_ENGINEER.value: qa,
    }

    config = FoundrAIConfig()
    config.sprint.max_task_retries = 3

    engine = SprintEngine(
        config=config,
        agents=agent_map,
        task_graph=task_graph,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
    )

    result = await engine.run_sprint(
        goal="Test exponential backoff",
        project_id="test-project",
    )

    # Should succeed after retries
    assert result["status"] == SprintStatus.COMPLETED
    assert result["tasks"][0].status == TaskStatus.DONE
    assert call_count == 3

    # Verify exponential backoff (timestamps should show increasing delays)
    # First retry should wait ~1 second, second retry ~2 seconds
    if len(timestamps) >= 3:
        wait1 = timestamps[1] - timestamps[0]
        wait2 = timestamps[2] - timestamps[1]
        # Second wait should be longer than first (exponential backoff)
        assert wait2 > wait1


@pytest.mark.asyncio
async def test_multiple_tasks_with_mixed_retry_scenarios(db, tmp_path, sprint_context, components):
    """Test sprint with multiple tasks having different retry scenarios."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)
    qa_role = get_role(AgentRoleName.QA_ENGINEER)

    # Create multiple tasks
    multi_tasks_json = json.dumps(
        [
            {
                "title": "Task succeeds first try",
                "description": "This will work immediately",
                "acceptance_criteria": ["Works"],
                "dependencies": [],
                "assigned_to": "developer",
                "priority": 1,
            },
            {
                "title": "Task needs retry",
                "description": "This will fail once then succeed",
                "acceptance_criteria": ["Works after retry"],
                "dependencies": [],
                "assigned_to": "developer",
                "priority": 2,
            },
            {
                "title": "Task fails permanently",
                "description": "This will fail with non-retryable error",
                "acceptance_criteria": ["Should fail"],
                "dependencies": [],
                "assigned_to": "developer",
                "priority": 3,
            },
        ]
    )

    pm = ProductManagerAgent(
        role=pm_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(multi_tasks_json, "json"),
    )
    qa = QAEngineerAgent(
        role=qa_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(QA_PASS_JSON, "json"),
    )

    # Track which task is being executed
    task_call_counts = {}

    async def mixed_behavior(*args, **kwargs):
        # Extract task from args (task is first arg in execute_task)
        task = args[0] if args else None
        task_title = task.title if task else "unknown"

        if task_title not in task_call_counts:
            task_call_counts[task_title] = 0
        task_call_counts[task_title] += 1

        if task_title == "Task succeeds first try":
            return RuntimeResult(
                output="Success immediately",
                parsed=None,
                artifacts=[],
                tokens_used=50,
                success=True,
            )
        elif task_title == "Task needs retry":
            if task_call_counts[task_title] == 1:
                raise RuntimeError("Rate limit exceeded: 429")
            return RuntimeResult(
                output="Success after retry",
                parsed=None,
                artifacts=[],
                tokens_used=50,
                success=True,
            )
        elif task_title == "Task fails permanently":
            raise RuntimeError("Context token limit exceeded")

        return RuntimeResult(
            output="Default success",
            parsed=None,
            artifacts=[],
            tokens_used=50,
            success=True,
        )

    dev = DeveloperAgent(
        role=dev_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock("Done"),
    )
    dev.execute_task = AsyncMock(side_effect=mixed_behavior)

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)
    message_bus.register_agent(AgentRoleName.QA_ENGINEER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
        AgentRoleName.QA_ENGINEER.value: qa,
    }

    config = FoundrAIConfig()
    config.sprint.max_task_retries = 3

    engine = SprintEngine(
        config=config,
        agents=agent_map,
        task_graph=task_graph,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
    )

    result = await engine.run_sprint(
        goal="Test mixed retry scenarios",
        project_id="test-project",
    )

    # Sprint completes with mixed results
    assert result["status"] == SprintStatus.COMPLETED
    assert len(result["tasks"]) == 3

    # Verify task outcomes
    tasks_by_title = {t.title: t for t in result["tasks"]}

    # First task should succeed immediately
    assert tasks_by_title["Task succeeds first try"].status == TaskStatus.DONE
    assert task_call_counts["Task succeeds first try"] == 1

    # Second task should succeed after retry
    assert tasks_by_title["Task needs retry"].status == TaskStatus.DONE
    assert task_call_counts["Task needs retry"] == 2

    # Third task should fail without retries (non-retryable error)
    assert tasks_by_title["Task fails permanently"].status == TaskStatus.FAILED
    assert task_call_counts["Task fails permanently"] == 1


@pytest.mark.asyncio
async def test_retry_behavior_at_runtime_level(db, tmp_path, sprint_context, components):
    """Test that AgentRuntime retry logic integrates correctly with sprint execution."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)

    pm = ProductManagerAgent(
        role=pm_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(SINGLE_TASK_JSON, "json"),
    )

    # Test that runtime-level retries work by having dev fail at runtime.run() level
    call_count = 0

    async def runtime_rate_limit_then_succeed(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call: rate limit error (retryable)
            raise RuntimeError("Rate limit exceeded: 429")
        # Second call: success
        return RuntimeResult(
            output="Task completed after runtime retry",
            parsed=None,
            artifacts=[],
            tokens_used=100,
            success=True,
        )

    dev = DeveloperAgent(
        role=dev_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock("Done"),
    )
    # Mock at runtime.run level to test AgentRuntime retry integration
    dev.runtime.run = AsyncMock(side_effect=runtime_rate_limit_then_succeed)

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
    }

    config = FoundrAIConfig()
    config.sprint.max_task_retries = 3

    engine = SprintEngine(
        config=config,
        agents=agent_map,
        task_graph=task_graph,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
    )

    result = await engine.run_sprint(
        goal="Test runtime-level retry integration",
        project_id="test-project",
    )

    # Should complete successfully with runtime retry
    assert result["status"] == SprintStatus.COMPLETED
    assert len(result["tasks"]) == 1
    # Runtime retries happen inside AgentRuntime, so from the task perspective it's one successful call
    # But internally the runtime retried once
    assert call_count >= 2  # At least one retry occurred
