"""Append-only event log for full audit trail."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from foundrai.persistence.database import Database


class EventLog:
    """Append-only event log."""

    def __init__(self, db: Database) -> None:
        self.db = db
        self._listeners: list[Callable] = []

    async def append(self, event_type: str, data: dict) -> int:
        """Append an event and return its ID."""
        cursor = await self.db.conn.execute(
            "INSERT INTO events (event_type, data_json) VALUES (?, ?)",
            (event_type, json.dumps(data, default=str)),
        )
        await self.db.conn.commit()

        # Notify listeners
        for listener in self._listeners:
            await listener(event_type, data)

        return cursor.lastrowid  # type: ignore[return-value]

    async def query(
        self,
        event_type: str | None = None,
        since: str | None = None,
        limit: int = 100,
        sprint_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query events with optional filters."""
        sql = "SELECT * FROM events WHERE 1=1"
        params: list[Any] = []

        if event_type:
            sql += " AND event_type = ?"
            params.append(event_type)

        if since:
            sql += " AND timestamp > ?"
            params.append(since)

        if sprint_id:
            sql += " AND json_extract(data_json, '$.sprint_id') = ?"
            params.append(sprint_id)

        sql += " ORDER BY event_id DESC LIMIT ?"
        params.append(limit)

        cursor = await self.db.conn.execute(sql, params)
        rows = await cursor.fetchall()

        return [
            {
                "event_id": row["event_id"],
                "event_type": row["event_type"],
                "data": json.loads(row["data_json"]),
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]

    def register_listener(self, callback: Callable) -> None:
        """Register a listener for events."""
        self._listeners.append(callback)

    def unregister_listener(self, callback: Callable) -> None:
        """Remove a listener."""
        self._listeners.remove(callback)
