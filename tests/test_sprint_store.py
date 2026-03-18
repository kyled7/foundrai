"""Tests for SprintStore concurrent operations."""

from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio

from foundrai.models.enums import SprintStatus, TaskStatus
from foundrai.models.sprint import SprintMetrics, SprintState
from foundrai.models.task import Task
from foundrai.persistence.database import Database
from foundrai.persistence.sprint_store import SprintStore


@pytest_asyncio.fixture
async def sprint_store(db: Database) -> SprintStore:
    return SprintStore(db)


def _make_sprint_state(**kwargs) -> SprintState:
    defaults = {
        "sprint_id": "sprint-1",
        "project_id": "proj-1",
        "sprint_number": 1,
        "goal": "Test sprint",
        "status": SprintStatus.PLANNING,
        "tasks": [],
        "messages": [],
        "artifacts": [],
        "metrics": SprintMetrics(),
        "error": None,
    }
    defaults.update(kwargs)
    return SprintState(**defaults)


def _make_task(**kwargs) -> Task:
    defaults = {
        "id": "task-1",
        "title": "Test task",
        "description": "Test description",
        "acceptance_criteria": ["Criterion 1"],
        "assigned_to": "developer",
        "priority": 1,
        "status": TaskStatus.BACKLOG,
        "dependencies": [],
    }
    defaults.update(kwargs)
    return Task(**defaults)


@pytest.mark.asyncio
async def test_store_concurrent_updates(sprint_store: SprintStore) -> None:
    """Test that concurrent updates to the same sprint are serialized correctly."""
    # Create a sprint
    state = _make_sprint_state()
    await sprint_store.create_sprint(state)

    # Define concurrent update tasks
    async def update_status(status: SprintStatus, delay: float = 0) -> None:
        if delay:
            await asyncio.sleep(delay)
        await sprint_store.update_sprint_status("sprint-1", status)

    # Run concurrent updates
    await asyncio.gather(
        update_status(SprintStatus.EXECUTING, 0.01),
        update_status(SprintStatus.REVIEWING, 0.02),
        update_status(SprintStatus.COMPLETED, 0.03),
    )

    # Verify final state
    result = await sprint_store.get_sprint("sprint-1")
    assert result is not None
    # The final status should be COMPLETED since it has the longest delay
    assert result["status"] == SprintStatus.COMPLETED


@pytest.mark.asyncio
async def test_store_concurrent_task_updates(sprint_store: SprintStore) -> None:
    """Test that concurrent task updates are serialized correctly."""
    # Create a sprint
    state = _make_sprint_state()
    await sprint_store.create_sprint(state)

    # Create initial tasks
    task1 = _make_task(id="task-1", title="Task 1")
    task2 = _make_task(id="task-2", title="Task 2")
    await sprint_store.create_task("sprint-1", task1)
    await sprint_store.create_task("sprint-1", task2)

    # Define concurrent task update tasks
    async def update_task_status(task_id: str, status: TaskStatus, delay: float = 0) -> None:
        if delay:
            await asyncio.sleep(delay)
        task = _make_task(id=task_id, status=status)
        await sprint_store.update_task(task)

    # Run concurrent updates
    await asyncio.gather(
        update_task_status("task-1", TaskStatus.IN_PROGRESS, 0.01),
        update_task_status("task-2", TaskStatus.IN_PROGRESS, 0.01),
        update_task_status("task-1", TaskStatus.DONE, 0.02),
        update_task_status("task-2", TaskStatus.DONE, 0.02),
    )

    # Verify final state
    tasks = await sprint_store.get_tasks("sprint-1")
    assert len(tasks) == 2
    assert all(task.status == TaskStatus.DONE for task in tasks)


@pytest.mark.asyncio
async def test_store_concurrent_sprint_number_generation(sprint_store: SprintStore) -> None:
    """Test that concurrent next_sprint_number calls are serialized correctly."""
    # Create initial sprint
    state = _make_sprint_state(sprint_number=1)
    await sprint_store.create_sprint(state)

    # Define concurrent next_sprint_number calls
    async def get_next_number() -> int:
        return await sprint_store.next_sprint_number("proj-1")

    # Run concurrent calls
    results = await asyncio.gather(
        get_next_number(),
        get_next_number(),
        get_next_number(),
    )

    # All calls should return the same number (2) because of locking
    assert all(num == 2 for num in results)


@pytest.mark.asyncio
async def test_store_concurrent_checkpoint_saves(sprint_store: SprintStore) -> None:
    """Test that concurrent checkpoint saves are serialized correctly."""
    # Create a sprint
    state = _make_sprint_state()
    await sprint_store.create_sprint(state)

    # Define concurrent checkpoint save tasks
    async def save_checkpoint(name: str) -> str:
        return await sprint_store.save_checkpoint("sprint-1", name, state)

    # Run concurrent saves
    checkpoint_ids = await asyncio.gather(
        save_checkpoint("checkpoint-1"),
        save_checkpoint("checkpoint-2"),
        save_checkpoint("checkpoint-3"),
    )

    # All checkpoints should be saved successfully
    assert len(checkpoint_ids) == 3
    assert len(set(checkpoint_ids)) == 3  # All unique IDs
    for cp_id in checkpoint_ids:
        loaded = await sprint_store.load_checkpoint(cp_id)
        assert loaded is not None
        assert loaded["sprint_id"] == "sprint-1"
