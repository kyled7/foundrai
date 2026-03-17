"""CRUD operations for sprints and tasks."""

from __future__ import annotations

import json
import uuid
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

    async def save_checkpoint(
        self, sprint_id: str, checkpoint_name: str, state: SprintState
    ) -> str:
        """Save a sprint checkpoint and return the checkpoint ID."""
        checkpoint_id = f"cp_{uuid.uuid4().hex[:12]}"
        state_json = json.dumps({
            "sprint_id": state["sprint_id"],
            "project_id": state["project_id"],
            "sprint_number": state.get("sprint_number", 1),
            "goal": state["goal"],
            "status": state["status"].value if hasattr(state["status"], "value") else state["status"],
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "acceptance_criteria": task.acceptance_criteria,
                    "assigned_to": task.assigned_to if isinstance(task.assigned_to, str) else task.assigned_to.value,
                    "priority": task.priority,
                    "status": task.status if isinstance(task.status, str) else task.status.value,
                    "dependencies": task.dependencies,
                }
                for task in state.get("tasks", [])
            ],
            "metrics": (
                state["metrics"].model_dump()
                if isinstance(state.get("metrics"), SprintMetrics)
                else state.get("metrics", {})
            ),
            "error": state.get("error"),
        })
        await self.db.conn.execute(
            "INSERT INTO checkpoints (checkpoint_id, sprint_id, checkpoint_name, state_json)"
            " VALUES (?, ?, ?, ?)",
            (checkpoint_id, sprint_id, checkpoint_name, state_json),
        )
        await self.db.conn.commit()
        return checkpoint_id

    async def load_checkpoint(self, checkpoint_id: str) -> SprintState | None:
        """Load a checkpoint by ID."""
        cursor = await self.db.conn.execute(
            "SELECT state_json FROM checkpoints WHERE checkpoint_id = ?",
            (checkpoint_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None

        state_data = json.loads(row["state_json"])
        return SprintState(
            sprint_id=state_data["sprint_id"],
            project_id=state_data["project_id"],
            sprint_number=state_data.get("sprint_number", 1),
            goal=state_data["goal"],
            status=SprintStatus(state_data["status"]),
            tasks=[
                Task(
                    id=task_data["id"],
                    title=task_data["title"],
                    description=task_data["description"],
                    acceptance_criteria=task_data.get("acceptance_criteria", []),
                    assigned_to=task_data["assigned_to"],
                    priority=task_data.get("priority", 3),
                    status=task_data["status"],
                    dependencies=task_data.get("dependencies", []),
                )
                for task_data in state_data.get("tasks", [])
            ],
            messages=[],
            artifacts=[],
            metrics=SprintMetrics(**state_data.get("metrics", {})),
            error=state_data.get("error"),
        )

    async def get_latest_checkpoint(self, sprint_id: str) -> SprintState | None:
        """Get the most recent checkpoint for a sprint."""
        cursor = await self.db.conn.execute(
            "SELECT checkpoint_id FROM checkpoints WHERE sprint_id = ?"
            " ORDER BY created_at DESC LIMIT 1",
            (sprint_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return await self.load_checkpoint(row["checkpoint_id"])
