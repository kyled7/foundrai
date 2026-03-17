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


@pytest.mark.asyncio
async def test_checkpoint_create_and_load(db):
    store = SprintStore(db)
    state: SprintState = {
        "sprint_id": "s1",
        "project_id": "proj1",
        "sprint_number": 1,
        "goal": "Test checkpoint",
        "status": SprintStatus.EXECUTING,
        "tasks": [
            Task(id="t1", title="Task 1", description="First task"),
            Task(id="t2", title="Task 2", description="Second task"),
        ],
        "messages": [],
        "artifacts": [],
        "metrics": SprintMetrics(total_tasks=2, completed_tasks=1),
    }
    await store.create_sprint(state)

    # Save checkpoint
    checkpoint_id = await store.save_checkpoint("s1", "after_task_1", state)
    assert checkpoint_id.startswith("cp_")

    # Load checkpoint
    loaded_state = await store.load_checkpoint(checkpoint_id)
    assert loaded_state is not None
    assert loaded_state["sprint_id"] == "s1"
    assert loaded_state["goal"] == "Test checkpoint"
    assert loaded_state["status"] == SprintStatus.EXECUTING
    assert len(loaded_state["tasks"]) == 2
    assert loaded_state["tasks"][0].title == "Task 1"
    assert loaded_state["metrics"].total_tasks == 2
    assert loaded_state["metrics"].completed_tasks == 1

    # Get latest checkpoint
    latest = await store.get_latest_checkpoint("s1")
    assert latest is not None
    assert latest["sprint_id"] == "s1"
    assert latest["goal"] == "Test checkpoint"
