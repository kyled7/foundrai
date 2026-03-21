"""Tests for multi-sprint support with learning carryover."""

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
from foundrai.config import FoundrAIConfig, MemoryConfig
from foundrai.models.enums import AgentRoleName, SprintStatus
from foundrai.orchestration.engine import SprintEngine
from foundrai.orchestration.message_bus import MessageBus
from foundrai.orchestration.task_graph import TaskGraph
from foundrai.persistence.artifact_store import ArtifactStore
from foundrai.persistence.event_log import EventLog
from foundrai.persistence.sprint_store import SprintStore
from foundrai.persistence.vector_memory import VectorMemory


def _mock_runtime(content, fmt=None):
    parsed = None
    if fmt == "json" or content.startswith(("[", "{")):
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            pass
    rt = AsyncMock()
    rt.run = AsyncMock(
        return_value=RuntimeResult(
            output=content,
            parsed=parsed,
            artifacts=[],
            tokens_used=50,
            success=True,
        )
    )
    return rt


SINGLE_TASK = json.dumps(
    [
        {
            "title": "Task A",
            "description": "Do A",
            "acceptance_criteria": ["A works"],
            "dependencies": [],
            "assigned_to": "developer",
            "priority": 1,
        }
    ]
)


@pytest.fixture
def ctx(tmp_path):
    return SprintContext(
        project_name="test",
        project_path=str(tmp_path),
        sprint_goal="test goal",
        sprint_number=1,
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


def _make_agents(mb, ctx, pm_resp):
    qa_pass = json.dumps({"passed": True, "issues": [], "suggestions": []})
    pm = ProductManagerAgent(
        role=get_role(AgentRoleName.PRODUCT_MANAGER),
        model="t",
        tools=[],
        message_bus=mb,
        sprint_context=ctx,
        runtime=_mock_runtime(pm_resp, "json"),
    )
    dev = DeveloperAgent(
        role=get_role(AgentRoleName.DEVELOPER),
        model="t",
        tools=[],
        message_bus=mb,
        sprint_context=ctx,
        runtime=_mock_runtime("Done"),
    )
    qa = QAEngineerAgent(
        role=get_role(AgentRoleName.QA_ENGINEER),
        model="t",
        tools=[],
        message_bus=mb,
        sprint_context=ctx,
        runtime=_mock_runtime(qa_pass, "json"),
    )
    return {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
        AgentRoleName.QA_ENGINEER.value: qa,
    }


@pytest.mark.asyncio
async def test_two_sprints_same_project(db, ctx, infra):
    """Two sprints on the same project should both complete."""
    el, ss, art, mb, tg = infra
    agents = _make_agents(mb, ctx, SINGLE_TASK)

    engine = SprintEngine(
        config=FoundrAIConfig(),
        agents=agents,
        task_graph=tg,
        message_bus=mb,
        sprint_store=ss,
        event_log=el,
        artifact_store=art,
    )

    result1 = await engine.run_sprint("Sprint 1 goal", "proj1")
    assert result1["status"] == SprintStatus.COMPLETED
    assert result1["sprint_number"] == 1

    # Reset task graph for sprint 2
    engine.task_graph = TaskGraph()
    result2 = await engine.run_sprint("Sprint 2 goal", "proj1")
    assert result2["status"] == SprintStatus.COMPLETED
    assert result2["sprint_number"] == 2


@pytest.mark.asyncio
async def test_sprint_with_vector_memory(db, ctx, infra, tmp_path):
    """Sprint with vector memory should store learnings."""
    el, ss, art, mb, tg = infra
    agents = _make_agents(mb, ctx, SINGLE_TASK)

    vm = VectorMemory(MemoryConfig(chromadb_path=str(tmp_path / "vectors")))

    engine = SprintEngine(
        config=FoundrAIConfig(),
        agents=agents,
        task_graph=tg,
        message_bus=mb,
        sprint_store=ss,
        event_log=el,
        artifact_store=art,
        vector_memory=vm,
    )

    result = await engine.run_sprint("Test with memory", "proj1")
    assert result["status"] == SprintStatus.COMPLETED

    # Check that learnings were stored
    learnings = await vm.get_all_learnings()
    assert len(learnings) > 0


@pytest.mark.asyncio
async def test_sprint_numbers_increment(db, ctx, infra):
    """Sprint numbers should auto-increment per project."""
    el, ss, art, mb, tg = infra
    agents = _make_agents(mb, ctx, SINGLE_TASK)

    for i in range(3):
        engine = SprintEngine(
            config=FoundrAIConfig(),
            agents=agents,
            task_graph=TaskGraph(),
            message_bus=mb,
            sprint_store=ss,
            event_log=el,
            artifact_store=art,
        )
        result = await engine.run_sprint(f"Goal {i}", "proj1")
        assert result["sprint_number"] == i + 1
