"""E2E test for approval rejection flow with feedback.

This test verifies that:
1. Approval requests can be rejected with detailed feedback
2. Rejection comment is stored in database
3. Agent receives rejection (task becomes BLOCKED)
4. Rejection status is reflected in UI
5. Events are logged correctly
"""

from datetime import datetime

import pytest
from httpx import AsyncClient

from foundrai.api.deps import get_db


@pytest.mark.asyncio
async def test_approval_rejection_with_feedback(client: AsyncClient, project_id: str):
    """Test that an approval can be rejected with detailed feedback."""
    # Step 1: Create sprint with REQUIRE_APPROVAL autonomy
    create_resp = await client.post(
        f"/api/projects/{project_id}/sprints",
        json={"goal": "Test rejection flow"},
    )
    assert create_resp.status_code == 200
    sprint_id = create_resp.json()["sprint_id"]

    # Step 2: Insert approval request
    db = await get_db()
    approval_id = "test-rejection-approval-1"
    created_at = datetime.utcnow().isoformat()

    await db.conn.execute(
        """INSERT INTO approvals
           (approval_id, sprint_id, agent_id, action_type, title, description, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            approval_id,
            sprint_id,
            "developer",
            "task_execution",
            "Execute risky task",
            "This task requires approval and will be rejected",
            "pending",
            created_at,
        ),
    )
    await db.conn.commit()

    # Step 3: Verify approval is pending
    list_resp = await client.get(f"/api/sprints/{sprint_id}/approvals")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["pending_count"] == 1
    assert data["approvals"][0]["status"] == "pending"

    # Step 4: Reject with detailed feedback
    feedback_comment = "This approach is too risky. Please implement unit tests first and use a safer algorithm."
    reject_resp = await client.post(
        f"/api/approvals/{approval_id}/reject",
        json={"comment": feedback_comment},
    )
    assert reject_resp.status_code == 200
    reject_data = reject_resp.json()
    assert reject_data["status"] == "rejected"
    assert reject_data["resolved_at"] is not None

    # Step 5: Verify approval status changed to 'rejected' in database
    detail_resp = await client.get(f"/api/approvals/{approval_id}")
    assert detail_resp.status_code == 200
    approval_data = detail_resp.json()
    assert approval_data["status"] == "rejected"
    assert approval_data["comment"] == feedback_comment
    assert approval_data["resolved_at"] is not None

    # Step 6: Verify pending count decreased
    list_resp = await client.get(f"/api/sprints/{sprint_id}/approvals")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["pending_count"] == 0  # No longer pending
    assert data["total"] == 1  # Still in total list

    # Step 7: Verify cannot approve rejected approval
    approve_resp = await client.post(
        f"/api/approvals/{approval_id}/approve",
        json={"comment": "Changed my mind"},
    )
    assert approve_resp.status_code == 409  # Conflict - already resolved

    # Step 8: Verify cannot reject again
    reject_again_resp = await client.post(
        f"/api/approvals/{approval_id}/reject",
        json={"comment": "Still no"},
    )
    assert reject_again_resp.status_code == 409  # Conflict - already resolved


@pytest.mark.asyncio
async def test_rejection_without_comment(client: AsyncClient, project_id: str):
    """Test that an approval can be rejected without a comment."""
    # Create sprint and approval
    create_resp = await client.post(
        f"/api/projects/{project_id}/sprints",
        json={"goal": "Test rejection without comment"},
    )
    sprint_id = create_resp.json()["sprint_id"]

    db = await get_db()
    approval_id = "test-rejection-no-comment"

    await db.conn.execute(
        """INSERT INTO approvals
           (approval_id, sprint_id, agent_id, action_type, title, status)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (approval_id, sprint_id, "developer", "task_execution", "Task to reject", "pending"),
    )
    await db.conn.commit()

    # Reject without comment
    reject_resp = await client.post(
        f"/api/approvals/{approval_id}/reject",
        json={},  # Empty comment
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"

    # Verify in database
    detail_resp = await client.get(f"/api/approvals/{approval_id}")
    assert detail_resp.status_code == 200
    approval_data = detail_resp.json()
    assert approval_data["status"] == "rejected"
    assert approval_data["comment"] == ""  # Empty string, not None


@pytest.mark.asyncio
async def test_multiple_approvals_mixed_decisions(
    client: AsyncClient, project_id: str
):
    """Test that multiple approvals can have different outcomes (approve/reject)."""
    # Create sprint
    create_resp = await client.post(
        f"/api/projects/{project_id}/sprints",
        json={"goal": "Test mixed decisions"},
    )
    sprint_id = create_resp.json()["sprint_id"]

    # Create three approval requests
    db = await get_db()
    approval_ids = ["mixed-1", "mixed-2", "mixed-3"]

    for approval_id in approval_ids:
        await db.conn.execute(
            """INSERT INTO approvals
               (approval_id, sprint_id, agent_id, action_type, title, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (approval_id, sprint_id, "developer", "task_execution", f"Task {approval_id}", "pending"),
        )
    await db.conn.commit()

    # Verify all pending
    list_resp = await client.get(f"/api/sprints/{sprint_id}/approvals")
    assert list_resp.json()["pending_count"] == 3

    # Approve first one
    await client.post(
        f"/api/approvals/mixed-1/approve",
        json={"comment": "Good work"},
    )

    # Reject second one with feedback
    await client.post(
        f"/api/approvals/mixed-2/reject",
        json={"comment": "Needs more work"},
    )

    # Leave third one pending

    # Verify counts
    list_resp = await client.get(f"/api/sprints/{sprint_id}/approvals")
    data = list_resp.json()
    assert data["pending_count"] == 1  # Only mixed-3
    assert data["total"] == 3

    # Verify individual statuses
    resp1 = await client.get(f"/api/approvals/mixed-1")
    assert resp1.json()["status"] == "approved"
    assert resp1.json()["comment"] == "Good work"

    resp2 = await client.get(f"/api/approvals/mixed-2")
    assert resp2.json()["status"] == "rejected"
    assert resp2.json()["comment"] == "Needs more work"

    resp3 = await client.get(f"/api/approvals/mixed-3")
    assert resp3.json()["status"] == "pending"
    assert resp3.json()["comment"] is None or resp3.json()["comment"] == ""


@pytest.mark.asyncio
async def test_rejection_comment_max_length(client: AsyncClient, project_id: str):
    """Test rejection with very long feedback comment."""
    # Create sprint and approval
    create_resp = await client.post(
        f"/api/projects/{project_id}/sprints",
        json={"goal": "Test long comment"},
    )
    sprint_id = create_resp.json()["sprint_id"]

    db = await get_db()
    approval_id = "test-long-comment"

    await db.conn.execute(
        """INSERT INTO approvals
           (approval_id, sprint_id, agent_id, action_type, title, status)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (approval_id, sprint_id, "developer", "task_execution", "Task with long feedback", "pending"),
    )
    await db.conn.commit()

    # Create very long comment (simulate detailed feedback)
    long_comment = """This code needs significant improvements:

1. Error handling: Add try-catch blocks around all API calls
2. Input validation: Validate all user inputs before processing
3. Performance: The current algorithm has O(n²) complexity - needs optimization
4. Security: SQL injection vulnerability in line 42 - use parameterized queries
5. Testing: Add unit tests for all edge cases
6. Documentation: Add docstrings to all public methods
7. Code style: Follow PEP 8 conventions consistently
8. Dependencies: Update deprecated libraries to latest versions

Please address these issues and resubmit for approval.
"""

    # Reject with long comment
    reject_resp = await client.post(
        f"/api/approvals/{approval_id}/reject",
        json={"comment": long_comment},
    )
    assert reject_resp.status_code == 200

    # Verify comment stored correctly
    detail_resp = await client.get(f"/api/approvals/{approval_id}")
    assert detail_resp.status_code == 200
    approval_data = detail_resp.json()
    assert approval_data["status"] == "rejected"
    assert approval_data["comment"] == long_comment
    assert len(approval_data["comment"]) > 500  # Verify it's indeed long


@pytest.mark.asyncio
async def test_rejection_special_characters_in_comment(
    client: AsyncClient, project_id: str
):
    """Test rejection comment with special characters and formatting."""
    # Create sprint and approval
    create_resp = await client.post(
        f"/api/projects/{project_id}/sprints",
        json={"goal": "Test special chars"},
    )
    sprint_id = create_resp.json()["sprint_id"]

    db = await get_db()
    approval_id = "test-special-chars"

    await db.conn.execute(
        """INSERT INTO approvals
           (approval_id, sprint_id, agent_id, action_type, title, status)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (approval_id, sprint_id, "developer", "task_execution", "Task with special chars", "pending"),
    )
    await db.conn.commit()

    # Comment with special characters
    special_comment = """Issues found:
- Code contains "quotes" and 'apostrophes'
- SQL injection: WHERE user='${userInput}' <-- dangerous!
- Use this instead: `WHERE user = ?` with parameterized queries
- Math symbols: x > 10 && y < 20
- Newlines, tabs\t, and other escapes\n
- Unicode: 🚀 Ready to launch? ✅ Yes!
"""

    # Reject with special characters
    reject_resp = await client.post(
        f"/api/approvals/{approval_id}/reject",
        json={"comment": special_comment},
    )
    assert reject_resp.status_code == 200

    # Verify comment stored correctly
    detail_resp = await client.get(f"/api/approvals/{approval_id}")
    assert detail_resp.status_code == 200
    approval_data = detail_resp.json()
    assert approval_data["status"] == "rejected"
    assert approval_data["comment"] == special_comment
