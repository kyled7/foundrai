"""Token usage persistence layer."""

from __future__ import annotations

from foundrai.models.token_usage import TokenUsage
from foundrai.persistence.database import Database


class TokenStore:
    """Manages token usage records in the database."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def record_usage(self, usage: TokenUsage) -> int:
        """Record a token usage entry. Returns the usage_id."""
        cursor = await self.db.conn.execute(
            """INSERT INTO token_usage
               (task_id, sprint_id, project_id, agent_role, model,
                prompt_tokens, completion_tokens, total_tokens, cost_usd, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                usage.task_id,
                usage.sprint_id,
                usage.project_id,
                usage.agent_role,
                usage.model,
                usage.prompt_tokens,
                usage.completion_tokens,
                usage.total_tokens,
                usage.cost_usd,
                usage.timestamp,
            ),
        )
        await self.db.conn.commit()

        # Broadcast cost update event via WebSocket
        # Lazy import to avoid circular dependency
        try:
            from foundrai.api.app import ws_manager
            await ws_manager.broadcast(
                usage.sprint_id,
                "cost_updated",
                {
                    "sprint_id": usage.sprint_id,
                    "task_id": usage.task_id,
                    "cost_usd": usage.cost_usd,
                    "agent_role": usage.agent_role,
                },
            )
        except ImportError:
            # WebSocket manager not available (e.g., in tests)
            pass

        return cursor.lastrowid or 0

    async def get_task_usage(self, task_id: str) -> list[TokenUsage]:
        """Get all token usage records for a task."""
        cursor = await self.db.conn.execute(
            "SELECT * FROM token_usage WHERE task_id = ? ORDER BY timestamp",
            (task_id,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_usage(r) for r in rows]

    async def get_sprint_usage(self, sprint_id: str) -> dict:
        """Get aggregated token usage for a sprint."""
        cursor = await self.db.conn.execute(
            """SELECT COALESCE(SUM(total_tokens), 0) as total_tokens,
                      COALESCE(SUM(cost_usd), 0.0) as total_cost,
                      COUNT(*) as call_count
               FROM token_usage WHERE sprint_id = ?""",
            (sprint_id,),
        )
        row = await cursor.fetchone()
        result: dict = {
            "sprint_id": sprint_id,
            "total_tokens": row["total_tokens"],
            "total_cost": row["total_cost"],
            "call_count": row["call_count"],
            "by_agent": {},
        }

        cursor = await self.db.conn.execute(
            """SELECT agent_role,
                      COALESCE(SUM(total_tokens), 0) as total_tokens,
                      COALESCE(SUM(cost_usd), 0.0) as total_cost,
                      COUNT(*) as call_count
               FROM token_usage WHERE sprint_id = ?
               GROUP BY agent_role""",
            (sprint_id,),
        )
        for row in await cursor.fetchall():
            result["by_agent"][row["agent_role"]] = {
                "total_tokens": row["total_tokens"],
                "total_cost": row["total_cost"],
                "call_count": row["call_count"],
            }
        return result

    async def get_agent_usage(self, project_id: str, agent_role: str) -> dict:
        """Get aggregated token usage for an agent in a project."""
        cursor = await self.db.conn.execute(
            """SELECT COALESCE(SUM(total_tokens), 0) as total_tokens,
                      COALESCE(SUM(cost_usd), 0.0) as total_cost,
                      COUNT(*) as call_count
               FROM token_usage WHERE project_id = ? AND agent_role = ?""",
            (project_id, agent_role),
        )
        row = await cursor.fetchone()
        return {
            "project_id": project_id,
            "agent_role": agent_role,
            "total_tokens": row["total_tokens"],
            "total_cost": row["total_cost"],
            "call_count": row["call_count"],
        }

    async def get_project_usage(self, project_id: str) -> dict:
        """Get aggregated token usage for a project."""
        cursor = await self.db.conn.execute(
            """SELECT COALESCE(SUM(total_tokens), 0) as total_tokens,
                      COALESCE(SUM(cost_usd), 0.0) as total_cost,
                      COUNT(*) as call_count
               FROM token_usage WHERE project_id = ?""",
            (project_id,),
        )
        row = await cursor.fetchone()
        result: dict = {
            "project_id": project_id,
            "total_tokens": row["total_tokens"],
            "total_cost": row["total_cost"],
            "call_count": row["call_count"],
            "by_agent": {},
            "by_sprint": {},
        }

        cursor = await self.db.conn.execute(
            """SELECT agent_role,
                      COALESCE(SUM(total_tokens), 0) as total_tokens,
                      COALESCE(SUM(cost_usd), 0.0) as total_cost,
                      COUNT(*) as call_count
               FROM token_usage WHERE project_id = ?
               GROUP BY agent_role""",
            (project_id,),
        )
        for row in await cursor.fetchall():
            result["by_agent"][row["agent_role"]] = {
                "total_tokens": row["total_tokens"],
                "total_cost": row["total_cost"],
                "call_count": row["call_count"],
            }

        cursor = await self.db.conn.execute(
            """SELECT sprint_id,
                      COALESCE(SUM(total_tokens), 0) as total_tokens,
                      COALESCE(SUM(cost_usd), 0.0) as total_cost,
                      COUNT(*) as call_count
               FROM token_usage WHERE project_id = ?
               GROUP BY sprint_id""",
            (project_id,),
        )
        for row in await cursor.fetchall():
            result["by_sprint"][row["sprint_id"]] = {
                "total_tokens": row["total_tokens"],
                "total_cost": row["total_cost"],
                "call_count": row["call_count"],
            }
        return result

    async def get_sprint_spent(self, sprint_id: str) -> float:
        """Get total USD spent for a sprint."""
        cursor = await self.db.conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0.0) as total FROM token_usage WHERE sprint_id = ?",
            (sprint_id,),
        )
        row = await cursor.fetchone()
        return float(row["total"])

    async def get_agent_spent(self, sprint_id: str, agent_role: str) -> float:
        """Get total USD spent by an agent in a sprint."""
        cursor = await self.db.conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0.0) as total "
            "FROM token_usage WHERE sprint_id = ? AND agent_role = ?",
            (sprint_id, agent_role),
        )
        row = await cursor.fetchone()
        return float(row["total"])

    def _row_to_usage(self, row: object) -> TokenUsage:
        """Convert a database row to a TokenUsage object."""
        return TokenUsage(
            usage_id=row["usage_id"],  # type: ignore[index]
            task_id=row["task_id"],  # type: ignore[index]
            sprint_id=row["sprint_id"],  # type: ignore[index]
            project_id=row["project_id"],  # type: ignore[index]
            agent_role=row["agent_role"],  # type: ignore[index]
            model=row["model"],  # type: ignore[index]
            prompt_tokens=row["prompt_tokens"],  # type: ignore[index]
            completion_tokens=row["completion_tokens"],  # type: ignore[index]
            total_tokens=row["total_tokens"],  # type: ignore[index]
            cost_usd=row["cost_usd"],  # type: ignore[index]
            timestamp=row["timestamp"],  # type: ignore[index]
        )
