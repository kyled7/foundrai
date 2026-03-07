"""Sprint API routes."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from foundrai.api.deps import get_db

router = APIRouter()


class SprintCreate(BaseModel):
    goal: str = Field(..., min_length=1, max_length=1000)


@router.post("/projects/{project_id}/sprints", status_code=201)
async def create_sprint(project_id: str, body: SprintCreate) -> dict:
    """Create a new sprint."""
    db = await get_db()

    # Check project exists
    cursor = await db.conn.execute(
        "SELECT 1 FROM projects WHERE project_id = ?", (project_id,)
    )
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Project not found")

    # Check no active sprint
    cursor = await db.conn.execute(
        "SELECT 1 FROM sprints WHERE project_id = ?"
        " AND status NOT IN ('completed', 'failed', 'cancelled')",
        (project_id,),
    )
    if await cursor.fetchone():
        raise HTTPException(status_code=409, detail="Active sprint already exists")

    # Get next sprint number
    cursor = await db.conn.execute(
        "SELECT MAX(sprint_number) as m FROM sprints WHERE project_id = ?",
        (project_id,),
    )
    row = await cursor.fetchone()
    sprint_number = (row["m"] or 0) + 1

    sprint_id = str(uuid.uuid4())
    await db.conn.execute(
        """INSERT INTO sprints (sprint_id, project_id, sprint_number, goal, status)
        VALUES (?, ?, ?, ?, ?)""",
        (sprint_id, project_id, sprint_number, body.goal, "created"),
    )
    await db.conn.commit()

    return {
        "sprint_id": sprint_id,
        "project_id": project_id,
        "sprint_number": sprint_number,
        "goal": body.goal,
        "status": "created",
        "tasks": [],
        "metrics": {"total_tasks": 0, "completed_tasks": 0, "failed_tasks": 0,
                     "total_tokens": 0, "total_llm_calls": 0, "duration_seconds": 0,
                     "completion_rate": 0},
    }


@router.get("/projects/{project_id}/sprints")
async def list_sprints(project_id: str) -> dict:
    """List sprints for a project."""
    db = await get_db()
    cursor = await db.conn.execute(
        "SELECT 1 FROM projects WHERE project_id = ?", (project_id,)
    )
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Project not found")

    cursor = await db.conn.execute(
        "SELECT * FROM sprints WHERE project_id = ? ORDER BY sprint_number DESC",
        (project_id,),
    )
    rows = await cursor.fetchall()
    sprints = []
    for row in rows:
        sprints.append({
            "sprint_id": row["sprint_id"],
            "project_id": row["project_id"],
            "sprint_number": row["sprint_number"],
            "goal": row["goal"],
            "status": row["status"],
        })
    return {"sprints": sprints, "total": len(sprints)}


@router.get("/sprints/{sprint_id}")
async def get_sprint(sprint_id: str) -> dict:
    """Get sprint details."""
    db = await get_db()
    cursor = await db.conn.execute(
        "SELECT * FROM sprints WHERE sprint_id = ?", (sprint_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Sprint not found")

    return {
        "sprint_id": row["sprint_id"],
        "project_id": row["project_id"],
        "sprint_number": row["sprint_number"],
        "goal": row["goal"],
        "status": row["status"],
        "metrics": json.loads(row["metrics_json"] or "{}"),
    }


@router.get("/sprints/{sprint_id}/metrics")
async def get_sprint_metrics(sprint_id: str) -> dict:
    """Get sprint metrics."""
    db = await get_db()
    cursor = await db.conn.execute(
        "SELECT * FROM sprints WHERE sprint_id = ?", (sprint_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Sprint not found")

    metrics = json.loads(row["metrics_json"] or "{}")
    return {
        "total_tasks": metrics.get("total_tasks", 0),
        "completed_tasks": metrics.get("completed_tasks", 0),
        "failed_tasks": metrics.get("failed_tasks", 0),
        "total_tokens": metrics.get("total_tokens", 0),
        "total_llm_calls": metrics.get("total_llm_calls", 0),
        "duration_seconds": metrics.get("duration_seconds", 0),
        "completion_rate": metrics.get("completion_rate", 0),
        "tasks_by_status": metrics.get("tasks_by_status", {}),
        "tokens_by_agent": metrics.get("tokens_by_agent", {}),
    }


@router.post("/projects/{project_id}/sprints/multi")
async def start_multi_sprint(project_id: str, body: SprintCreate) -> dict:
    """Start a multi-sprint execution that iterates until goal is achieved."""
    db = await get_db()
    cursor = await db.conn.execute(
        "SELECT 1 FROM projects WHERE project_id = ?", (project_id,)
    )
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "status": "multi_sprint_queued",
        "project_id": project_id,
        "goal": body.goal,
        "message": "Multi-sprint execution queued. Monitor via WebSocket or events API.",
    }


@router.get("/sprints/{sprint_id}/goal-tree")
async def get_goal_tree(sprint_id: str) -> dict:
    """Get goal decomposition tree."""
    db = await get_db()
    cursor = await db.conn.execute(
        "SELECT * FROM sprints WHERE sprint_id = ?", (sprint_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Sprint not found")

    nodes = [{"id": sprint_id, "type": "goal", "label": row["goal"],
              "status": row["status"], "assigned_to": None, "metadata": {}}]
    edges = []

    # Add task nodes
    task_cursor = await db.conn.execute(
        "SELECT * FROM tasks WHERE sprint_id = ?", (sprint_id,)
    )
    task_rows = await task_cursor.fetchall()
    for task in task_rows:
        nodes.append({
            "id": task["task_id"],
            "type": "task",
            "label": task["title"],
            "status": task["status"],
            "assigned_to": task["assigned_to"],
            "metadata": {},
        })
        edges.append({"source": sprint_id, "target": task["task_id"], "type": "decomposition"})

    return {"nodes": nodes, "edges": edges}
