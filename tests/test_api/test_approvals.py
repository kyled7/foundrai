"""Tests for approval endpoints."""

import pytest
from httpx import AsyncClient

from foundrai.api.deps import get_db


@pytest.mark.asyncio
async def test_list_approvals_empty(client: AsyncClient, project_id: str):
    create_resp = await client.post(
        f"/api/projects/{project_id}/sprints",
        json={"goal": "test"},
    )
    sprint_id = create_resp.json()["sprint_id"]
    resp = await client.get(f"/api/sprints/{sprint_id}/approvals")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["pending_count"] == 0


@pytest.mark.asyncio
async def test_approve_not_found(client: AsyncClient):
    resp = await client.post("/api/approvals/nonexistent/approve", json={})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_approve_flow(client: AsyncClient, project_id: str):
    """Test creating an approval (via DB) and approving it."""
    create_resp = await client.post(
        f"/api/projects/{project_id}/sprints",
        json={"goal": "test"},
    )
    sprint_id = create_resp.json()["sprint_id"]

    # Insert an approval directly into DB
    db = await get_db()
    await db.conn.execute(
        """INSERT INTO approvals (approval_id, sprint_id, agent_id, action_type, title, status)
        VALUES (?, ?, ?, ?, ?, ?)""",
        ("test-approval-1", sprint_id, "developer", "task_execution", "Execute task", "pending"),
    )
    await db.conn.commit()

    # List approvals
    resp = await client.get(f"/api/sprints/{sprint_id}/approvals")
    assert resp.status_code == 200
    data = resp.json()
    assert data["pending_count"] == 1
    assert data["total"] == 1

    # Approve it
    resp = await client.post(
        "/api/approvals/test-approval-1/approve",
        json={"comment": "Looks good"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "approved"
    assert data["resolved_at"]

    # Can't approve again
    resp = await client.post("/api/approvals/test-approval-1/approve", json={})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_reject_flow(client: AsyncClient, project_id: str):
    create_resp = await client.post(
        f"/api/projects/{project_id}/sprints",
        json={"goal": "test"},
    )
    sprint_id = create_resp.json()["sprint_id"]

    db = await get_db()
    await db.conn.execute(
        """INSERT INTO approvals (approval_id, sprint_id, agent_id, action_type, title, status)
        VALUES (?, ?, ?, ?, ?, ?)""",
        ("test-approval-2", sprint_id, "developer", "task_execution", "Execute task", "pending"),
    )
    await db.conn.commit()

    resp = await client.post(
        "/api/approvals/test-approval-2/reject",
        json={"comment": "Not ready"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"
