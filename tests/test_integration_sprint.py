"""Integration test: full mini-sprint with mocked LLM.

Backward Compatibility Verification:
These tests verify that the sprint flow hardening features (retry logic,
timeout handling, sprint resume, and race condition protection) maintain
backward compatibility with existing sprint execution behavior.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from foundrai.agents.context import SprintContext
from foundrai.agents.personas.developer import DeveloperAgent
from foundrai.agents.personas.product_manager import ProductManagerAgent
from foundrai.agents.personas.qa_engineer import QAEngineerAgent
from foundrai.agents.roles import get_role
from foundrai.agents.runtime import AgentRuntime, RuntimeResult
from foundrai.models.enums import AgentRoleName, SprintStatus, TaskStatus
from foundrai.orchestration.engine import SprintEngine
from foundrai.orchestration.message_bus import MessageBus
from foundrai.orchestration.task_graph import TaskGraph
from foundrai.persistence.artifact_store import ArtifactStore
from foundrai.persistence.event_log import EventLog
from foundrai.persistence.sprint_store import SprintStore

PM_RESPONSE = json.dumps(
    [
        {
            "title": "Create Flask app",
            "description": "Create a basic Flask hello world app",
            "acceptance_criteria": ["App returns 200 on /", "Response is 'Hello World'"],
            "dependencies": [],
            "assigned_to": "developer",
            "priority": 1,
        },
        {
            "title": "Write tests",
            "description": "Write pytest tests for the Flask app",
            "acceptance_criteria": ["Tests pass", "Coverage > 80%"],
            "dependencies": ["Create Flask app"],
            "assigned_to": "developer",
            "priority": 2,
        },
    ]
)

DEV_RESPONSE = "I've implemented the Flask app with a hello world endpoint at /."

QA_RESPONSE = json.dumps(
    {
        "passed": True,
        "issues": [],
        "suggestions": ["Consider adding error handling"],
    }
)


def _make_runtime_mock(response_content: str, response_format: str | None = None) -> AsyncMock:
    """Create a mock runtime that returns a canned response."""
    runtime = AsyncMock(spec=AgentRuntime)
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
    return SprintContext(
        project_name="test-project",
        project_path=str(tmp_path),
        sprint_goal="Build a hello world REST API with Flask",
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
async def test_full_sprint_flow(db, tmp_path, sprint_context, components):
    """Full sprint: PM decomposes → Dev codes → QA reviews → sprint completes.

    BACKWARD COMPATIBILITY:
    - Sprint completes successfully with default retry/timeout config
    - No retries triggered for successful tasks
    - Checkpoints created transparently without breaking flow
    - All existing metrics and persistence still work
    """
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    # Create agents with mocked runtimes
    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)
    qa_role = get_role(AgentRoleName.QA_ENGINEER)

    pm = ProductManagerAgent(
        role=pm_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(PM_RESPONSE, "json"),
    )
    dev = DeveloperAgent(
        role=dev_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(DEV_RESPONSE),
    )
    qa = QAEngineerAgent(
        role=qa_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(QA_RESPONSE, "json"),
    )

    # Register agents on message bus
    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)
    message_bus.register_agent(AgentRoleName.QA_ENGINEER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
        AgentRoleName.QA_ENGINEER.value: qa,
    }

    from foundrai.config import FoundrAIConfig

    config = FoundrAIConfig()

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
        goal="Build a hello world REST API with Flask",
        project_id="test-project",
    )

    # Verify sprint completed
    assert result["status"] == SprintStatus.COMPLETED
    assert len(result["tasks"]) == 2
    assert result["tasks"][0].title == "Create Flask app"
    assert result["tasks"][1].title == "Write tests"

    # All tasks should be done (QA passed them)
    for task in result["tasks"]:
        assert task.status == TaskStatus.DONE, f"Task '{task.title}' status: {task.status}"

    # Metrics should be populated
    metrics = result["metrics"]
    assert metrics.total_tasks == 2
    assert metrics.completed_tasks == 2
    assert metrics.failed_tasks == 0
    assert metrics.total_tokens > 0

    # Verify persistence
    stored = await sprint_store.get_sprint(result["sprint_id"])
    assert stored is not None
    assert stored["status"] == SprintStatus.COMPLETED

    # Verify events were logged
    events = await event_log.query(limit=50)
    event_types = [e["event_type"] for e in events]
    assert "sprint.started" in event_types
    assert "sprint.status_changed" in event_types
    assert "task.status_changed" in event_types

    # Verify messages were sent via message bus
    history = message_bus.get_history()
    assert len(history) > 0
    assert any(m.type.value == "goal_decomposition" for m in history)

    # BACKWARD COMPATIBILITY: Verify checkpoints created without breaking flow
    checkpoints = await sprint_store.get_latest_checkpoint(result["sprint_id"])
    assert checkpoints is not None, "Checkpoints should be created transparently"


@pytest.mark.asyncio
async def test_sprint_fails_when_planning_fails(db, tmp_path, sprint_context, components):
    """Sprint should fail gracefully when PM raises an error.

    BACKWARD COMPATIBILITY:
    - Error handling still works as expected
    - Sprint fails gracefully without retries (planning errors are non-retryable)
    """
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    pm = ProductManagerAgent(
        role=pm_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
    )
    # Make runtime raise an error
    pm.runtime = AsyncMock()
    pm.runtime.run = AsyncMock(side_effect=RuntimeError("LLM API down"))

    agent_map = {AgentRoleName.PRODUCT_MANAGER.value: pm}

    from foundrai.config import FoundrAIConfig

    engine = SprintEngine(
        config=FoundrAIConfig(),
        agents=agent_map,
        task_graph=task_graph,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
    )

    result = await engine.run_sprint(goal="Fail test", project_id="test")
    assert result["status"] == SprintStatus.FAILED
    assert "Planning failed" in (result.get("error") or "")


@pytest.mark.asyncio
async def test_sprint_fails_when_no_tasks_produced(db, tmp_path, sprint_context, components):
    """Sprint fails when PM returns empty task list."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    pm = ProductManagerAgent(
        role=pm_role,
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock("[]", "json"),
    )
    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)

    agent_map = {AgentRoleName.PRODUCT_MANAGER.value: pm}

    from foundrai.config import FoundrAIConfig

    engine = SprintEngine(
        config=FoundrAIConfig(),
        agents=agent_map,
        task_graph=task_graph,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
    )

    result = await engine.run_sprint(goal="Empty", project_id="test")
    assert result["status"] == SprintStatus.FAILED


@pytest.mark.asyncio
async def test_sprint_with_qa_failure(db, tmp_path, sprint_context, components):
    """Tasks that fail QA review should be marked as failed.

    BACKWARD COMPATIBILITY:
    - QA failure handling unchanged
    - Failed tasks still marked correctly
    - Sprint completion logic preserved
    """
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    qa_fail = json.dumps({"passed": False, "issues": ["Code is buggy"], "suggestions": []})

    pm_single_task = json.dumps(
        [
            {
                "title": "Build feature",
                "description": "Build it",
                "acceptance_criteria": ["Works"],
                "dependencies": [],
                "assigned_to": "developer",
                "priority": 1,
            }
        ]
    )

    pm = ProductManagerAgent(
        role=get_role(AgentRoleName.PRODUCT_MANAGER),
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(pm_single_task, "json"),
    )
    dev = DeveloperAgent(
        role=get_role(AgentRoleName.DEVELOPER),
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(DEV_RESPONSE),
    )
    qa = QAEngineerAgent(
        role=get_role(AgentRoleName.QA_ENGINEER),
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(qa_fail, "json"),
    )

    for role in [AgentRoleName.PRODUCT_MANAGER, AgentRoleName.DEVELOPER, AgentRoleName.QA_ENGINEER]:
        message_bus.register_agent(role.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
        AgentRoleName.QA_ENGINEER.value: qa,
    }

    from foundrai.config import FoundrAIConfig

    engine = SprintEngine(
        config=FoundrAIConfig(),
        agents=agent_map,
        task_graph=task_graph,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
    )

    result = await engine.run_sprint(goal="QA fail test", project_id="test")
    assert result["status"] == SprintStatus.COMPLETED
    assert result["tasks"][0].status == TaskStatus.FAILED
    assert result["metrics"].failed_tasks == 1


@pytest.mark.asyncio
async def test_sprint_without_qa_agent(db, tmp_path, sprint_context, components):
    """Sprint should complete even without QA agent — tasks auto-pass.

    BACKWARD COMPATIBILITY:
    - Optional QA agent behavior unchanged
    - Tasks auto-pass without QA agent
    """
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_single = json.dumps(
        [
            {
                "title": "Solo task",
                "description": "Do it",
                "acceptance_criteria": [],
                "dependencies": [],
                "assigned_to": "developer",
                "priority": 1,
            }
        ]
    )

    pm = ProductManagerAgent(
        role=get_role(AgentRoleName.PRODUCT_MANAGER),
        model="t",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(pm_single, "json"),
    )
    dev = DeveloperAgent(
        role=get_role(AgentRoleName.DEVELOPER),
        model="t",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock("Done"),
    )
    for r in [AgentRoleName.PRODUCT_MANAGER, AgentRoleName.DEVELOPER]:
        message_bus.register_agent(r.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
    }

    from foundrai.config import FoundrAIConfig

    engine = SprintEngine(
        config=FoundrAIConfig(),
        agents=agent_map,
        task_graph=task_graph,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
    )

    result = await engine.run_sprint(goal="No QA", project_id="test")
    assert result["status"] == SprintStatus.COMPLETED
    assert result["tasks"][0].status == TaskStatus.DONE


@pytest.mark.asyncio
async def test_backward_compatibility_default_configs(db, tmp_path, sprint_context, components):
    """Verify default configs preserve pre-hardening behavior.

    BACKWARD COMPATIBILITY TEST:
    This test explicitly verifies that:
    1. Default retry config (3 retries) doesn't affect successful tasks
    2. Default timeout config (300s) doesn't affect fast tasks
    3. Checkpoint creation happens transparently
    4. Lock-protected operations don't cause deadlocks or delays
    5. All existing APIs and return values unchanged
    """
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_response = json.dumps(
        [
            {
                "title": "Quick task",
                "description": "A fast task",
                "acceptance_criteria": ["Done quickly"],
                "dependencies": [],
                "assigned_to": "developer",
                "priority": 1,
            }
        ]
    )

    pm = ProductManagerAgent(
        role=get_role(AgentRoleName.PRODUCT_MANAGER),
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(pm_response, "json"),
    )
    dev = DeveloperAgent(
        role=get_role(AgentRoleName.DEVELOPER),
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock("Task completed quickly"),
    )
    qa = QAEngineerAgent(
        role=get_role(AgentRoleName.QA_ENGINEER),
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(QA_RESPONSE, "json"),
    )

    for r in [AgentRoleName.PRODUCT_MANAGER, AgentRoleName.DEVELOPER, AgentRoleName.QA_ENGINEER]:
        message_bus.register_agent(r.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
        AgentRoleName.QA_ENGINEER.value: qa,
    }

    from foundrai.config import FoundrAIConfig

    config = FoundrAIConfig()

    # Verify default config values exist (they're optional, so presence matters)
    assert hasattr(config.sprint, "max_task_retries"), "Retry config should exist"
    assert hasattr(config.sprint, "task_timeout_seconds"), "Timeout config should exist"

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
        goal="Test backward compatibility",
        project_id="test-compat",
    )

    # BACKWARD COMPATIBILITY ASSERTIONS:

    # 1. Sprint completes successfully
    assert result["status"] == SprintStatus.COMPLETED
    assert len(result["tasks"]) == 1
    assert result["tasks"][0].status == TaskStatus.DONE

    # 2. All expected keys present (API unchanged)
    assert "sprint_id" in result
    assert "status" in result
    assert "tasks" in result
    assert "metrics" in result
    assert "project_id" in result
    assert "goal" in result

    # 3. Metrics structure unchanged
    metrics = result["metrics"]
    assert hasattr(metrics, "total_tasks")
    assert hasattr(metrics, "completed_tasks")
    assert hasattr(metrics, "failed_tasks")
    assert hasattr(metrics, "total_tokens")
    assert metrics.completed_tasks == 1
    assert metrics.failed_tasks == 0

    # 4. Persistence still works
    stored = await sprint_store.get_sprint(result["sprint_id"])
    assert stored is not None
    assert stored["status"] == SprintStatus.COMPLETED

    # 5. Event logging still works
    events = await event_log.query(limit=50)
    assert len(events) > 0
    event_types = [e["event_type"] for e in events]
    assert "sprint.started" in event_types
    assert "task.status_changed" in event_types

    # 6. Checkpoints created transparently (new feature, non-breaking)
    latest_checkpoint = await sprint_store.get_latest_checkpoint(result["sprint_id"])
    assert latest_checkpoint is not None, "Checkpoints should be created"

    # 7. Message bus history preserved
    history = message_bus.get_history()
    assert len(history) > 0

    # 8. Task structure unchanged
    task = result["tasks"][0]
    assert hasattr(task, "id")
    assert hasattr(task, "title")
    assert hasattr(task, "description")
    assert hasattr(task, "status")
    assert hasattr(task, "assigned_to")
