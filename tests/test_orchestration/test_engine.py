"""Tests for SprintEngine."""

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


def test_engine_module_imports():
    """Verify engine module can be imported without errors."""
    assert SprintEngine is not None


def _mock_runtime(content: str, fmt: str | None = None):
    parsed = None
    if fmt == "json" or content.startswith(("[", "{")):
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            pass
    rt = AsyncMock()
    rt.run = AsyncMock(return_value=RuntimeResult(
        output=content, parsed=parsed, artifacts=[], tokens_used=50, success=True,
    ))
    return rt


def _make_agents(message_bus, sprint_context, pm_resp, dev_resp="Done", qa_resp=None):
    pm = ProductManagerAgent(
        role=get_role(AgentRoleName.PRODUCT_MANAGER), model="t", tools=[],
        message_bus=message_bus, sprint_context=sprint_context,
        runtime=_mock_runtime(pm_resp, "json"),
    )
    dev = DeveloperAgent(
        role=get_role(AgentRoleName.DEVELOPER), model="t", tools=[],
        message_bus=message_bus, sprint_context=sprint_context,
        runtime=_mock_runtime(dev_resp),
    )
    agents = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
    }
    if qa_resp is not None:
        qa = QAEngineerAgent(
            role=get_role(AgentRoleName.QA_ENGINEER), model="t", tools=[],
            message_bus=message_bus, sprint_context=sprint_context,
            runtime=_mock_runtime(qa_resp, "json"),
        )
        agents[AgentRoleName.QA_ENGINEER.value] = qa
    return agents


@pytest.fixture
def ctx(tmp_path):
    return SprintContext(
        project_name="test", project_path=str(tmp_path),
        sprint_goal="test goal", sprint_number=1,
    )


@pytest.fixture
async def infra(db):
    el = EventLog(db)
    ss = SprintStore(db)
    art = ArtifactStore(db)
    mb = MessageBus(el)
    tg = TaskGraph()
    for r in ["product_manager", "developer", "qa_engineer"]:
        mb.register_agent(r)
    return el, ss, art, mb, tg


SINGLE_TASK = json.dumps([{
    "title": "Task A", "description": "Do A",
    "acceptance_criteria": ["A works"], "dependencies": [],
    "assigned_to": "developer", "priority": 1,
}])

TWO_TASKS = json.dumps([
    {"title": "T1", "description": "D1", "acceptance_criteria": [],
     "dependencies": [], "assigned_to": "developer", "priority": 1},
    {"title": "T2", "description": "D2", "acceptance_criteria": [],
     "dependencies": ["T1"], "assigned_to": "developer", "priority": 2},
])


@pytest.mark.asyncio
async def test_engine_build_graph(db, ctx, infra):
    el, ss, art, mb, tg = infra
    agents = _make_agents(mb, ctx, SINGLE_TASK)
    engine = SprintEngine(
        config=FoundrAIConfig(), agents=agents, task_graph=tg,
        message_bus=mb, sprint_store=ss, event_log=el, artifact_store=art,
    )
    assert engine.graph is not None


@pytest.mark.asyncio
async def test_engine_run_sprint_basic(db, ctx, infra):
    el, ss, art, mb, tg = infra
    qa_pass = json.dumps({"passed": True, "issues": [], "suggestions": []})
    agents = _make_agents(mb, ctx, SINGLE_TASK, qa_resp=qa_pass)

    engine = SprintEngine(
        config=FoundrAIConfig(), agents=agents, task_graph=tg,
        message_bus=mb, sprint_store=ss, event_log=el, artifact_store=art,
    )
    result = await engine.run_sprint("test", "proj")
    assert result["status"] == SprintStatus.COMPLETED
    assert len(result["tasks"]) == 1
    assert result["tasks"][0].status == TaskStatus.DONE


@pytest.mark.asyncio
async def test_engine_route_after_plan_no_tasks(db, ctx, infra):
    el, ss, art, mb, tg = infra
    agents = _make_agents(mb, ctx, "[]")

    engine = SprintEngine(
        config=FoundrAIConfig(), agents=agents, task_graph=tg,
        message_bus=mb, sprint_store=ss, event_log=el, artifact_store=art,
    )
    result = await engine.run_sprint("empty", "proj")
    assert result["status"] == SprintStatus.FAILED


@pytest.mark.asyncio
async def test_engine_route_after_plan_error(db, ctx, infra):
    el, ss, art, mb, tg = infra
    agents = _make_agents(mb, ctx, SINGLE_TASK)
    # Make PM raise
    agents[AgentRoleName.PRODUCT_MANAGER.value].runtime.run = AsyncMock(
        side_effect=Exception("boom")
    )

    engine = SprintEngine(
        config=FoundrAIConfig(), agents=agents, task_graph=tg,
        message_bus=mb, sprint_store=ss, event_log=el, artifact_store=art,
    )
    result = await engine.run_sprint("err", "proj")
    assert result["status"] == SprintStatus.FAILED
    assert "Planning failed" in result["error"]


@pytest.mark.asyncio
async def test_engine_task_execution_failure(db, ctx, infra):
    """When dev raises on execute_task, task should be marked failed."""
    el, ss, art, mb, tg = infra
    qa_pass = json.dumps({"passed": True, "issues": [], "suggestions": []})
    agents = _make_agents(mb, ctx, SINGLE_TASK, qa_resp=qa_pass)
    # Make dev fail
    agents[AgentRoleName.DEVELOPER.value].runtime.run = AsyncMock(
        side_effect=RuntimeError("code crash")
    )

    engine = SprintEngine(
        config=FoundrAIConfig(), agents=agents, task_graph=tg,
        message_bus=mb, sprint_store=ss, event_log=el, artifact_store=art,
    )
    result = await engine.run_sprint("dev fail", "proj")
    assert result["status"] == SprintStatus.COMPLETED
    assert result["tasks"][0].status == TaskStatus.FAILED


@pytest.mark.asyncio
async def test_engine_no_pm_agent(db, ctx, infra):
    el, ss, art, mb, tg = infra
    # No PM in agents
    agents = {
        AgentRoleName.DEVELOPER.value: (
            _make_agents(mb, ctx, SINGLE_TASK)[AgentRoleName.DEVELOPER.value]
        )
    }
    engine = SprintEngine(
        config=FoundrAIConfig(), agents=agents, task_graph=tg,
        message_bus=mb, sprint_store=ss, event_log=el, artifact_store=art,
    )
    result = await engine.run_sprint("no pm", "proj")
    assert result["status"] == SprintStatus.FAILED
    assert "Product Manager" in result["error"]


@pytest.mark.asyncio
async def test_engine_no_dev_agent(db, ctx, infra):
    """Without dev agent, tasks fail but sprint completes (Phase 2 behavior)."""
    el, ss, art, mb, tg = infra
    agents = {
        AgentRoleName.PRODUCT_MANAGER.value: (
            _make_agents(mb, ctx, SINGLE_TASK)[AgentRoleName.PRODUCT_MANAGER.value]
        )
    }
    engine = SprintEngine(
        config=FoundrAIConfig(), agents=agents, task_graph=tg,
        message_bus=mb, sprint_store=ss, event_log=el, artifact_store=art,
    )
    result = await engine.run_sprint("no dev", "proj")
    # Phase 2: sprint completes but tasks remain in backlog (no agent to execute)
    assert result["status"] == SprintStatus.COMPLETED
    assert result["tasks"][0].status in (TaskStatus.BACKLOG, TaskStatus.FAILED)


@pytest.mark.asyncio
async def test_engine_with_dependencies(db, ctx, infra):
    el, ss, art, mb, tg = infra
    qa_pass = json.dumps({"passed": True, "issues": [], "suggestions": []})
    agents = _make_agents(mb, ctx, TWO_TASKS, qa_resp=qa_pass)

    engine = SprintEngine(
        config=FoundrAIConfig(), agents=agents, task_graph=tg,
        message_bus=mb, sprint_store=ss, event_log=el, artifact_store=art,
    )
    result = await engine.run_sprint("deps", "proj")
    assert result["status"] == SprintStatus.COMPLETED
    assert len(result["tasks"]) == 2


@pytest.mark.asyncio
async def test_engine_metrics_calculated(db, ctx, infra):
    el, ss, art, mb, tg = infra
    qa_pass = json.dumps({"passed": True, "issues": [], "suggestions": []})
    agents = _make_agents(mb, ctx, SINGLE_TASK, qa_resp=qa_pass)

    engine = SprintEngine(
        config=FoundrAIConfig(), agents=agents, task_graph=tg,
        message_bus=mb, sprint_store=ss, event_log=el, artifact_store=art,
    )
    result = await engine.run_sprint("metrics", "proj")
    m = result["metrics"]
    assert m.total_tasks == 1
    assert m.completed_tasks == 1
    assert m.total_tokens == 50  # from mock


@pytest.mark.asyncio
async def test_engine_event_listener(db, ctx, infra):
    el, ss, art, mb, tg = infra
    qa_pass = json.dumps({"passed": True, "issues": [], "suggestions": []})
    agents = _make_agents(mb, ctx, SINGLE_TASK, qa_resp=qa_pass)

    events_captured = []

    async def listener(event_type, data):
        events_captured.append(event_type)

    el.register_listener(listener)

    engine = SprintEngine(
        config=FoundrAIConfig(), agents=agents, task_graph=tg,
        message_bus=mb, sprint_store=ss, event_log=el, artifact_store=art,
    )
    await engine.run_sprint("events", "proj")

    assert "sprint.started" in events_captured
    assert "sprint.status_changed" in events_captured
    assert "task.status_changed" in events_captured
