"""Tests for Sprint ceremonies (Planning, Review, Retrospective)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from foundrai.agents.context import SprintContext
from foundrai.agents.personas.product_manager import ProductManagerAgent
from foundrai.agents.roles import get_role
from foundrai.agents.runtime import RuntimeResult
from foundrai.models.enums import AgentRoleName, SprintStatus, TaskStatus
from foundrai.models.sprint import SprintMetrics, SprintState
from foundrai.models.task import Task
from foundrai.orchestration.ceremonies import (
    SprintPlanning,
    SprintRetrospective,
    SprintReview,
)


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


def _make_pm(message_bus, ctx, resp):
    pm = ProductManagerAgent(
        role=get_role(AgentRoleName.PRODUCT_MANAGER), model="t", tools=[],
        message_bus=message_bus, sprint_context=ctx,
        runtime=_mock_runtime(resp, "json"),
    )
    return pm


SINGLE_TASK = json.dumps([{
    "title": "Task A", "description": "Do A",
    "acceptance_criteria": ["A works"], "dependencies": [],
    "assigned_to": "developer", "priority": 1,
}])


@pytest.fixture
def ctx(tmp_path):
    return SprintContext(
        project_name="test", project_path=str(tmp_path),
        sprint_goal="test goal", sprint_number=1,
    )


@pytest.fixture
async def message_bus(db):
    from foundrai.orchestration.message_bus import MessageBus
    from foundrai.persistence.event_log import EventLog
    el = EventLog(db)
    mb = MessageBus(el)
    mb.register_agent("product_manager")
    return mb


@pytest.mark.asyncio
async def test_planning_basic(ctx, message_bus):
    pm = _make_pm(message_bus, ctx, SINGLE_TASK)
    planning = SprintPlanning()
    tasks = await planning.run(
        goal="build something",
        agents={"product_manager": pm},
        context=ctx,
    )
    assert len(tasks) == 1
    assert tasks[0].title == "Task A"
    assert tasks[0].estimated_tokens > 0


@pytest.mark.asyncio
async def test_planning_no_pm(ctx):
    planning = SprintPlanning()
    tasks = await planning.run(
        goal="build something",
        agents={},
        context=ctx,
    )
    assert tasks == []


@pytest.mark.asyncio
async def test_planning_effort_estimation(ctx, message_bus):
    pm = _make_pm(message_bus, ctx, SINGLE_TASK)
    planning = SprintPlanning()
    tasks = await planning.run(
        goal="build something",
        agents={"product_manager": pm},
        context=ctx,
    )
    # Should have reasonable estimate
    assert 1000 <= tasks[0].estimated_tokens <= 8000


def test_review_auto_score():
    review = SprintReview()
    done_task = Task(title="T1", description="D", status=TaskStatus.DONE)
    failed_task = Task(title="T2", description="D", status=TaskStatus.FAILED)
    score = review._auto_score([done_task], [failed_task])
    assert score == 0.5


def test_review_all_done():
    review = SprintReview()
    done1 = Task(title="T1", description="D", status=TaskStatus.DONE)
    done2 = Task(title="T2", description="D", status=TaskStatus.DONE)
    score = review._auto_score([done1, done2], [])
    assert score == 1.0


def test_review_empty():
    review = SprintReview()
    score = review._auto_score([], [])
    assert score == 0.0


@pytest.mark.asyncio
async def test_review_ceremony():
    review = SprintReview()
    state: SprintState = {
        "project_id": "p1",
        "sprint_id": "s1",
        "sprint_number": 1,
        "goal": "test",
        "status": SprintStatus.REVIEWING,
        "tasks": [
            Task(title="T1", description="D", status=TaskStatus.DONE),
            Task(title="T2", description="D", status=TaskStatus.FAILED),
        ],
        "messages": [],
        "artifacts": [],
        "metrics": SprintMetrics(),
        "created_at": "",
        "completed_at": None,
        "error": None,
    }
    summary = await review.run(state, {})
    assert summary.completed_count == 1
    assert summary.failed_count == 1
    assert summary.quality_score == 0.5


@pytest.mark.asyncio
async def test_retrospective_basic():
    retro = SprintRetrospective()
    state: SprintState = {
        "project_id": "p1",
        "sprint_id": "s1",
        "sprint_number": 1,
        "goal": "test",
        "status": SprintStatus.COMPLETED,
        "tasks": [
            Task(title="T1", description="D", status=TaskStatus.DONE),
            Task(title="T2", description="D", status=TaskStatus.FAILED),
        ],
        "messages": [],
        "artifacts": [],
        "metrics": SprintMetrics(),
        "created_at": "",
        "completed_at": None,
        "error": None,
    }
    summary = await retro.run(state, {})
    assert len(summary.learnings) > 0
    assert any("completion rate" in lr.content.lower() for lr in summary.learnings)


@pytest.mark.asyncio
async def test_retrospective_with_pm(ctx, message_bus):
    retro_resp = json.dumps({
        "went_well": ["Good decomposition"],
        "went_wrong": ["Slow execution"],
        "action_items": ["Improve prompts"],
        "learnings": ["Be more specific with acceptance criteria"],
    })
    pm = _make_pm(message_bus, ctx, SINGLE_TASK)
    pm.runtime = _mock_runtime(retro_resp, "json")

    retro = SprintRetrospective()
    state: SprintState = {
        "project_id": "p1",
        "sprint_id": "s1",
        "sprint_number": 1,
        "goal": "test",
        "status": SprintStatus.COMPLETED,
        "tasks": [
            Task(title="T1", description="D", status=TaskStatus.DONE),
        ],
        "messages": [],
        "artifacts": [],
        "metrics": SprintMetrics(),
        "created_at": "",
        "completed_at": None,
        "error": None,
    }
    summary = await retro.run(state, {"product_manager": pm})
    assert "Good decomposition" in summary.went_well
    assert "Slow execution" in summary.went_wrong
    assert len(summary.learnings) > 0
