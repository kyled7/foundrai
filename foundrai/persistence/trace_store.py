"""Decision trace persistence layer with zlib compression."""

from __future__ import annotations

import json
import zlib

from foundrai.models.decision_trace import DecisionTrace
from foundrai.persistence.database import Database


class TraceStore:
    """Manages decision trace records in the database."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def record_trace(self, trace: DecisionTrace) -> int:
        """Record a decision trace. Returns the trace_id."""
        prompt_compressed = zlib.compress(trace.prompt.encode("utf-8")) if trace.prompt else None
        response_compressed = zlib.compress(trace.response.encode("utf-8")) if trace.response else None

        cursor = await self.db.conn.execute(
            """INSERT INTO decision_traces
               (event_id, task_id, sprint_id, agent_role, model,
                prompt_compressed, response_compressed, thinking,
                tool_calls_json, tokens_used, cost_usd, duration_ms, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                trace.event_id,
                trace.task_id,
                trace.sprint_id,
                trace.agent_role,
                trace.model,
                prompt_compressed,
                response_compressed,
                trace.thinking,
                json.dumps(trace.tool_calls),
                trace.tokens_used,
                trace.cost_usd,
                trace.duration_ms,
                trace.timestamp,
            ),
        )
        await self.db.conn.commit()
        return cursor.lastrowid or 0

    async def get_task_traces(self, task_id: str) -> list[DecisionTrace]:
        """Get all traces for a task."""
        cursor = await self.db.conn.execute(
            "SELECT * FROM decision_traces WHERE task_id = ? ORDER BY timestamp",
            (task_id,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_trace(r) for r in rows]

    async def get_sprint_traces(self, sprint_id: str, limit: int = 50) -> list[DecisionTrace]:
        """Get traces for a sprint."""
        cursor = await self.db.conn.execute(
            "SELECT * FROM decision_traces WHERE sprint_id = ? ORDER BY timestamp DESC LIMIT ?",
            (sprint_id, limit),
        )
        rows = await cursor.fetchall()
        return [self._row_to_trace(r) for r in rows]

    async def get_trace(self, trace_id: int) -> DecisionTrace | None:
        """Get a single trace by ID with full decompressed content."""
        cursor = await self.db.conn.execute(
            "SELECT * FROM decision_traces WHERE trace_id = ?",
            (trace_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return self._row_to_trace(row)

    def _row_to_trace(self, row: object) -> DecisionTrace:
        """Convert a database row to a DecisionTrace."""
        prompt = ""
        if row["prompt_compressed"]:  # type: ignore[index]
            prompt = zlib.decompress(row["prompt_compressed"]).decode("utf-8")  # type: ignore[index]

        response = ""
        if row["response_compressed"]:  # type: ignore[index]
            response = zlib.decompress(row["response_compressed"]).decode("utf-8")  # type: ignore[index]

        tool_calls = []
        if row["tool_calls_json"]:  # type: ignore[index]
            tool_calls = json.loads(row["tool_calls_json"])  # type: ignore[index]

        return DecisionTrace(
            trace_id=row["trace_id"],  # type: ignore[index]
            event_id=row["event_id"],  # type: ignore[index]
            task_id=row["task_id"],  # type: ignore[index]
            sprint_id=row["sprint_id"],  # type: ignore[index]
            agent_role=row["agent_role"],  # type: ignore[index]
            model=row["model"],  # type: ignore[index]
            prompt=prompt,
            response=response,
            thinking=row["thinking"],  # type: ignore[index]
            tool_calls=tool_calls,
            tokens_used=row["tokens_used"],  # type: ignore[index]
            cost_usd=row["cost_usd"],  # type: ignore[index]
            duration_ms=row["duration_ms"],  # type: ignore[index]
            timestamp=row["timestamp"],  # type: ignore[index]
        )
