"""Learning API routes."""

from __future__ import annotations

from fastapi import APIRouter

from foundrai.api.deps import get_db

router = APIRouter()


@router.get("/projects/{project_id}/learnings")
async def list_learnings(project_id: str) -> dict:
    """List learnings for a project."""
    db = await get_db()
    cursor = await db.conn.execute(
        "SELECT * FROM learnings WHERE project_id = ? ORDER BY created_at DESC",
        (project_id,),
    )
    rows = await cursor.fetchall()
    learnings = [
        {
            "learning_id": r["learning_id"],
            "project_id": r["project_id"],
            "sprint_id": r["sprint_id"],
            "content": r["content"],
            "category": r["category"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]
    return {"learnings": learnings, "total": len(learnings)}
