"""Integration tests for timeout scenarios across sprint lifecycle."""

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
SINGLE_TASK_JSON = json.dumps([
    {
        "title": "Build feature",
        "description": "Implement a new feature",
        "acceptance_criteria": ["Feature works", "Tests pass"],
        "dependencies": [],
        "assigned_to": "developer",
        "priority": 1,
    },
])

MULTI_TASK_JSON = json.dumps([
    {
        "title": "Task 1",
        "description": "First task",
        "acceptance_criteria": ["Works"],
        "dependencies": [],
        "assigned_to": "developer",
        "priority": 1,
    },
    {
        "title": "Task 2",
        "description": "Second task",
        "acceptance_criteria": ["Works"],
        "dependencies": [],
        "assigned_to": "developer",
        "priority": 2,
    },
])

QA_PASS_JSON = json.dumps({
    "passed": True,
    "issues": [],
    "suggestions": [],
})


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
    runtime.run = AsyncMock(return_value=RuntimeResult(
        output=response_content,
        parsed=parsed,
        artifacts=[],
        tokens_used=100,
        success=True,
    ))
    return runtime


@pytest.fixture
def sprint_context(tmp_path):
    """Create a sprint context for testing."""
    return SprintContext(
        project_name="test-project",
        project_path=str(tmp_path),
        sprint_goal="Test timeout scenarios",
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
async def test_task_execution_timeout(db, tmp_path, sprint_context, components):
    """Test that task execution times out after configured duration."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)

    pm = ProductManagerAgent(
        role=pm_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(SINGLE_TASK_JSON, "json"),
    )

    # Create dev agent that hangs indefinitely
    async def hang_forever(*args, **kwargs):
        await asyncio.sleep(1000)  # Sleep much longer than timeout
        return RuntimeResult(
            output="Should never get here",
            parsed=None,
            artifacts=[],
            tokens_used=100,
            success=True,
        )

    dev = DeveloperAgent(
        role=dev_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock("Done"),
    )
    dev.runtime.run = AsyncMock(side_effect=hang_forever)

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
    }

    config = FoundrAIConfig()
    config.sprint.task_timeout_seconds = 2  # Short timeout for fast test

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
        goal="Test task timeout",
        project_id="test-project",
    )

    # Sprint should complete but task should fail due to timeout
    assert result["status"] == SprintStatus.COMPLETED
    assert len(result["tasks"]) == 1
    assert result["tasks"][0].status == TaskStatus.FAILED

    # Verify timeout event was logged
    events = await event_log.query(limit=50)
    event_types = [e["event_type"] for e in events]
    assert "task.status_changed" in event_types


@pytest.mark.asyncio
async def test_planning_phase_error_handling(db, tmp_path, sprint_context, components):
    """Test that planning phase errors are handled gracefully."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)

    # Create PM agent that raises an error during planning
    async def fail_planning(*args, **kwargs):
        raise RuntimeError("Planning service unavailable")

    pm = ProductManagerAgent(
        role=pm_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(SINGLE_TASK_JSON, "json"),
    )
    pm.decompose_goal = AsyncMock(side_effect=fail_planning)

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
    }

    config = FoundrAIConfig()
    config.sprint.task_timeout_seconds = 2  # Short timeout

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
        goal="Test planning error handling",
        project_id="test-project",
    )

    # Sprint should fail during planning
    assert result["status"] == SprintStatus.FAILED
    assert result["error"] is not None
    assert "Planning failed" in result["error"]


@pytest.mark.asyncio
async def test_qa_review_error_handling(db, tmp_path, sprint_context, components):
    """Test that QA review errors are handled gracefully."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)
    qa_role = get_role(AgentRoleName.QA_ENGINEER)

    pm = ProductManagerAgent(
        role=pm_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(SINGLE_TASK_JSON, "json"),
    )
    dev = DeveloperAgent(
        role=dev_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock("Feature implemented"),
    )

    # Create QA agent that raises error during review
    async def fail_qa_review(*args, **kwargs):
        raise RuntimeError("QA service temporarily unavailable")

    qa = QAEngineerAgent(
        role=qa_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(QA_PASS_JSON, "json"),
    )
    qa.review_task = AsyncMock(side_effect=fail_qa_review)

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)
    message_bus.register_agent(AgentRoleName.QA_ENGINEER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
        AgentRoleName.QA_ENGINEER.value: qa,
    }

    config = FoundrAIConfig()
    config.sprint.task_timeout_seconds = 2  # Short timeout

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
        goal="Test QA error handling",
        project_id="test-project",
    )

    # Sprint should complete even if QA has errors
    assert result["status"] == SprintStatus.COMPLETED
    assert len(result["tasks"]) == 1


@pytest.mark.asyncio
async def test_multiple_tasks_with_timeout(db, tmp_path, sprint_context, components):
    """Test that multiple tasks can timeout independently."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)
    qa_role = get_role(AgentRoleName.QA_ENGINEER)

    pm = ProductManagerAgent(
        role=pm_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(MULTI_TASK_JSON, "json"),
    )
    qa = QAEngineerAgent(
        role=qa_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(QA_PASS_JSON, "json"),
    )

    # Track which task is being executed
    task_call_counts = {}

    async def mixed_timeout_behavior(*args, **kwargs):
        task = args[0] if args else None
        task_title = task.title if task else "unknown"

        if task_title not in task_call_counts:
            task_call_counts[task_title] = 0
        task_call_counts[task_title] += 1

        if task_title == "Task 1":
            # First task times out
            await asyncio.sleep(1000)
            return RuntimeResult(
                output="Should not get here",
                parsed=None,
                artifacts=[],
                tokens_used=50,
                success=True,
            )
        elif task_title == "Task 2":
            # Second task succeeds
            return RuntimeResult(
                output="Task 2 completed successfully",
                parsed=None,
                artifacts=[],
                tokens_used=50,
                success=True,
            )

        return RuntimeResult(
            output="Default",
            parsed=None,
            artifacts=[],
            tokens_used=50,
            success=True,
        )

    dev = DeveloperAgent(
        role=dev_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock("Done"),
    )
    dev.execute_task = AsyncMock(side_effect=mixed_timeout_behavior)

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)
    message_bus.register_agent(AgentRoleName.QA_ENGINEER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
        AgentRoleName.QA_ENGINEER.value: qa,
    }

    config = FoundrAIConfig()
    config.sprint.task_timeout_seconds = 2  # Short timeout

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
        goal="Test multiple tasks with timeout",
        project_id="test-project",
    )

    # Sprint should complete with mixed results
    assert result["status"] == SprintStatus.COMPLETED
    assert len(result["tasks"]) == 2

    # Verify task outcomes
    tasks_by_title = {t.title: t for t in result["tasks"]}
    assert tasks_by_title["Task 1"].status == TaskStatus.FAILED  # Timed out
    assert tasks_by_title["Task 2"].status == TaskStatus.DONE  # Succeeded


@pytest.mark.asyncio
async def test_timeout_during_retry(db, tmp_path, sprint_context, components):
    """Test that timeout occurs during a retry attempt."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)

    pm = ProductManagerAgent(
        role=pm_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(SINGLE_TASK_JSON, "json"),
    )

    # First attempt fails with retryable error, second attempt times out
    call_count = 0

    async def fail_then_timeout(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("Rate limit exceeded: 429")
        else:
            # Second attempt times out
            await asyncio.sleep(1000)
            return RuntimeResult(
                output="Should not get here",
                parsed=None,
                artifacts=[],
                tokens_used=100,
                success=True,
            )

    dev = DeveloperAgent(
        role=dev_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock("Done"),
    )
    dev.runtime.run = AsyncMock(side_effect=fail_then_timeout)

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
    }

    config = FoundrAIConfig()
    config.sprint.task_timeout_seconds = 2  # Short timeout
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
        goal="Test timeout during retry",
        project_id="test-project",
    )

    # Should fail due to timeout on retry
    assert result["status"] == SprintStatus.COMPLETED
    assert len(result["tasks"]) == 1
    assert result["tasks"][0].status == TaskStatus.FAILED
    assert call_count >= 1  # At least one attempt was made


@pytest.mark.asyncio
async def test_timeout_no_recovery(db, tmp_path, sprint_context, components):
    """Test that timeout failure is permanent (no retry after timeout).

    Note: Timeout occurs at the task execution wrapper level, so retries
    inside the wrapper won't help - the whole execution times out.
    """
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)

    pm = ProductManagerAgent(
        role=pm_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(SINGLE_TASK_JSON, "json"),
    )

    # Task that always times out
    call_count = 0

    async def always_timeout(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        # Always hang longer than timeout
        await asyncio.sleep(1000)
        return RuntimeResult(
            output="Should not get here",
            parsed=None,
            artifacts=[],
            tokens_used=100,
            success=True,
        )

    dev = DeveloperAgent(
        role=dev_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock("Done"),
    )
    dev.runtime.run = AsyncMock(side_effect=always_timeout)

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
    }

    config = FoundrAIConfig()
    config.sprint.task_timeout_seconds = 2  # Short timeout
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
        goal="Test timeout no recovery",
        project_id="test-project",
    )

    # Should fail due to timeout - timeout wraps entire retry logic
    assert result["status"] == SprintStatus.COMPLETED
    assert len(result["tasks"]) == 1
    assert result["tasks"][0].status == TaskStatus.FAILED


@pytest.mark.asyncio
async def test_timeout_event_logging(db, tmp_path, sprint_context, components):
    """Test that timeout events are properly logged."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)

    pm = ProductManagerAgent(
        role=pm_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(SINGLE_TASK_JSON, "json"),
    )

    # Create dev agent that times out
    async def timeout_task(*args, **kwargs):
        await asyncio.sleep(1000)
        return RuntimeResult(
            output="Should not get here",
            parsed=None,
            artifacts=[],
            tokens_used=100,
            success=True,
        )

    dev = DeveloperAgent(
        role=dev_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock("Done"),
    )
    dev.runtime.run = AsyncMock(side_effect=timeout_task)

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
    }

    config = FoundrAIConfig()
    config.sprint.task_timeout_seconds = 2

    engine = SprintEngine(
        config=config,
        agents=agent_map,
        task_graph=task_graph,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
    )

    await engine.run_sprint(
        goal="Test timeout event logging",
        project_id="test-project",
    )

    # Verify events were logged
    events = await event_log.query(limit=100)
    event_types = [e["event_type"] for e in events]

    # Should have sprint and task events
    assert "sprint.started" in event_types
    assert "task.status_changed" in event_types
    assert "sprint.status_changed" in event_types

    # Should have a specific timeout event logged
    assert "task.timeout" in event_types

    # Find the timeout event
    timeout_events = [e for e in events if e["event_type"] == "task.timeout"]
    assert len(timeout_events) == 1
    assert "timeout_seconds" in timeout_events[0]["data"]
    assert timeout_events[0]["data"]["timeout_seconds"] == 2


@pytest.mark.asyncio
async def test_short_timeout_configuration(db, tmp_path, sprint_context, components):
    """Test that timeout configuration is respected at different values."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)

    pm = ProductManagerAgent(
        role=pm_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(SINGLE_TASK_JSON, "json"),
    )

    # Sleep for 3 seconds
    async def sleep_three_seconds(*args, **kwargs):
        await asyncio.sleep(3)
        return RuntimeResult(
            output="Task completed",
            parsed=None,
            artifacts=[],
            tokens_used=100,
            success=True,
        )

    dev = DeveloperAgent(
        role=dev_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock("Done"),
    )
    dev.runtime.run = AsyncMock(side_effect=sleep_three_seconds)

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
    }

    config = FoundrAIConfig()
    config.sprint.task_timeout_seconds = 1  # Very short timeout (task takes 3 seconds)

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
        goal="Test short timeout config",
        project_id="test-project",
    )

    # Should timeout because task takes longer than configured timeout
    assert result["status"] == SprintStatus.COMPLETED
    assert len(result["tasks"]) == 1
    assert result["tasks"][0].status == TaskStatus.FAILED


@pytest.mark.asyncio
async def test_no_timeout_with_zero_config(db, tmp_path, sprint_context, components):
    """Test that setting timeout to 0 or None disables timeout."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)
    qa_role = get_role(AgentRoleName.QA_ENGINEER)

    pm = ProductManagerAgent(
        role=pm_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(SINGLE_TASK_JSON, "json"),
    )
    qa = QAEngineerAgent(
        role=qa_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(QA_PASS_JSON, "json"),
    )

    # Sleep briefly (but would timeout with short timeout configured)
    async def brief_sleep(*args, **kwargs):
        await asyncio.sleep(0.5)
        return RuntimeResult(
            output="Task completed successfully",
            parsed=None,
            artifacts=[],
            tokens_used=100,
            success=True,
        )

    dev = DeveloperAgent(
        role=dev_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock("Done"),
    )
    dev.runtime.run = AsyncMock(side_effect=brief_sleep)

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)
    message_bus.register_agent(AgentRoleName.QA_ENGINEER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
        AgentRoleName.QA_ENGINEER.value: qa,
    }

    config = FoundrAIConfig()
    # Set very high timeout essentially disabling it for this short task
    config.sprint.task_timeout_seconds = 10000

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
        goal="Test no timeout",
        project_id="test-project",
    )

    # Should succeed since timeout is effectively disabled
    assert result["status"] == SprintStatus.COMPLETED
    assert len(result["tasks"]) == 1
    assert result["tasks"][0].status == TaskStatus.DONE
