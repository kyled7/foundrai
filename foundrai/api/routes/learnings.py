"""Learning API routes."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from foundrai.api.deps import get_db, get_vector_memory

router = APIRouter()


class LearningUpdate(BaseModel):
    """Request model for updating learning content."""
    content: str = Field(..., min_length=1)


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


@router.get("/projects/{project_id}/learnings/vector")
async def get_vector_learnings(project_id: str) -> dict:
    """Get learnings from VectorMemory for a project."""
    db = await get_db()

    # Check project exists
    cursor = await db.conn.execute(
        "SELECT 1 FROM projects WHERE project_id = ?", (project_id,)
    )
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Project not found")

    # Get learnings from VectorMemory
    vm = await get_vector_memory()
    learnings_list = await vm.get_all_learnings(project_id=project_id)

    learnings = [
        {
            "learning_id": learning.id,
            "project_id": learning.project_id,
            "sprint_id": learning.sprint_id,
            "content": learning.content,
            "category": learning.category,
            "timestamp": learning.timestamp,
        }
        for learning in learnings_list
    ]
    return {"learnings": learnings, "total": len(learnings)}


@router.put("/learnings/{learning_id}")
async def update_learning(learning_id: str, update: LearningUpdate) -> dict:
    """Update a learning's content."""
    db = await get_db()

    # Verify learning exists
    cursor = await db.conn.execute(
        "SELECT * FROM learnings WHERE learning_id = ?", (learning_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Learning not found")

    # Update learning content
    now = datetime.now(timezone.utc).isoformat()
    await db.conn.execute(
        "UPDATE learnings SET content = ?, updated_at = ? WHERE learning_id = ?",
        (update.content, now, learning_id)
    )
    await db.conn.commit()

    # Return updated learning
    cursor = await db.conn.execute(
        "SELECT * FROM learnings WHERE learning_id = ?", (learning_id,)
    )
    row = await cursor.fetchone()

    return {
        "learning_id": row["learning_id"],
        "project_id": row["project_id"],
        "sprint_id": row["sprint_id"],
        "content": row["content"],
        "category": row["category"],
        "created_at": row["created_at"],
        "updated_at": row.get("updated_at"),
    }
