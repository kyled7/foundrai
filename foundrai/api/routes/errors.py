"""Error diagnosis API routes."""

from __future__ import annotations

from fastapi import APIRouter

from foundrai.api.deps import get_db
from foundrai.persistence.error_store import ErrorStore

router = APIRouter()


async def _get_error_store() -> ErrorStore:
    db = await get_db()
    return ErrorStore(db)


@router.get("/sprints/{sprint_id}/errors")
async def get_sprint_errors(sprint_id: str) -> dict:
    """Get all errors for a sprint."""
    store = await _get_error_store()
    errors = await store.get_sprint_errors(sprint_id)
    return {
        "errors": [_error_to_dict(e) for e in errors],
        "total": len(errors),
    }


@router.get("/tasks/{task_id}/errors")
async def get_task_errors(task_id: str) -> dict:
    """Get all errors for a task."""
    store = await _get_error_store()
    errors = await store.get_task_errors(task_id)
    return {
        "errors": [_error_to_dict(e) for e in errors],
        "total": len(errors),
    }


def _error_to_dict(e) -> dict:
    return {
        "error_id": e.error_id,
        "task_id": e.task_id,
        "sprint_id": e.sprint_id,
        "agent_role": e.agent_role,
        "error_type": e.error_type,
        "error_message": e.error_message,
        "traceback": e.traceback,
        "context_json": e.context_json,
        "suggested_fix": e.suggested_fix,
        "timestamp": e.timestamp,
    }
