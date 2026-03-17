"""Task API routes."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from foundrai.api.deps import get_db

router = APIRouter()


class TaskStatusUpdate(BaseModel):
    """Request model for updating task status."""
    status: str


@router.get("/sprints/{sprint_id}/tasks")
async def list_tasks(sprint_id: str) -> list[dict]:
    """List tasks in a sprint."""
    db = await get_db()
    # Verify sprint exists
    cursor = await db.conn.execute(
        "SELECT 1 FROM sprints WHERE sprint_id = ?", (sprint_id,)
    )
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Sprint not found")

    cursor = await db.conn.execute(
        "SELECT * FROM tasks WHERE sprint_id = ? ORDER BY priority", (sprint_id,)
    )
    rows = await cursor.fetchall()
    return [
        {
            "task_id": r["task_id"],
            "title": r["title"],
            "description": r["description"],
            "acceptance_criteria": json.loads(r["acceptance_criteria_json"] or "[]"),
            "assigned_to": r["assigned_to"],
            "priority": r["priority"],
            "status": r["status"],
            "dependencies": json.loads(r["dependencies_json"] or "[]"),
            "result": json.loads(r["result_json"]) if r["result_json"] else None,
            "review": json.loads(r["review_json"]) if r["review_json"] else None,
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]


@router.get("/tasks/{task_id}")
async def get_task(task_id: str) -> dict:
    """Get a task by ID."""
    db = await get_db()
    cursor = await db.conn.execute(
        "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": row["task_id"],
        "title": row["title"],
        "description": row["description"],
        "status": row["status"],
    }


@router.patch("/tasks/{task_id}")
async def update_task_status(task_id: str, update: TaskStatusUpdate) -> dict:
    """Update a task's status."""
    db = await get_db()

    # Verify task exists
    cursor = await db.conn.execute(
        "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update task status
    now = datetime.now(timezone.utc).isoformat()
    await db.conn.execute(
        "UPDATE tasks SET status = ?, updated_at = ? WHERE task_id = ?",
        (update.status, now, task_id)
    )
    await db.conn.commit()

    # Return updated task
    cursor = await db.conn.execute(
        "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
    )
    row = await cursor.fetchone()

    return {
        "task_id": row["task_id"],
        "title": row["title"],
        "description": row["description"],
        "acceptance_criteria": json.loads(row["acceptance_criteria_json"] or "[]"),
        "assigned_to": row["assigned_to"],
        "priority": row["priority"],
        "status": row["status"],
        "dependencies": json.loads(row["dependencies_json"] or "[]"),
        "result": json.loads(row["result_json"]) if row["result_json"] else None,
        "review": json.loads(row["review_json"]) if row["review_json"] else None,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
