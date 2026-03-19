"""Agent health and quality monitoring persistence layer."""

from __future__ import annotations

import json
from datetime import datetime

from foundrai.models.agent_health import AgentHealth, AgentHealthMetrics
from foundrai.models.enums import AgentRoleName
from foundrai.persistence.database import Database


class AgentHealthStore:
    """Manages agent health metrics in the database."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def calculate_health_score(
        self,
        agent_role: AgentRoleName | str,
        project_id: str,
        sprint_id: str | None = None,
    ) -> AgentHealth:
        """Calculate and save agent health metrics.

        Args:
            agent_role: The role of the agent to evaluate
            project_id: The project context
            sprint_id: Optional sprint filter (None = all sprints in project)

        Returns:
            AgentHealth object with calculated metrics and recommendations
        """
        metrics = await self._calculate_metrics(agent_role, project_id, sprint_id)

        # Calculate overall health score (weighted average)
        # Weights: completion (30%), quality (30%), cost_efficiency (20%), failure_rate (20%)
        health_score = (
            metrics.completion_rate * 0.3
            + metrics.quality_score * 0.3
            + self._normalize_cost_efficiency(metrics.cost_efficiency) * 0.2
            + (100 - metrics.failure_rate) * 0.2
        )

        # Determine status
        if health_score >= 80:
            status = "healthy"
        elif health_score >= 50:
            status = "warning"
        else:
            status = "unhealthy"

        # Generate recommendations
        recommendations = self._generate_recommendations(metrics)

        # Create AgentHealth object
        agent_health = AgentHealth(
            agent_role=agent_role,  # type: ignore[arg-type]
            project_id=project_id,
            sprint_id=sprint_id,
            health_score=round(health_score, 2),
            status=status,
            metrics=metrics,
            recommendations=recommendations,
            timestamp=datetime.utcnow(),
        )

        # Save to database
        await self._save_health_record(agent_health)

        return agent_health

    async def _calculate_metrics(
        self,
        agent_role: AgentRoleName | str,
        project_id: str,
        sprint_id: str | None = None,
    ) -> AgentHealthMetrics:
        """Calculate raw metrics from database."""
        # Build query conditions
        if sprint_id:
            task_filter = "assigned_to = ? AND sprint_id = ?"
            task_params = (str(agent_role), sprint_id)
        else:
            # Get all sprints for this project
            sprint_cursor = await self.db.conn.execute(
                "SELECT sprint_id FROM sprints WHERE project_id = ?",
                (project_id,),
            )
            sprint_rows = await sprint_cursor.fetchall()
            sprint_ids = [row["sprint_id"] for row in sprint_rows]

            if not sprint_ids:
                return AgentHealthMetrics()

            placeholders = ",".join("?" * len(sprint_ids))
            task_filter = f"assigned_to = ? AND sprint_id IN ({placeholders})"
            task_params = (str(agent_role), *sprint_ids)

        # Get task statistics
        task_cursor = await self.db.conn.execute(
            f"""SELECT
                COUNT(*) as total_tasks,
                SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as completed_tasks,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tasks
            FROM tasks WHERE {task_filter}""",
            task_params,
        )
        task_row = await task_cursor.fetchone()

        total_tasks = task_row["total_tasks"] or 0
        completed_tasks = task_row["completed_tasks"] or 0
        failed_tasks = task_row["failed_tasks"] or 0

        # Calculate rates
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
        failure_rate = (failed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0

        # Get quality score from reviews
        quality_score = await self._calculate_quality_score(task_filter, task_params)

        # Get token usage and cost
        token_cursor = await self.db.conn.execute(
            f"""SELECT
                COALESCE(SUM(total_tokens), 0) as total_tokens,
                COALESCE(SUM(cost_usd), 0.0) as total_cost
            FROM token_usage
            WHERE agent_role = ? AND project_id = ?""" +
            (f" AND sprint_id = ?" if sprint_id else ""),
            (str(agent_role), project_id, sprint_id) if sprint_id else (str(agent_role), project_id),
        )
        token_row = await token_cursor.fetchone()

        total_tokens = token_row["total_tokens"] or 0
        total_cost = token_row["total_cost"] or 0.0

        # Calculate cost efficiency (tokens per completed task)
        cost_efficiency = (total_tokens / completed_tasks) if completed_tasks > 0 else 0.0

        # Calculate average execution time
        avg_execution_time = await self._calculate_avg_execution_time(task_filter, task_params)

        return AgentHealthMetrics(
            completion_rate=round(completion_rate, 2),
            quality_score=round(quality_score, 2),
            cost_efficiency=round(cost_efficiency, 2),
            avg_execution_time=round(avg_execution_time, 2),
            failure_rate=round(failure_rate, 2),
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            total_tokens=total_tokens,
            total_cost_usd=round(total_cost, 2),
        )

    async def _calculate_quality_score(self, task_filter: str, task_params: tuple) -> float:
        """Calculate quality score based on review pass rate."""
        cursor = await self.db.conn.execute(
            f"""SELECT
                COUNT(*) as total_reviews,
                SUM(CASE WHEN json_extract(review_json, '$.passed') = 1 THEN 1 ELSE 0 END) as passed_reviews
            FROM tasks
            WHERE {task_filter} AND review_json IS NOT NULL""",
            task_params,
        )
        row = await cursor.fetchone()

        total_reviews = row["total_reviews"] or 0
        passed_reviews = row["passed_reviews"] or 0

        if total_reviews == 0:
            return 0.0

        return (passed_reviews / total_reviews) * 100

    async def _calculate_avg_execution_time(self, task_filter: str, task_params: tuple) -> float:
        """Calculate average task execution time in seconds."""
        cursor = await self.db.conn.execute(
            f"""SELECT
                AVG(
                    CASE
                        WHEN updated_at IS NOT NULL AND created_at IS NOT NULL
                        THEN (julianday(updated_at) - julianday(created_at)) * 86400
                        ELSE 0
                    END
                ) as avg_time
            FROM tasks
            WHERE {task_filter} AND status = 'done'""",
            task_params,
        )
        row = await cursor.fetchone()
        return row["avg_time"] or 0.0

    def _normalize_cost_efficiency(self, cost_efficiency: float) -> float:
        """Normalize cost efficiency to 0-100 scale (lower is better).

        Using inverse exponential scaling:
        - 0 tokens/task = 100 (perfect, but unlikely)
        - 5000 tokens/task = 50 (average)
        - 10000+ tokens/task = 0-25 (inefficient)
        """
        if cost_efficiency == 0:
            return 100.0

        # Inverse exponential: score decreases as tokens increase
        # Target: 5000 tokens = 50 score
        target_tokens = 5000
        normalized = 100 * (target_tokens / (cost_efficiency + target_tokens))
        return max(0.0, min(100.0, normalized))

    def _generate_recommendations(self, metrics: AgentHealthMetrics) -> list[str]:
        """Generate actionable recommendations based on metrics."""
        recommendations = []

        # Completion rate recommendations
        if metrics.completion_rate < 50:
            recommendations.append(
                "Low completion rate. Consider reassigning tasks or checking for blockers."
            )
        elif metrics.completion_rate < 75:
            recommendations.append(
                "Moderate completion rate. Review task complexity and agent capacity."
            )

        # Quality score recommendations
        if metrics.quality_score < 50 and metrics.total_tasks > 0:
            recommendations.append(
                "Low quality score. Review failed QA checks and consider model upgrade."
            )
        elif metrics.quality_score < 75 and metrics.total_tasks > 0:
            recommendations.append(
                "Moderate quality score. Analyze review feedback for improvement opportunities."
            )

        # Cost efficiency recommendations
        if metrics.cost_efficiency > 10000:
            recommendations.append(
                "High token usage per task. Consider using a smaller model or optimizing prompts."
            )
        elif metrics.cost_efficiency > 7500:
            recommendations.append(
                "Above-average token usage. Monitor prompt efficiency and context size."
            )

        # Failure rate recommendations
        if metrics.failure_rate > 25:
            recommendations.append(
                "High failure rate. Check error logs for patterns and adjust agent configuration."
            )
        elif metrics.failure_rate > 10:
            recommendations.append(
                "Elevated failure rate. Review error types and consider timeout adjustments."
            )

        # Execution time recommendations
        if metrics.avg_execution_time > 600:  # 10 minutes
            recommendations.append(
                "Long execution times. Consider breaking down tasks or optimizing workflows."
            )

        # If everything is good
        if not recommendations:
            recommendations.append("Agent performing well. No immediate actions required.")

        return recommendations

    async def _save_health_record(self, health: AgentHealth) -> int:
        """Save health record to database. Returns health_id."""
        cursor = await self.db.conn.execute(
            """INSERT INTO agent_health_metrics
               (agent_role, project_id, sprint_id, health_score, status,
                metrics_json, recommendations_json, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(health.agent_role),
                health.project_id,
                health.sprint_id,
                health.health_score,
                health.status,
                health.metrics.model_dump_json(),
                json.dumps(health.recommendations),
                health.timestamp.isoformat(),
            ),
        )
        await self.db.conn.commit()
        return cursor.lastrowid or 0

    async def get_agent_health(
        self,
        agent_role: AgentRoleName | str,
        project_id: str,
        sprint_id: str | None = None,
    ) -> AgentHealth | None:
        """Get the most recent health record for an agent."""
        cursor = await self.db.conn.execute(
            """SELECT * FROM agent_health_metrics
               WHERE agent_role = ? AND project_id = ?""" +
            (" AND sprint_id = ?" if sprint_id else " AND sprint_id IS NULL") +
            " ORDER BY timestamp DESC LIMIT 1",
            (str(agent_role), project_id, sprint_id) if sprint_id else (str(agent_role), project_id),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return self._row_to_health(row)

    async def get_project_health(self, project_id: str) -> list[AgentHealth]:
        """Get the most recent health records for all agents in a project."""
        # Get the latest health record for each agent
        cursor = await self.db.conn.execute(
            """SELECT * FROM agent_health_metrics
               WHERE project_id = ?
               AND sprint_id IS NULL
               AND health_id IN (
                   SELECT MAX(health_id)
                   FROM agent_health_metrics
                   WHERE project_id = ? AND sprint_id IS NULL
                   GROUP BY agent_role
               )
               ORDER BY agent_role""",
            (project_id, project_id),
        )
        rows = await cursor.fetchall()
        return [self._row_to_health(r) for r in rows]

    async def get_sprint_health(self, sprint_id: str) -> list[AgentHealth]:
        """Get the most recent health records for all agents in a sprint."""
        cursor = await self.db.conn.execute(
            """SELECT * FROM agent_health_metrics
               WHERE sprint_id = ?
               AND health_id IN (
                   SELECT MAX(health_id)
                   FROM agent_health_metrics
                   WHERE sprint_id = ?
                   GROUP BY agent_role
               )
               ORDER BY agent_role""",
            (sprint_id, sprint_id),
        )
        rows = await cursor.fetchall()
        return [self._row_to_health(r) for r in rows]

    def _row_to_health(self, row: object) -> AgentHealth:
        """Convert a database row to an AgentHealth object."""
        metrics_data = json.loads(row["metrics_json"])  # type: ignore[index]
        recommendations = json.loads(row["recommendations_json"])  # type: ignore[index]

        return AgentHealth(
            agent_role=row["agent_role"],  # type: ignore[index,arg-type]
            project_id=row["project_id"],  # type: ignore[index]
            sprint_id=row["sprint_id"],  # type: ignore[index]
            health_score=row["health_score"],  # type: ignore[index]
            status=row["status"],  # type: ignore[index]
            metrics=AgentHealthMetrics(**metrics_data),
            recommendations=recommendations,
            timestamp=datetime.fromisoformat(row["timestamp"]),  # type: ignore[index]
        )
