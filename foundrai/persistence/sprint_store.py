"""CRUD operations for sprints and tasks."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from foundrai.models.enums import SprintStatus
from foundrai.models.sprint import SprintMetrics, SprintState
from foundrai.models.task import Task

if TYPE_CHECKING:
    from foundrai.persistence.database import Database


class SprintStore:
    """CRUD operations for sprints and tasks."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def create_sprint(self, state: SprintState) -> None:
        """Insert a new sprint record."""
        metrics = state.get("metrics", SprintMetrics())
        metrics_json = metrics.model_dump_json() if isinstance(metrics, SprintMetrics) else "{}"
        await self.db.conn.execute(
            "INSERT INTO sprints"
            " (sprint_id, project_id, sprint_number, goal, status, metrics_json)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                state["sprint_id"],
                state["project_id"],
                state.get("sprint_number", 1),
                state["goal"],
                state["status"].value if hasattr(state["status"], "value") else state["status"],
                metrics_json,
            ),
        )
        await self.db.conn.commit()

    async def get_sprint(self, sprint_id: str) -> SprintState | None:
        """Get a sprint by ID."""
        cursor = await self.db.conn.execute(
            "SELECT * FROM sprints WHERE sprint_id = ?", (sprint_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None

        tasks = await self.get_tasks(sprint_id)
        metrics_data = json.loads(row["metrics_json"] or "{}")

        return SprintState(
            sprint_id=row["sprint_id"],
            project_id=row["project_id"],
            sprint_number=row["sprint_number"],
            goal=row["goal"],
            status=SprintStatus(row["status"]),
            tasks=tasks,
            messages=[],
            artifacts=[],
            metrics=SprintMetrics(**metrics_data),
            error=row["error"],
        )

    async def update_sprint_status(
        self, sprint_id: str, status: SprintStatus
    ) -> None:
        """Update sprint status."""
        status_val = status.value if hasattr(status, "value") else status
        await self.db.conn.execute(
            "UPDATE sprints SET status = ? WHERE sprint_id = ?",
            (status_val, sprint_id),
        )
        await self.db.conn.commit()

    async def complete_sprint(self, state: SprintState) -> None:
        """Mark sprint as completed with metrics."""
        metrics = state.get("metrics", SprintMetrics())
        metrics_json = metrics.model_dump_json() if isinstance(metrics, SprintMetrics) else "{}"
        status = state["status"]
        status_val = status.value if hasattr(status, "value") else status
        await self.db.conn.execute(
            """UPDATE sprints SET status = ?, metrics_json = ?,
            completed_at = datetime('now'), error = ?
            WHERE sprint_id = ?""",
            (status_val, metrics_json, state.get("error"), state["sprint_id"]),
        )
        await self.db.conn.commit()

    async def next_sprint_number(self, project_id: str) -> int:
        """Get the next sprint number for a project."""
        cursor = await self.db.conn.execute(
            "SELECT MAX(sprint_number) as max_num FROM sprints WHERE project_id = ?",
            (project_id,),
        )
        row = await cursor.fetchone()
        if row and row["max_num"] is not None:
            return row["max_num"] + 1
        return 1

    async def create_task(self, sprint_id: str, task: Task) -> None:
        """Insert a task."""
        await self.db.conn.execute(
            """INSERT INTO tasks
            (task_id, sprint_id, title, description, acceptance_criteria_json,
             assigned_to, priority, status, dependencies_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task.id,
                sprint_id,
                task.title,
                task.description,
                json.dumps(task.acceptance_criteria),
                task.assigned_to if isinstance(task.assigned_to, str) else task.assigned_to.value,
                task.priority,
                task.status if isinstance(task.status, str) else task.status.value,
                json.dumps(task.dependencies),
            ),
        )
        await self.db.conn.commit()

    async def update_task(self, task: Task) -> None:
        """Update a task's status and results."""
        result_json = task.result.model_dump_json() if task.result else None
        review_json = task.review.model_dump_json() if task.review else None
        status_val = task.status if isinstance(task.status, str) else task.status.value
        await self.db.conn.execute(
            """UPDATE tasks SET status = ?, result_json = ?, review_json = ?,
            updated_at = datetime('now') WHERE task_id = ?""",
            (status_val, result_json, review_json, task.id),
        )
        await self.db.conn.commit()

    async def get_tasks(self, sprint_id: str) -> list[Task]:
        """Get all tasks for a sprint."""
        cursor = await self.db.conn.execute(
            "SELECT * FROM tasks WHERE sprint_id = ? ORDER BY priority, created_at",
            (sprint_id,),
        )
        rows = await cursor.fetchall()
        tasks = []
        for row in rows:
            tasks.append(Task(
                id=row["task_id"],
                title=row["title"],
                description=row["description"],
                acceptance_criteria=json.loads(row["acceptance_criteria_json"] or "[]"),
                assigned_to=row["assigned_to"],
                priority=row["priority"],
                status=row["status"],
                dependencies=json.loads(row["dependencies_json"] or "[]"),
            ))
        return tasks

    async def update_tasks(self, sprint_id: str, tasks: list[Task]) -> None:
        """Insert or update all tasks for a sprint."""
        for task in tasks:
            # Try update first, insert if not exists
            cursor = await self.db.conn.execute(
                "SELECT task_id FROM tasks WHERE task_id = ?", (task.id,)
            )
            if await cursor.fetchone():
                await self.update_task(task)
            else:
                await self.create_task(sprint_id, task)

    async def get_latest_sprint(self, project_id: str) -> SprintState | None:
        """Get the most recent sprint for a project."""
        cursor = await self.db.conn.execute(
            "SELECT sprint_id FROM sprints WHERE project_id = ?"
            " ORDER BY sprint_number DESC LIMIT 1",
            (project_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return await self.get_sprint(row["sprint_id"])

    async def has_active_sprint(self, project_id: str) -> bool:
        """Check if a project has an active (non-completed/failed) sprint."""
        cursor = await self.db.conn.execute(
            "SELECT 1 FROM sprints WHERE project_id = ?"
            " AND status NOT IN ('completed', 'failed', 'cancelled')"
            " LIMIT 1",
            (project_id,),
        )
        return await cursor.fetchone() is not None
