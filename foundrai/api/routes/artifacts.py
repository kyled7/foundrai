"""Artifact API routes."""

from __future__ import annotations

from fastapi import APIRouter

from foundrai.api.deps import get_db

router = APIRouter()


@router.get("/sprints/{sprint_id}/artifacts")
async def list_artifacts(sprint_id: str) -> dict:
    """List artifacts for a sprint."""
    db = await get_db()
    cursor = await db.conn.execute(
        "SELECT * FROM artifacts WHERE sprint_id = ?", (sprint_id,)
    )
    rows = await cursor.fetchall()
    artifacts = [
        {
            "artifact_id": r["artifact_id"],
            "sprint_id": r["sprint_id"],
            "task_id": r["task_id"],
            "agent_id": r["agent_id"],
            "artifact_type": r["artifact_type"],
            "file_path": r["file_path"],
            "size_bytes": r["size_bytes"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]
    return {"artifacts": artifacts, "total": len(artifacts)}
