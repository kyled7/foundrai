"""Tests for parallel task execution in SprintEngine."""

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


def _mock_runtime(content, fmt=None):
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


def _make_agents(message_bus, ctx, pm_resp, dev_resp="Done", qa_resp=None):
    pm = ProductManagerAgent(
        role=get_role(AgentRoleName.PRODUCT_MANAGER), model="t", tools=[],
        message_bus=message_bus, sprint_context=ctx,
        runtime=_mock_runtime(pm_resp, "json"),
    )
    dev = DeveloperAgent(
        role=get_role(AgentRoleName.DEVELOPER), model="t", tools=[],
        message_bus=message_bus, sprint_context=ctx,
        runtime=_mock_runtime(dev_resp),
    )
    agents = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
    }
    if qa_resp is not None:
        qa = QAEngineerAgent(
            role=get_role(AgentRoleName.QA_ENGINEER), model="t", tools=[],
            message_bus=message_bus, sprint_context=ctx,
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


# 3 independent tasks (can run in parallel)
PARALLEL_TASKS = json.dumps([
    {"title": "T1", "description": "D1", "acceptance_criteria": [],
     "dependencies": [], "assigned_to": "developer", "priority": 1},
    {"title": "T2", "description": "D2", "acceptance_criteria": [],
     "dependencies": [], "assigned_to": "developer", "priority": 2},
    {"title": "T3", "description": "D3", "acceptance_criteria": [],
     "dependencies": [], "assigned_to": "developer", "priority": 3},
])

# Tasks with dependency chain: T1 -> T2 -> T3
CHAINED_TASKS = json.dumps([
    {"title": "T1", "description": "D1", "acceptance_criteria": [],
     "dependencies": [], "assigned_to": "developer", "priority": 1},
    {"title": "T2", "description": "D2", "acceptance_criteria": [],
     "dependencies": ["T1"], "assigned_to": "developer", "priority": 2},
    {"title": "T3", "description": "D3", "acceptance_criteria": [],
     "dependencies": ["T2"], "assigned_to": "developer", "priority": 3},
])


@pytest.mark.asyncio
async def test_parallel_independent_tasks(db, ctx, infra):
    """3 independent tasks should all complete (executed in parallel)."""
    el, ss, art, mb, tg = infra
    qa_pass = json.dumps({"passed": True, "issues": [], "suggestions": []})
    agents = _make_agents(mb, ctx, PARALLEL_TASKS, qa_resp=qa_pass)

    engine = SprintEngine(
        config=FoundrAIConfig(), agents=agents, task_graph=tg,
        message_bus=mb, sprint_store=ss, event_log=el, artifact_store=art,
    )
    result = await engine.run_sprint("parallel", "proj")
    assert result["status"] == SprintStatus.COMPLETED
    assert len(result["tasks"]) == 3
    assert all(t.status == TaskStatus.DONE for t in result["tasks"])


@pytest.mark.asyncio
async def test_chained_tasks_execute_in_order(db, ctx, infra):
    """Chained tasks should execute sequentially due to dependencies."""
    el, ss, art, mb, tg = infra
    qa_pass = json.dumps({"passed": True, "issues": [], "suggestions": []})
    agents = _make_agents(mb, ctx, CHAINED_TASKS, qa_resp=qa_pass)

    engine = SprintEngine(
        config=FoundrAIConfig(), agents=agents, task_graph=tg,
        message_bus=mb, sprint_store=ss, event_log=el, artifact_store=art,
    )
    result = await engine.run_sprint("chain", "proj")
    assert result["status"] == SprintStatus.COMPLETED
    assert all(t.status == TaskStatus.DONE for t in result["tasks"])


@pytest.mark.asyncio
async def test_retrospective_runs_after_review(db, ctx, infra):
    """Sprint should include retrospective step."""
    el, ss, art, mb, tg = infra
    qa_pass = json.dumps({"passed": True, "issues": [], "suggestions": []})
    agents = _make_agents(mb, ctx, PARALLEL_TASKS, qa_resp=qa_pass)

    events_captured = []

    async def listener(event_type, data):
        events_captured.append(event_type)

    el.register_listener(listener)

    engine = SprintEngine(
        config=FoundrAIConfig(), agents=agents, task_graph=tg,
        message_bus=mb, sprint_store=ss, event_log=el, artifact_store=art,
    )
    await engine.run_sprint("retro", "proj")

    assert "sprint.retrospective_started" in events_captured
    assert "sprint.retrospective_completed" in events_captured
    assert "sprint.review_completed" in events_captured
