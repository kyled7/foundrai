"""Performance data persistence layer for model recommendations."""

from __future__ import annotations

from foundrai.models.enums import AgentRoleName
from foundrai.models.recommendation import PerformanceMetrics
from foundrai.persistence.database import Database


class RecommendationStore:
    """Manages performance data queries for model recommendations."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_agent_performance(
        self, project_id: str, agent_role: AgentRoleName
    ) -> list[PerformanceMetrics]:
        """Get performance metrics for all models used by an agent role in a project.

        Returns a list of PerformanceMetrics, one for each model that the agent has used.
        """
        cursor = await self.db.conn.execute(
            """SELECT
                   model,
                   agent_role,
                   COUNT(DISTINCT task_id) as total_tasks,
                   COALESCE(SUM(total_tokens), 0) as total_tokens,
                   COALESCE(SUM(cost_usd), 0.0) as total_cost
               FROM token_usage
               WHERE project_id = ? AND agent_role = ?
               GROUP BY model, agent_role""",
            (project_id, agent_role),
        )
        rows = await cursor.fetchall()

        metrics_list = []
        for row in rows:
            # Get task success/failure data
            task_cursor = await self.db.conn.execute(
                """SELECT
                       COUNT(*) as completed_tasks,
                       SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_tasks
                   FROM tasks
                   WHERE sprint_id IN (
                       SELECT DISTINCT sprint_id
                       FROM token_usage
                       WHERE project_id = ? AND agent_role = ? AND model = ?
                   )
                   AND assigned_to = ?
                   AND status IN ('completed', 'failed')""",
                (project_id, agent_role, row["model"], agent_role),
            )
            task_row = await task_cursor.fetchone()

            total_tasks = task_row["completed_tasks"] or 0
            successful_tasks = task_row["successful_tasks"] or 0
            failed_tasks = total_tasks - successful_tasks

            # Calculate averages
            avg_tokens = float(row["total_tokens"]) / total_tasks if total_tasks > 0 else 0.0
            avg_cost = float(row["total_cost"]) / total_tasks if total_tasks > 0 else 0.0
            success_rate = (successful_tasks / total_tasks * 100.0) if total_tasks > 0 else 0.0

            metrics = PerformanceMetrics(
                model=row["model"],
                agent_role=agent_role,
                success_rate=success_rate,
                avg_tokens_per_task=avg_tokens,
                avg_cost_per_task=avg_cost,
                total_tasks=total_tasks,
                successful_tasks=successful_tasks,
                failed_tasks=failed_tasks,
                total_tokens=row["total_tokens"],
                total_cost_usd=row["total_cost"],
                project_id=project_id,
            )
            metrics_list.append(metrics)

        return metrics_list

    async def get_model_performance(
        self, project_id: str, model: str
    ) -> dict[str, PerformanceMetrics]:
        """Get performance metrics for a specific model across all agent roles.

        Returns a dict mapping agent_role to PerformanceMetrics.
        """
        cursor = await self.db.conn.execute(
            """SELECT
                   model,
                   agent_role,
                   COUNT(DISTINCT task_id) as total_tasks,
                   COALESCE(SUM(total_tokens), 0) as total_tokens,
                   COALESCE(SUM(cost_usd), 0.0) as total_cost
               FROM token_usage
               WHERE project_id = ? AND model = ?
               GROUP BY model, agent_role""",
            (project_id, model),
        )
        rows = await cursor.fetchall()

        metrics_by_role: dict[str, PerformanceMetrics] = {}
        for row in rows:
            agent_role = row["agent_role"]

            # Get task success/failure data
            task_cursor = await self.db.conn.execute(
                """SELECT
                       COUNT(*) as completed_tasks,
                       SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_tasks
                   FROM tasks
                   WHERE sprint_id IN (
                       SELECT DISTINCT sprint_id
                       FROM token_usage
                       WHERE project_id = ? AND agent_role = ? AND model = ?
                   )
                   AND assigned_to = ?
                   AND status IN ('completed', 'failed')""",
                (project_id, agent_role, model, agent_role),
            )
            task_row = await task_cursor.fetchone()

            total_tasks = task_row["completed_tasks"] or 0
            successful_tasks = task_row["successful_tasks"] or 0
            failed_tasks = total_tasks - successful_tasks

            # Calculate averages
            avg_tokens = float(row["total_tokens"]) / total_tasks if total_tasks > 0 else 0.0
            avg_cost = float(row["total_cost"]) / total_tasks if total_tasks > 0 else 0.0
            success_rate = (successful_tasks / total_tasks * 100.0) if total_tasks > 0 else 0.0

            metrics = PerformanceMetrics(
                model=model,
                agent_role=agent_role,  # type: ignore[arg-type]
                success_rate=success_rate,
                avg_tokens_per_task=avg_tokens,
                avg_cost_per_task=avg_cost,
                total_tasks=total_tasks,
                successful_tasks=successful_tasks,
                failed_tasks=failed_tasks,
                total_tokens=row["total_tokens"],
                total_cost_usd=row["total_cost"],
                project_id=project_id,
            )
            metrics_by_role[agent_role] = metrics

        return metrics_by_role

    async def get_sprint_performance(self, sprint_id: str) -> dict[str, list[PerformanceMetrics]]:
        """Get performance metrics for all agents in a sprint, grouped by agent role.

        Returns a dict mapping agent_role to list of PerformanceMetrics (one per model).
        """
        cursor = await self.db.conn.execute(
            """SELECT
                   model,
                   agent_role,
                   COUNT(DISTINCT task_id) as total_tasks,
                   COALESCE(SUM(total_tokens), 0) as total_tokens,
                   COALESCE(SUM(cost_usd), 0.0) as total_cost
               FROM token_usage
               WHERE sprint_id = ?
               GROUP BY agent_role, model""",
            (sprint_id,),
        )
        rows = await cursor.fetchall()

        metrics_by_role: dict[str, list[PerformanceMetrics]] = {}
        for row in rows:
            agent_role = row["agent_role"]

            # Get task success/failure data for this agent/model combo
            task_cursor = await self.db.conn.execute(
                """SELECT
                       COUNT(*) as completed_tasks,
                       SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_tasks
                   FROM tasks
                   WHERE sprint_id = ?
                   AND assigned_to = ?
                   AND status IN ('completed', 'failed')""",
                (sprint_id, agent_role),
            )
            task_row = await task_cursor.fetchone()

            total_tasks = task_row["completed_tasks"] or 0
            successful_tasks = task_row["successful_tasks"] or 0
            failed_tasks = total_tasks - successful_tasks

            # Calculate averages
            avg_tokens = float(row["total_tokens"]) / total_tasks if total_tasks > 0 else 0.0
            avg_cost = float(row["total_cost"]) / total_tasks if total_tasks > 0 else 0.0
            success_rate = (successful_tasks / total_tasks * 100.0) if total_tasks > 0 else 0.0

            metrics = PerformanceMetrics(
                model=row["model"],
                agent_role=agent_role,  # type: ignore[arg-type]
                success_rate=success_rate,
                avg_tokens_per_task=avg_tokens,
                avg_cost_per_task=avg_cost,
                total_tasks=total_tasks,
                successful_tasks=successful_tasks,
                failed_tasks=failed_tasks,
                total_tokens=row["total_tokens"],
                total_cost_usd=row["total_cost"],
                sprint_id=sprint_id,
            )

            if agent_role not in metrics_by_role:
                metrics_by_role[agent_role] = []
            metrics_by_role[agent_role].append(metrics)

        return metrics_by_role

    async def get_project_summary(self, project_id: str) -> dict:
        """Get aggregated performance summary for a project.

        Returns overall project statistics across all agents and models.
        """
        cursor = await self.db.conn.execute(
            """SELECT
                   COUNT(DISTINCT agent_role) as agent_count,
                   COUNT(DISTINCT model) as model_count,
                   COUNT(DISTINCT task_id) as total_tasks,
                   COALESCE(SUM(total_tokens), 0) as total_tokens,
                   COALESCE(SUM(cost_usd), 0.0) as total_cost
               FROM token_usage
               WHERE project_id = ?""",
            (project_id,),
        )
        row = await cursor.fetchone()

        # Get completed vs failed tasks
        task_cursor = await self.db.conn.execute(
            """SELECT
                   COUNT(*) as all_tasks,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                   SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tasks
               FROM tasks
               WHERE sprint_id IN (
                   SELECT DISTINCT sprint_id FROM sprints WHERE project_id = ?
               )
               AND status IN ('completed', 'failed')""",
            (project_id,),
        )
        task_row = await task_cursor.fetchone()

        return {
            "project_id": project_id,
            "agent_count": row["agent_count"] or 0,
            "model_count": row["model_count"] or 0,
            "total_tasks": task_row["all_tasks"] or 0,
            "completed_tasks": task_row["completed_tasks"] or 0,
            "failed_tasks": task_row["failed_tasks"] or 0,
            "total_tokens": row["total_tokens"] or 0,
            "total_cost": row["total_cost"] or 0.0,
            "avg_cost_per_task": (
                float(row["total_cost"]) / task_row["all_tasks"]
                if task_row["all_tasks"] and task_row["all_tasks"] > 0
                else 0.0
            ),
        }

    async def get_best_performing_model(
        self, project_id: str, agent_role: AgentRoleName
    ) -> str | None:
        """Get the best performing model for an agent role based on success rate.

        Returns the model name with the highest success rate, or None if no data.
        """
        metrics_list = await self.get_agent_performance(project_id, agent_role)

        if not metrics_list:
            return None

        # Filter out models with insufficient data (less than 3 tasks)
        viable_metrics = [m for m in metrics_list if m.total_tasks >= 3]

        if not viable_metrics:
            # Fall back to any model with data
            viable_metrics = metrics_list

        # Sort by success rate (descending), then by total tasks (descending)
        best = max(
            viable_metrics,
            key=lambda m: (m.success_rate, m.total_tasks),
        )

        return best.model

    async def get_most_cost_efficient_model(
        self, project_id: str, agent_role: AgentRoleName
    ) -> str | None:
        """Get the most cost-efficient model for an agent role.

        Returns the model with lowest avg_cost_per_task among successful models.
        """
        metrics_list = await self.get_agent_performance(project_id, agent_role)

        if not metrics_list:
            return None

        # Filter for models with reasonable success rate (>70%) and sufficient data
        viable_metrics = [m for m in metrics_list if m.success_rate >= 70.0 and m.total_tasks >= 3]

        if not viable_metrics:
            # Fall back to best success rate if no models meet threshold
            return await self.get_best_performing_model(project_id, agent_role)

        # Find cheapest among viable models
        most_efficient = min(viable_metrics, key=lambda m: m.avg_cost_per_task)

        return most_efficient.model
