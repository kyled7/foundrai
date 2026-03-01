"""Task API routes."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from foundrai.api.deps import get_db

router = APIRouter()


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
