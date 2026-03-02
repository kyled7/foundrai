"""Event replay API routes."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from foundrai.api.deps import get_db

router = APIRouter()


@router.get("/sprints/{sprint_id}/replay")
async def get_replay_events(sprint_id: str) -> dict:
    """Get all events for a sprint sorted by timestamp for replay."""
    db = await get_db()
    cursor = await db.conn.execute(
        """SELECT * FROM events
        WHERE json_extract(data_json, '$.sprint_id') = ?
        ORDER BY event_id ASC""",
        (sprint_id,),
    )
    rows = await cursor.fetchall()
    events = [
        {
            "event_id": r["event_id"],
            "event_type": r["event_type"],
            "data": json.loads(r["data_json"]),
            "timestamp": r["timestamp"],
        }
        for r in rows
    ]
    return {"events": events, "total": len(events)}
