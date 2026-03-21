"""Approval API routes."""

from __future__ import annotations

import json
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
            "context": json.loads(r["context_json"] or "{}"),
            "created_at": r["created_at"],
            "expires_at": r["expires_at"],
        }
        for r in rows
    ]
    pending = sum(1 for a in approvals if a["status"] == "pending")
    return {"approvals": approvals, "pending_count": pending, "total": len(approvals)}


@router.get("/approvals/{approval_id}")
async def get_approval(approval_id: str) -> dict:
    """Get approval details."""
    db = await get_db()
    cursor = await db.conn.execute("SELECT * FROM approvals WHERE approval_id = ?", (approval_id,))
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
        "context": json.loads(row["context_json"] or "{}"),
        "comment": row["comment"],
        "created_at": row["created_at"],
        "resolved_at": row["resolved_at"],
        "expires_at": row["expires_at"],
    }


@router.post("/approvals/{approval_id}/approve")
async def approve(approval_id: str, body: ApprovalDecision) -> dict:
    """Approve a pending approval."""
    db = await get_db()
    cursor = await db.conn.execute("SELECT * FROM approvals WHERE approval_id = ?", (approval_id,))
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

    # Update trust scores after approval
    sprint_id = row["sprint_id"]
    agent_role = row["agent_id"]
    action_type = row["action_type"]

    # Get project_id from sprint
    sprint_cursor = await db.conn.execute(
        "SELECT project_id FROM sprints WHERE sprint_id = ?", (sprint_id,)
    )
    sprint_row = await sprint_cursor.fetchone()
    if sprint_row:
        project_id = sprint_row["project_id"]

        # Update trust score - increment success count
        await db.conn.execute(
            "INSERT INTO agent_trust_scores"
            " (project_id, agent_role, action_type, success_count, failure_count,"
            " trust_score, last_updated)"
            " VALUES (?, ?, ?, 1, 0, 1.0, ?)"
            " ON CONFLICT(project_id, agent_role, action_type)"
            " DO UPDATE SET"
            " success_count = success_count + 1,"
            " trust_score = CAST(success_count + 1 AS REAL) /"
            " (success_count + 1 + failure_count),"
            " last_updated = ?",
            (project_id, agent_role, action_type, resolved_at, resolved_at),
        )

    await db.conn.commit()
    return {"approval_id": approval_id, "status": "approved", "resolved_at": resolved_at}


@router.post("/approvals/{approval_id}/reject")
async def reject(approval_id: str, body: ApprovalDecision) -> dict:
    """Reject a pending approval."""
    db = await get_db()
    cursor = await db.conn.execute("SELECT * FROM approvals WHERE approval_id = ?", (approval_id,))
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

    # Update trust scores after rejection
    sprint_id = row["sprint_id"]
    agent_role = row["agent_id"]
    action_type = row["action_type"]

    # Get project_id from sprint
    sprint_cursor = await db.conn.execute(
        "SELECT project_id FROM sprints WHERE sprint_id = ?", (sprint_id,)
    )
    sprint_row = await sprint_cursor.fetchone()
    if sprint_row:
        project_id = sprint_row["project_id"]

        # Update trust score - increment failure count
        await db.conn.execute(
            "INSERT INTO agent_trust_scores"
            " (project_id, agent_role, action_type, success_count, failure_count,"
            " trust_score, last_updated)"
            " VALUES (?, ?, ?, 0, 1, 0.0, ?)"
            " ON CONFLICT(project_id, agent_role, action_type)"
            " DO UPDATE SET"
            " failure_count = failure_count + 1,"
            " trust_score = CAST(success_count AS REAL) /"
            " (success_count + failure_count + 1),"
            " last_updated = ?",
            (project_id, agent_role, action_type, resolved_at, resolved_at),
        )

    await db.conn.commit()
    return {"approval_id": approval_id, "status": "rejected", "resolved_at": resolved_at}
