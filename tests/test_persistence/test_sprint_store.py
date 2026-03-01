"""Tests for SprintStore."""

import pytest

from foundrai.models.enums import SprintStatus
from foundrai.models.sprint import SprintMetrics, SprintState
from foundrai.models.task import Task
from foundrai.persistence.sprint_store import SprintStore


@pytest.mark.asyncio
async def test_create_and_get_sprint(db):
    store = SprintStore(db)
    state: SprintState = {
        "sprint_id": "s1",
        "project_id": "proj1",
        "sprint_number": 1,
        "goal": "Build something",
        "status": SprintStatus.CREATED,
        "tasks": [],
        "messages": [],
        "artifacts": [],
        "metrics": SprintMetrics(),
    }
    await store.create_sprint(state)
    result = await store.get_sprint("s1")
    assert result is not None
    assert result["goal"] == "Build something"
    assert result["status"] == SprintStatus.CREATED


@pytest.mark.asyncio
async def test_update_sprint_status(db):
    store = SprintStore(db)
    state: SprintState = {
        "sprint_id": "s2",
        "project_id": "proj1",
        "sprint_number": 1,
        "goal": "Test",
        "status": SprintStatus.CREATED,
        "metrics": SprintMetrics(),
    }
    await store.create_sprint(state)
    await store.update_sprint_status("s2", SprintStatus.EXECUTING)
    result = await store.get_sprint("s2")
    assert result["status"] == SprintStatus.EXECUTING


@pytest.mark.asyncio
async def test_next_sprint_number(db):
    store = SprintStore(db)
    num = await store.next_sprint_number("proj1")
    assert num == 1

    state: SprintState = {
        "sprint_id": "s1",
        "project_id": "proj1",
        "sprint_number": 1,
        "goal": "First",
        "status": SprintStatus.CREATED,
        "metrics": SprintMetrics(),
    }
    await store.create_sprint(state)
    num = await store.next_sprint_number("proj1")
    assert num == 2


@pytest.mark.asyncio
async def test_create_and_get_tasks(db):
    store = SprintStore(db)
    state: SprintState = {
        "sprint_id": "s1",
        "project_id": "proj1",
        "sprint_number": 1,
        "goal": "Test",
        "status": SprintStatus.CREATED,
        "metrics": SprintMetrics(),
    }
    await store.create_sprint(state)

    task = Task(id="t1", title="Task 1", description="Do something")
    await store.create_task("s1", task)

    tasks = await store.get_tasks("s1")
    assert len(tasks) == 1
    assert tasks[0].title == "Task 1"
