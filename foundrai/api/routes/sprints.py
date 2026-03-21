"""Sprint API routes."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from foundrai.api.deps import get_db, get_vector_memory

router = APIRouter()


class SprintCreate(BaseModel):
    goal: str = Field(..., min_length=1, max_length=1000)
    auto_execute: bool = False


@router.post("/projects/{project_id}/sprints", status_code=201)
async def create_sprint(project_id: str, body: SprintCreate) -> dict:
    """Create a new sprint, optionally auto-executing it."""
    db = await get_db()

    # Check project exists
    cursor = await db.conn.execute("SELECT 1 FROM projects WHERE project_id = ?", (project_id,))
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

    result = {
        "sprint_id": sprint_id,
        "project_id": project_id,
        "sprint_number": sprint_number,
        "goal": body.goal,
        "status": "created",
        "tasks": [],
        "metrics": {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_tokens": 0,
            "total_llm_calls": 0,
            "duration_seconds": 0,
            "completion_rate": 0,
        },
    }

    # Auto-execute if requested
    if body.auto_execute:
        from foundrai.api.routes.execution import ExecuteRequest, execute_sprint

        await execute_sprint(sprint_id, ExecuteRequest(goal=body.goal))
        result["status"] = "executing"

    return result


@router.get("/projects/{project_id}/sprints")
async def list_sprints(project_id: str) -> dict:
    """List sprints for a project."""
    db = await get_db()
    cursor = await db.conn.execute("SELECT 1 FROM projects WHERE project_id = ?", (project_id,))
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Project not found")

    cursor = await db.conn.execute(
        "SELECT * FROM sprints WHERE project_id = ? ORDER BY sprint_number DESC",
        (project_id,),
    )
    rows = await cursor.fetchall()
    sprints = []
    for row in rows:
        metrics = json.loads(row["metrics_json"] or "{}")
        sprints.append(
            {
                "sprint_id": row["sprint_id"],
                "project_id": row["project_id"],
                "sprint_number": row["sprint_number"],
                "goal": row["goal"],
                "status": row["status"],
                "metrics": metrics,
            }
        )
    return {"sprints": sprints, "total": len(sprints)}


@router.get("/sprints/{sprint_id}")
async def get_sprint(sprint_id: str) -> dict:
    """Get sprint details including tasks."""
    db = await get_db()
    cursor = await db.conn.execute("SELECT * FROM sprints WHERE sprint_id = ?", (sprint_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Sprint not found")

    # Fetch tasks for this sprint
    task_cursor = await db.conn.execute(
        "SELECT * FROM tasks WHERE sprint_id = ? ORDER BY priority, created_at",
        (sprint_id,),
    )
    task_rows = await task_cursor.fetchall()
    tasks = []
    for t in task_rows:
        tasks.append(
            {
                "task_id": t["task_id"],
                "title": t["title"],
                "description": t["description"],
                "acceptance_criteria": json.loads(t["acceptance_criteria_json"] or "[]"),
                "assigned_to": t["assigned_to"],
                "priority": t["priority"],
                "status": t["status"],
                "dependencies": json.loads(t["dependencies_json"] or "[]"),
                "result": json.loads(t["result_json"]) if t["result_json"] else None,
                "review": json.loads(t["review_json"]) if t["review_json"] else None,
                "created_at": t["created_at"],
                "updated_at": t["updated_at"],
            }
        )

    metrics = json.loads(row["metrics_json"] or "{}")
    return {
        "sprint_id": row["sprint_id"],
        "project_id": row["project_id"],
        "sprint_number": row["sprint_number"],
        "goal": row["goal"],
        "status": row["status"],
        "tasks": tasks,
        "metrics": metrics,
        "created_at": row["created_at"],
        "completed_at": row["completed_at"] if "completed_at" in row.keys() else None,
        "error": row["error"] if "error" in row.keys() else None,
    }


@router.get("/sprints/{sprint_id}/metrics")
async def get_sprint_metrics(sprint_id: str) -> dict:
    """Get sprint metrics."""
    db = await get_db()
    cursor = await db.conn.execute("SELECT * FROM sprints WHERE sprint_id = ?", (sprint_id,))
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
    cursor = await db.conn.execute("SELECT 1 FROM projects WHERE project_id = ?", (project_id,))
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Project not found")

    # Create the first sprint
    result = await create_sprint(
        project_id,
        SprintCreate(goal=body.goal, auto_execute=True),
    )
    return {
        "status": "multi_sprint_started",
        "project_id": project_id,
        "sprint_id": result["sprint_id"],
        "goal": body.goal,
        "message": "First sprint is executing. Monitor via WebSocket.",
    }


@router.get("/sprints/{sprint_id}/retrospective")
async def get_retrospective(sprint_id: str) -> dict:
    """Get sprint retrospective data.

    Generates a retrospective summary from completed sprint data.
    """
    db = await get_db()
    cursor = await db.conn.execute("SELECT * FROM sprints WHERE sprint_id = ?", (sprint_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Sprint not found")

    if row["status"] not in ("completed", "failed"):
        raise HTTPException(
            status_code=400,
            detail="Retrospective is only available for completed or failed sprints",
        )

    # Gather task stats
    task_cursor = await db.conn.execute(
        "SELECT status, COUNT(*) as cnt FROM tasks WHERE sprint_id = ? GROUP BY status",
        (sprint_id,),
    )
    status_counts: dict[str, int] = {}
    for t in await task_cursor.fetchall():
        status_counts[t["status"]] = t["cnt"]

    done = status_counts.get("done", 0)
    failed = status_counts.get("failed", 0)
    total = sum(status_counts.values())
    rate = done / total if total > 0 else 0

    # Build went_well / went_wrong from task outcomes
    went_well: list[str] = []
    went_wrong: list[str] = []
    action_items: list[str] = []

    if done > 0:
        went_well.append(f"{done} of {total} tasks completed successfully")
    if rate >= 0.8:
        went_well.append("High task completion rate")
    if failed > 0:
        went_wrong.append(f"{failed} task(s) failed during execution")
        action_items.append("Review failed tasks and refine acceptance criteria for next sprint")
    if status_counts.get("blocked", 0) > 0:
        went_wrong.append(f"{status_counts['blocked']} task(s) were blocked by approval timeouts")
        action_items.append("Review approval policies to reduce bottlenecks")
    if rate < 0.5 and total > 0:
        went_wrong.append("Less than half the tasks were completed")
        action_items.append("Consider breaking goal into smaller, more achievable sprints")

    # Get learnings from DB
    learnings_from_db = []
    try:
        lc = await db.conn.execute(
            "SELECT * FROM learnings WHERE sprint_id = ? ORDER BY created_at DESC",
            (sprint_id,),
        )
        learning_rows = await lc.fetchall()
        learnings_from_db = [
            {
                "learning_id": lr["learning_id"],
                "project_id": lr["project_id"],
                "sprint_id": lr["sprint_id"],
                "content": lr["content"],
                "category": lr["category"],
                "created_at": lr["created_at"],
            }
            for lr in learning_rows
        ]
    except Exception:
        pass

    # Get learnings from VectorMemory
    learnings_from_vector = []
    try:
        vm = await get_vector_memory()
        learnings_list = await vm.get_all_learnings(sprint_id=sprint_id)
        learnings_from_vector = [
            {
                "learning_id": learning.id,
                "project_id": learning.project_id,
                "sprint_id": learning.sprint_id,
                "content": learning.content,
                "category": learning.category,
                "timestamp": learning.timestamp,
            }
            for learning in learnings_list
        ]
    except Exception:
        pass

    # Get cost summary
    cost_cursor = await db.conn.execute(
        """SELECT COALESCE(SUM(cost_usd), 0.0) as total_cost,
                  COALESCE(SUM(total_tokens), 0) as total_tokens
           FROM token_usage WHERE sprint_id = ?""",
        (sprint_id,),
    )
    cost_row = await cost_cursor.fetchone()

    # Get by-agent breakdown
    agent_cursor = await db.conn.execute(
        """SELECT agent_role,
                  COALESCE(SUM(cost_usd), 0.0) as cost_usd,
                  COALESCE(SUM(total_tokens), 0) as tokens
           FROM token_usage WHERE sprint_id = ?
           GROUP BY agent_role""",
        (sprint_id,),
    )
    by_agent = {
        row["agent_role"]: {"cost_usd": row["cost_usd"], "tokens": row["tokens"]}
        for row in await agent_cursor.fetchall()
    }

    # Get by-task breakdown
    task_cursor = await db.conn.execute(
        """SELECT task_id,
                  COALESCE(SUM(cost_usd), 0.0) as cost_usd,
                  COALESCE(SUM(total_tokens), 0) as tokens
           FROM token_usage WHERE sprint_id = ?
           GROUP BY task_id""",
        (sprint_id,),
    )
    by_task = {
        row["task_id"]: {"cost_usd": row["cost_usd"], "tokens": row["tokens"]}
        for row in await task_cursor.fetchall()
    }

    cost_summary = {
        "total_cost": cost_row["total_cost"],
        "total_tokens": cost_row["total_tokens"],
        "by_agent": by_agent,
        "by_task": by_task,
    }

    return {
        "went_well": went_well,
        "went_wrong": went_wrong,
        "action_items": action_items,
        "learnings_count": len(learnings_from_db),
        "learnings": learnings_from_db,
        "learnings_vector": learnings_from_vector,
        "cost_summary": cost_summary,
    }


@router.get("/sprints/{sprint_id}/goal-tree")
async def get_goal_tree(sprint_id: str) -> dict:
    """Get goal decomposition tree."""
    db = await get_db()
    cursor = await db.conn.execute("SELECT * FROM sprints WHERE sprint_id = ?", (sprint_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Sprint not found")

    nodes = [
        {
            "id": sprint_id,
            "type": "goal",
            "label": row["goal"],
            "status": row["status"],
            "assigned_to": None,
            "metadata": {},
        }
    ]
    edges = []

    # Add task nodes
    task_cursor = await db.conn.execute("SELECT * FROM tasks WHERE sprint_id = ?", (sprint_id,))
    task_rows = await task_cursor.fetchall()
    for task in task_rows:
        nodes.append(
            {
                "id": task["task_id"],
                "type": "task",
                "label": task["title"],
                "status": task["status"],
                "assigned_to": task["assigned_to"],
                "metadata": {},
            }
        )
        edges.append(
            {
                "source": sprint_id,
                "target": task["task_id"],
                "type": "decomposition",
            }
        )

    return {"nodes": nodes, "edges": edges}
