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


@pytest.mark.asyncio
async def test_store_concurrent_updates(db):
    """Test that concurrent database operations don't cause race conditions."""
    import asyncio

    store = SprintStore(db)

    # Create a sprint
    state: SprintState = {
        "sprint_id": "concurrent_test",
        "project_id": "proj1",
        "sprint_number": 1,
        "goal": "Test concurrent updates",
        "status": SprintStatus.EXECUTING,
        "tasks": [],
        "messages": [],
        "artifacts": [],
        "metrics": SprintMetrics(),
    }
    await store.create_sprint(state)

    # Test 1: Concurrent task creations
    tasks = [
        Task(id=f"task_{i}", title=f"Task {i}", description=f"Task {i} description")
        for i in range(10)
    ]

    async def create_task_wrapper(task):
        await store.create_task("concurrent_test", task)

    # Create tasks concurrently
    await asyncio.gather(*[create_task_wrapper(task) for task in tasks])

    # Verify all tasks were created
    retrieved_tasks = await store.get_tasks("concurrent_test")
    assert len(retrieved_tasks) == 10

    # Test 2: Concurrent task updates
    async def update_task_status(task_id):
        task = Task(id=task_id, title="Updated", description="Updated", status="done")
        await store.update_task(task)

    # Update tasks concurrently
    task_ids = [f"task_{i}" for i in range(10)]
    await asyncio.gather(*[update_task_status(task_id) for task_id in task_ids])

    # Verify all tasks were updated
    updated_tasks = await store.get_tasks("concurrent_test")
    assert all(task.status == "done" for task in updated_tasks)

    # Test 3: Concurrent sprint status updates
    async def update_status():
        await store.update_sprint_status("concurrent_test", SprintStatus.EXECUTING)

    # Multiple concurrent status updates (should be safe with locking)
    await asyncio.gather(*[update_status() for _ in range(5)])

    # Verify sprint status is consistent
    sprint = await store.get_sprint("concurrent_test")
    assert sprint["status"] == SprintStatus.EXECUTING

    # Test 4: Concurrent checkpoint saves
    async def save_checkpoint(i):
        checkpoint_state = {
            "sprint_id": "concurrent_test",
            "project_id": "proj1",
            "sprint_number": 1,
            "goal": "Test concurrent updates",
            "status": SprintStatus.EXECUTING,
            "tasks": [],
            "messages": [],
            "artifacts": [],
            "metrics": SprintMetrics(total_tasks=i),
        }
        return await store.save_checkpoint("concurrent_test", f"checkpoint_{i}", checkpoint_state)

    # Save multiple checkpoints concurrently
    checkpoint_ids = await asyncio.gather(*[save_checkpoint(i) for i in range(5)])

    # Verify all checkpoints were created with unique IDs
    assert len(checkpoint_ids) == 5
    assert len(set(checkpoint_ids)) == 5  # All unique
