"""Tests for Architect and Designer agents."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from foundrai.agents.context import SprintContext
from foundrai.agents.personas.architect import ArchitectAgent
from foundrai.agents.personas.designer import DesignerAgent
from foundrai.agents.roles import get_role
from foundrai.agents.runtime import RuntimeResult
from foundrai.models.enums import AgentRoleName
from foundrai.models.task import Task


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


@pytest.fixture
def ctx(tmp_path):
    return SprintContext(
        project_name="test",
        project_path=str(tmp_path),
        sprint_goal="test goal",
        sprint_number=1,
    )


@pytest.fixture
async def message_bus(db):
    from foundrai.orchestration.message_bus import MessageBus
    from foundrai.persistence.event_log import EventLog

    el = EventLog(db)
    mb = MessageBus(el)
    mb.register_agent("architect")
    mb.register_agent("designer")
    return mb


def test_architect_role_registered():
    role = get_role(AgentRoleName.ARCHITECT)
    assert role.display_name == "Architect"
    assert "system_design" in role.skills


def test_designer_role_registered():
    role = get_role(AgentRoleName.DESIGNER)
    assert role.display_name == "Designer"
    assert "ui_design" in role.skills


@pytest.mark.asyncio
async def test_architect_review_plan(ctx, message_bus):
    review_resp = json.dumps(
        [
            {
                "title": "Build API",
                "technical_notes": "Use FastAPI",
                "additional_criteria": ["Must have OpenAPI docs"],
            }
        ]
    )
    arch = ArchitectAgent(
        role=get_role(AgentRoleName.ARCHITECT),
        model="t",
        tools=[],
        message_bus=message_bus,
        sprint_context=ctx,
        runtime=_mock_runtime(review_resp, "json"),
    )
    tasks = [
        Task(
            title="Build API",
            description="Build REST API",
            acceptance_criteria=["Responds 200"],
        )
    ]
    result = await arch.review_plan(tasks, ctx)
    assert len(result) == 1
    assert "Must have OpenAPI docs" in result[0].acceptance_criteria


@pytest.mark.asyncio
async def test_architect_execute_task(ctx, message_bus):
    arch = ArchitectAgent(
        role=get_role(AgentRoleName.ARCHITECT),
        model="t",
        tools=[],
        message_bus=message_bus,
        sprint_context=ctx,
        runtime=_mock_runtime("Designed the architecture"),
    )
    task = Task(title="Design system", description="Create system design")
    result = await arch.execute_task(task)
    assert result.success
    assert "architecture" in result.output.lower()


@pytest.mark.asyncio
async def test_designer_execute_task(ctx, message_bus):
    des = DesignerAgent(
        role=get_role(AgentRoleName.DESIGNER),
        model="t",
        tools=[],
        message_bus=message_bus,
        sprint_context=ctx,
        runtime=_mock_runtime("Created design spec"),
    )
    task = Task(title="Design UI", description="Create UI mockup")
    result = await des.execute_task(task)
    assert result.success


def test_architect_decompose_raises(ctx, message_bus):
    arch = ArchitectAgent(
        role=get_role(AgentRoleName.ARCHITECT),
        model="t",
        tools=[],
        message_bus=message_bus,
        sprint_context=ctx,
    )
    with pytest.raises(NotImplementedError):
        import asyncio

        asyncio.get_event_loop().run_until_complete(arch.decompose_goal("x"))


def test_designer_decompose_raises(ctx, message_bus):
    des = DesignerAgent(
        role=get_role(AgentRoleName.DESIGNER),
        model="t",
        tools=[],
        message_bus=message_bus,
        sprint_context=ctx,
    )
    with pytest.raises(NotImplementedError):
        import asyncio

        asyncio.get_event_loop().run_until_complete(des.decompose_goal("x"))
