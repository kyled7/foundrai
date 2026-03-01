"""Event and message API routes."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from foundrai.api.deps import get_db

router = APIRouter()


@router.get("/sprints/{sprint_id}/events")
async def list_events(sprint_id: str) -> dict:
    """List events for a sprint."""
    db = await get_db()
    # Verify sprint exists
    cursor = await db.conn.execute(
        "SELECT 1 FROM sprints WHERE sprint_id = ?", (sprint_id,)
    )
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Sprint not found")

    cursor = await db.conn.execute(
        """SELECT * FROM events
        WHERE json_extract(data_json, '$.sprint_id') = ?
        ORDER BY event_id DESC LIMIT 100""",
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
    return {"events": events, "total": len(events), "has_more": False}


@router.get("/sprints/{sprint_id}/messages")
async def list_messages(sprint_id: str) -> dict:
    """List agent messages for a sprint."""
    db = await get_db()
    cursor = await db.conn.execute(
        "SELECT 1 FROM sprints WHERE sprint_id = ?", (sprint_id,)
    )
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Sprint not found")

    cursor = await db.conn.execute(
        "SELECT * FROM messages WHERE sprint_id = ? ORDER BY timestamp DESC",
        (sprint_id,),
    )
    rows = await cursor.fetchall()
    messages = [
        {
            "message_id": r["message_id"],
            "type": r["type"],
            "from_agent": r["from_agent"],
            "to_agent": r["to_agent"],
            "content": r["content"],
            "metadata": json.loads(r["metadata_json"] or "{}"),
            "timestamp": r["timestamp"],
        }
        for r in rows
    ]
    return {"messages": messages, "total": len(messages)}
