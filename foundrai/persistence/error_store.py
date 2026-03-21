"""Error log persistence layer."""

from __future__ import annotations

from foundrai.models.error_log import ErrorLog
from foundrai.persistence.database import Database


class ErrorStore:
    """Manages error log records in the database."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def record_error(self, error: ErrorLog) -> int:
        """Record an error log entry. Returns the error_id."""
        cursor = await self.db.conn.execute(
            """INSERT INTO error_logs
               (task_id, sprint_id, agent_role, error_type, error_message,
                traceback, context_json, suggested_fix, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                error.task_id,
                error.sprint_id,
                error.agent_role,
                error.error_type,
                error.error_message,
                error.traceback,
                error.context_json,
                error.suggested_fix,
                error.timestamp,
            ),
        )
        await self.db.conn.commit()
        return cursor.lastrowid or 0

    async def get_task_errors(self, task_id: str) -> list[ErrorLog]:
        """Get all errors for a task."""
        cursor = await self.db.conn.execute(
            "SELECT * FROM error_logs WHERE task_id = ? ORDER BY timestamp",
            (task_id,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_error(r) for r in rows]

    async def get_sprint_errors(self, sprint_id: str) -> list[ErrorLog]:
        """Get all errors for a sprint."""
        cursor = await self.db.conn.execute(
            "SELECT * FROM error_logs WHERE sprint_id = ? ORDER BY timestamp DESC",
            (sprint_id,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_error(r) for r in rows]

    @staticmethod
    def classify_error(exception: Exception) -> str:
        """Auto-classify an exception into an error type."""
        msg = str(exception).lower()
        exc_type = type(exception).__name__.lower()

        if "rate" in msg or "rate_limit" in msg or "429" in msg:
            return "rate_limit"
        if (
            "context" in msg
            or "token" in msg
            and ("limit" in msg or "overflow" in msg or "exceed" in msg)
        ):
            return "context_overflow"
        if (
            "timeout" in msg
            or "timed out" in msg
            or exc_type in ("timeouterror", "asynciotimeouterror")
        ):
            return "timeout"
        if "tool" in msg or "function" in msg and "call" in msg:
            return "tool_error"
        if "parse" in msg or "json" in msg or "decode" in msg:
            return "parse_error"
        return "unknown"

    def _row_to_error(self, row: object) -> ErrorLog:
        """Convert a database row to an ErrorLog."""
        return ErrorLog(
            error_id=row["error_id"],  # type: ignore[index]
            task_id=row["task_id"],  # type: ignore[index]
            sprint_id=row["sprint_id"],  # type: ignore[index]
            agent_role=row["agent_role"],  # type: ignore[index]
            error_type=row["error_type"],  # type: ignore[index]
            error_message=row["error_message"],  # type: ignore[index]
            traceback=row["traceback"],  # type: ignore[index]
            context_json=row["context_json"],  # type: ignore[index]
            suggested_fix=row["suggested_fix"],  # type: ignore[index]
            timestamp=row["timestamp"],  # type: ignore[index]
        )
