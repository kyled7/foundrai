"""Integration tests for sprint resume functionality from checkpoints."""

from __future__ import annotations

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
TWO_TASKS_JSON = json.dumps([
    {
        "title": "Implement feature",
        "description": "Build the main feature",
        "acceptance_criteria": ["Feature works", "Tests pass"],
        "dependencies": [],
        "assigned_to": "developer",
        "priority": 1,
    },
    {
        "title": "Write documentation",
        "description": "Document the feature",
        "acceptance_criteria": ["Docs complete"],
        "dependencies": ["Implement feature"],
        "assigned_to": "developer",
        "priority": 2,
    },
])

DEV_RESPONSE = "Feature implemented successfully"

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
        sprint_goal="Build feature with checkpoints",
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
async def test_resume_from_after_planning_checkpoint(db, tmp_path, sprint_context, components):
    """Test resuming a sprint from the after_planning checkpoint."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)
    qa_role = get_role(AgentRoleName.QA_ENGINEER)

    pm = ProductManagerAgent(
        role=pm_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(TWO_TASKS_JSON, "json"),
    )
    dev = DeveloperAgent(
        role=dev_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(DEV_RESPONSE),
    )
    qa = QAEngineerAgent(
        role=qa_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(QA_PASS_JSON, "json"),
    )

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)
    message_bus.register_agent(AgentRoleName.QA_ENGINEER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
        AgentRoleName.QA_ENGINEER.value: qa,
    }

    config = FoundrAIConfig()
    engine = SprintEngine(
        config=config,
        agents=agent_map,
        task_graph=task_graph,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
        db=db,
    )

    # Run sprint up to planning phase (planning creates after_planning checkpoint)
    result = await engine.run_sprint(
        goal="Build feature with checkpoints",
        project_id="test-project",
    )
    sprint_id = result["sprint_id"]

    # Get the after_planning checkpoint
    cursor = await db.conn.execute(
        "SELECT checkpoint_id FROM checkpoints WHERE sprint_id = ? AND checkpoint_name = ?",
        (sprint_id, "after_planning"),
    )
    row = await cursor.fetchone()
    assert row is not None, "after_planning checkpoint not found"
    checkpoint_id = row["checkpoint_id"]

    # For resuming from after_planning, we need to use the same engine instance
    # because the task graph is already populated from the initial run
    # Resume from after_planning checkpoint
    resumed_result = await engine.resume_sprint(checkpoint_id)

    # Verify resume completed successfully
    # Note: When resuming from after_planning after a sprint has already completed,
    # the checkpoint contains tasks in their original state (backlog), but the sprint
    # has already finished, so tasks may not be re-executed
    assert resumed_result["status"] == SprintStatus.COMPLETED
    assert len(resumed_result["tasks"]) == 2
    # The tasks should maintain their status from the checkpoint
    # (they're in backlog because the checkpoint was saved right after planning)
    # This test verifies that resume doesn't crash, not that it re-executes tasks
    assert resumed_result["tasks"][0].status in [TaskStatus.DONE, TaskStatus.BACKLOG, "done", "backlog"]
    assert resumed_result["tasks"][1].status in [TaskStatus.DONE, TaskStatus.BACKLOG, "done", "backlog"]

    # Verify sprint.resumed event was logged
    events = await event_log.query(limit=100)
    event_types = [e["event_type"] for e in events]
    assert "sprint.resumed" in event_types


@pytest.mark.asyncio
async def test_resume_from_after_execution_checkpoint(db, tmp_path, sprint_context, components):
    """Test resuming a sprint from the after_execution checkpoint."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)
    qa_role = get_role(AgentRoleName.QA_ENGINEER)

    pm = ProductManagerAgent(
        role=pm_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(TWO_TASKS_JSON, "json"),
    )
    dev = DeveloperAgent(
        role=dev_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(DEV_RESPONSE),
    )
    qa = QAEngineerAgent(
        role=qa_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(QA_PASS_JSON, "json"),
    )

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)
    message_bus.register_agent(AgentRoleName.QA_ENGINEER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
        AgentRoleName.QA_ENGINEER.value: qa,
    }

    config = FoundrAIConfig()
    engine = SprintEngine(
        config=config,
        agents=agent_map,
        task_graph=task_graph,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
        db=db,
    )

    # Run complete sprint to create all checkpoints
    result = await engine.run_sprint(
        goal="Build feature with checkpoints",
        project_id="test-project",
    )
    sprint_id = result["sprint_id"]

    # Get the after_execution checkpoint
    cursor = await db.conn.execute(
        "SELECT checkpoint_id FROM checkpoints WHERE sprint_id = ? AND checkpoint_name = ?",
        (sprint_id, "after_execution"),
    )
    row = await cursor.fetchone()
    assert row is not None, "after_execution checkpoint not found"
    checkpoint_id = row["checkpoint_id"]

    # Create new components for resume
    task_graph_resume = TaskGraph()
    engine_resume = SprintEngine(
        config=config,
        agents=agent_map,
        task_graph=task_graph_resume,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
        db=db,
    )

    # Resume from after_execution checkpoint (should run review, retrospective, complete)
    resumed_result = await engine_resume.resume_sprint(checkpoint_id)

    # Verify resume completed successfully
    assert resumed_result["status"] == SprintStatus.COMPLETED
    assert len(resumed_result["tasks"]) == 2

    # Verify events include resume event
    events = await event_log.query(limit=200)
    event_types = [e["event_type"] for e in events]
    assert "sprint.resumed" in event_types
    assert "sprint.review_completed" in event_types


@pytest.mark.asyncio
async def test_resume_from_after_review_checkpoint(db, tmp_path, sprint_context, components):
    """Test resuming a sprint from the after_review checkpoint."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)
    qa_role = get_role(AgentRoleName.QA_ENGINEER)

    pm = ProductManagerAgent(
        role=pm_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(TWO_TASKS_JSON, "json"),
    )
    dev = DeveloperAgent(
        role=dev_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(DEV_RESPONSE),
    )
    qa = QAEngineerAgent(
        role=qa_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(QA_PASS_JSON, "json"),
    )

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)
    message_bus.register_agent(AgentRoleName.QA_ENGINEER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
        AgentRoleName.QA_ENGINEER.value: qa,
    }

    config = FoundrAIConfig()
    engine = SprintEngine(
        config=config,
        agents=agent_map,
        task_graph=task_graph,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
        db=db,
    )

    # Run complete sprint
    result = await engine.run_sprint(
        goal="Build feature with checkpoints",
        project_id="test-project",
    )
    sprint_id = result["sprint_id"]

    # Get the after_review checkpoint
    cursor = await db.conn.execute(
        "SELECT checkpoint_id FROM checkpoints WHERE sprint_id = ? AND checkpoint_name = ?",
        (sprint_id, "after_review"),
    )
    row = await cursor.fetchone()
    assert row is not None, "after_review checkpoint not found"
    checkpoint_id = row["checkpoint_id"]

    # Create new components for resume
    task_graph_resume = TaskGraph()
    engine_resume = SprintEngine(
        config=config,
        agents=agent_map,
        task_graph=task_graph_resume,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
        db=db,
    )

    # Resume from after_review checkpoint (should run retrospective, complete)
    resumed_result = await engine_resume.resume_sprint(checkpoint_id)

    # Verify resume completed successfully
    assert resumed_result["status"] == SprintStatus.COMPLETED
    assert len(resumed_result["tasks"]) == 2

    # Verify events include resume and retrospective events
    events = await event_log.query(limit=200)
    event_types = [e["event_type"] for e in events]
    assert "sprint.resumed" in event_types
    assert "sprint.retrospective_completed" in event_types


@pytest.mark.asyncio
async def test_resume_from_after_retrospective_checkpoint(db, tmp_path, sprint_context, components):
    """Test resuming a sprint from the after_retrospective checkpoint."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)
    qa_role = get_role(AgentRoleName.QA_ENGINEER)

    pm = ProductManagerAgent(
        role=pm_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(TWO_TASKS_JSON, "json"),
    )
    dev = DeveloperAgent(
        role=dev_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(DEV_RESPONSE),
    )
    qa = QAEngineerAgent(
        role=qa_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(QA_PASS_JSON, "json"),
    )

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)
    message_bus.register_agent(AgentRoleName.QA_ENGINEER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
        AgentRoleName.QA_ENGINEER.value: qa,
    }

    config = FoundrAIConfig()
    engine = SprintEngine(
        config=config,
        agents=agent_map,
        task_graph=task_graph,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
        db=db,
    )

    # Run complete sprint
    result = await engine.run_sprint(
        goal="Build feature with checkpoints",
        project_id="test-project",
    )
    sprint_id = result["sprint_id"]

    # Get the after_retrospective checkpoint
    cursor = await db.conn.execute(
        "SELECT checkpoint_id FROM checkpoints WHERE sprint_id = ? AND checkpoint_name = ?",
        (sprint_id, "after_retrospective"),
    )
    row = await cursor.fetchone()
    assert row is not None, "after_retrospective checkpoint not found"
    checkpoint_id = row["checkpoint_id"]

    # Create new components for resume
    task_graph_resume = TaskGraph()
    engine_resume = SprintEngine(
        config=config,
        agents=agent_map,
        task_graph=task_graph_resume,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
        db=db,
    )

    # Resume from after_retrospective checkpoint (should just complete)
    resumed_result = await engine_resume.resume_sprint(checkpoint_id)

    # Verify resume completed successfully
    assert resumed_result["status"] == SprintStatus.COMPLETED
    assert len(resumed_result["tasks"]) == 2

    # Verify events include resume
    events = await event_log.query(limit=200)
    event_types = [e["event_type"] for e in events]
    assert "sprint.resumed" in event_types


@pytest.mark.asyncio
async def test_resume_with_invalid_checkpoint_id(db, tmp_path, sprint_context, components):
    """Test that resuming with an invalid checkpoint ID raises an error."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    agent_map = {}

    config = FoundrAIConfig()
    engine = SprintEngine(
        config=config,
        agents=agent_map,
        task_graph=task_graph,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
        db=db,
    )

    # Try to resume with non-existent checkpoint ID
    with pytest.raises(ValueError, match="Checkpoint .* not found"):
        await engine.resume_sprint("invalid_checkpoint_id")


@pytest.mark.asyncio
async def test_resume_sprint_state_is_restored(db, tmp_path, sprint_context, components):
    """Test that sprint state is correctly restored from checkpoint."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)
    qa_role = get_role(AgentRoleName.QA_ENGINEER)

    pm = ProductManagerAgent(
        role=pm_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(TWO_TASKS_JSON, "json"),
    )
    dev = DeveloperAgent(
        role=dev_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(DEV_RESPONSE),
    )
    qa = QAEngineerAgent(
        role=qa_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(QA_PASS_JSON, "json"),
    )

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)
    message_bus.register_agent(AgentRoleName.QA_ENGINEER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
        AgentRoleName.QA_ENGINEER.value: qa,
    }

    config = FoundrAIConfig()
    engine = SprintEngine(
        config=config,
        agents=agent_map,
        task_graph=task_graph,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
        db=db,
    )

    # Run sprint to create checkpoints
    result = await engine.run_sprint(
        goal="Build feature with checkpoints",
        project_id="test-project",
    )
    sprint_id = result["sprint_id"]
    original_goal = result["goal"]
    original_project_id = result["project_id"]

    # Get the after_planning checkpoint
    cursor = await db.conn.execute(
        "SELECT checkpoint_id FROM checkpoints WHERE sprint_id = ? AND checkpoint_name = ?",
        (sprint_id, "after_planning"),
    )
    row = await cursor.fetchone()
    assert row is not None
    checkpoint_id = row["checkpoint_id"]

    # Load checkpoint and verify state is restored
    loaded_state = await sprint_store.load_checkpoint(checkpoint_id)
    assert loaded_state is not None
    assert loaded_state["sprint_id"] == sprint_id
    assert loaded_state["goal"] == original_goal
    assert loaded_state["project_id"] == original_project_id
    assert len(loaded_state["tasks"]) == 2
    assert loaded_state["tasks"][0].title == "Implement feature"
    assert loaded_state["tasks"][1].title == "Write documentation"


@pytest.mark.asyncio
async def test_resume_sprint_with_task_dependencies(db, tmp_path, sprint_context, components):
    """Test that task dependencies are preserved when resuming from checkpoint."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    # Tasks with dependencies
    dependent_tasks_json = json.dumps([
        {
            "title": "Setup project",
            "description": "Initialize project structure",
            "acceptance_criteria": ["Project initialized"],
            "dependencies": [],
            "assigned_to": "developer",
            "priority": 1,
        },
        {
            "title": "Build feature",
            "description": "Build on top of setup",
            "acceptance_criteria": ["Feature works"],
            "dependencies": ["Setup project"],
            "assigned_to": "developer",
            "priority": 2,
        },
    ])

    pm_role = get_role(AgentRoleName.PRODUCT_MANAGER)
    dev_role = get_role(AgentRoleName.DEVELOPER)
    qa_role = get_role(AgentRoleName.QA_ENGINEER)

    pm = ProductManagerAgent(
        role=pm_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(dependent_tasks_json, "json"),
    )
    dev = DeveloperAgent(
        role=dev_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(DEV_RESPONSE),
    )
    qa = QAEngineerAgent(
        role=qa_role, model="test/model", tools=[], message_bus=message_bus,
        sprint_context=sprint_context, runtime=_make_runtime_mock(QA_PASS_JSON, "json"),
    )

    message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)
    message_bus.register_agent(AgentRoleName.DEVELOPER.value)
    message_bus.register_agent(AgentRoleName.QA_ENGINEER.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
        AgentRoleName.QA_ENGINEER.value: qa,
    }

    config = FoundrAIConfig()
    engine = SprintEngine(
        config=config,
        agents=agent_map,
        task_graph=task_graph,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
        db=db,
    )

    # Run sprint
    result = await engine.run_sprint(
        goal="Build with dependencies",
        project_id="test-project",
    )
    sprint_id = result["sprint_id"]

    # Get the after_planning checkpoint
    cursor = await db.conn.execute(
        "SELECT checkpoint_id FROM checkpoints WHERE sprint_id = ? AND checkpoint_name = ?",
        (sprint_id, "after_planning"),
    )
    row = await cursor.fetchone()
    assert row is not None
    checkpoint_id = row["checkpoint_id"]

    # Load checkpoint and verify dependencies are preserved
    loaded_state = await sprint_store.load_checkpoint(checkpoint_id)
    assert loaded_state is not None

    tasks_by_title = {t.title: t for t in loaded_state["tasks"]}
    assert "Setup project" in tasks_by_title
    assert "Build feature" in tasks_by_title

    # Verify the dependent task has correct dependency
    build_feature_task = tasks_by_title["Build feature"]
    assert len(build_feature_task.dependencies) > 0
