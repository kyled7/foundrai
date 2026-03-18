"""Approval API routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from foundrai.api.deps import get_db

router = APIRouter()


class ApprovalDecision(BaseModel):
    comment: str = ""


@router.get("/sprints/{sprint_id}/approvals")
async def list_approvals(sprint_id: str) -> dict:
    """List approvals for a sprint."""
    db = await get_db()
    cursor = await db.conn.execute(
        "SELECT * FROM approvals WHERE sprint_id = ? ORDER BY created_at DESC",
        (sprint_id,),
    )
    rows = await cursor.fetchall()
    approvals = [
        {
            "approval_id": r["approval_id"],
            "sprint_id": r["sprint_id"],
            "agent_id": r["agent_id"],
            "action_type": r["action_type"],
            "title": r["title"],
            "status": r["status"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]
    pending = sum(1 for a in approvals if a["status"] == "pending")
    return {"approvals": approvals, "pending_count": pending, "total": len(approvals)}


@router.get("/approvals/{approval_id}")
async def get_approval(approval_id: str) -> dict:
    """Get approval details."""
    db = await get_db()
    cursor = await db.conn.execute(
        "SELECT * FROM approvals WHERE approval_id = ?", (approval_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Approval not found")

    return {
        "approval_id": row["approval_id"],
        "sprint_id": row["sprint_id"],
        "agent_id": row["agent_id"],
        "action_type": row["action_type"],
        "title": row["title"],
        "status": row["status"],
        "comment": row["comment"],
        "created_at": row["created_at"],
        "resolved_at": row.get("resolved_at"),
    }


@router.post("/approvals/{approval_id}/approve")
async def approve(approval_id: str, body: ApprovalDecision) -> dict:
    """Approve a pending approval."""
    db = await get_db()
    cursor = await db.conn.execute(
        "SELECT * FROM approvals WHERE approval_id = ?", (approval_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Approval not found")
    if row["status"] != "pending":
        raise HTTPException(status_code=409, detail="Approval already resolved")

    resolved_at = datetime.utcnow().isoformat()
    await db.conn.execute(
        "UPDATE approvals SET status = 'approved', comment = ?,"
        " resolved_at = ? WHERE approval_id = ?",
        (body.comment, resolved_at, approval_id),
    )
    await db.conn.commit()
    return {"approval_id": approval_id, "status": "approved", "resolved_at": resolved_at}


@router.post("/approvals/{approval_id}/reject")
async def reject(approval_id: str, body: ApprovalDecision) -> dict:
    """Reject a pending approval."""
    db = await get_db()
    cursor = await db.conn.execute(
        "SELECT * FROM approvals WHERE approval_id = ?", (approval_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Approval not found")
    if row["status"] != "pending":
        raise HTTPException(status_code=409, detail="Approval already resolved")

    resolved_at = datetime.utcnow().isoformat()
    await db.conn.execute(
        "UPDATE approvals SET status = 'rejected', comment = ?,"
        " resolved_at = ? WHERE approval_id = ?",
        (body.comment, resolved_at, approval_id),
    )
    await db.conn.commit()
    return {"approval_id": approval_id, "status": "rejected", "resolved_at": resolved_at}
