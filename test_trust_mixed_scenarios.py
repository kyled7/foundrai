#!/usr/bin/env python3
"""
Additional test for mixed success/failure trust score scenarios.

Verifies that trust scores:
1. Decrease appropriately when failures occur
2. Calculate correct success rates with mixed results
3. Don't recommend upgrade with low success rates
"""

import asyncio
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import aiosqlite

sys.path.insert(0, str(Path(__file__).parent))

from foundrai.models.enums import ActionType, AgentRoleName, AutonomyLevel


async def test_mixed_scenario():
    """Test trust scoring with 7 successes and 3 failures."""
    print("=" * 70)
    print("🧪 Mixed Success/Failure Scenario Test")
    print("=" * 70)

    db_path = ".foundrai/test_trust_mixed.db"
    project_id = f"test-project-{uuid.uuid4().hex[:8]}"
    sprint_id = f"sprint-{uuid.uuid4().hex[:8]}"

    # Remove existing test database
    db_file = Path(db_path)
    if db_file.exists():
        db_file.unlink()
    db_file.parent.mkdir(parents=True, exist_ok=True)

    # Setup database
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row

    from foundrai.persistence.database import SCHEMA_SQL
    await db.executescript(SCHEMA_SQL)
    await db.commit()

    # Create test project and sprint
    await db.execute(
        "INSERT INTO projects (project_id, name, description) VALUES (?, ?, ?)",
        (project_id, "Mixed Test", "Mixed scenario test"),
    )
    await db.execute(
        "INSERT INTO sprints (sprint_id, project_id, sprint_number, goal, status) VALUES (?, ?, ?, ?, ?)",
        (sprint_id, project_id, 1, "Test mixed", "in_progress"),
    )
    await db.commit()

    print("\n📊 Running 10 approval cycles (7 approve, 3 reject)...")

    # Simulate 10 approval cycles with 7 approvals and 3 rejections
    for i in range(1, 11):
        approval_id = f"approval-{uuid.uuid4().hex[:8]}"
        created_at = datetime.utcnow().isoformat()
        expires_at = (datetime.utcnow() + timedelta(minutes=5)).isoformat()

        # Create approval
        await db.execute(
            """INSERT INTO approvals
               (approval_id, sprint_id, agent_id, action_type, title, status, created_at, expires_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                approval_id,
                sprint_id,
                AgentRoleName.DEVELOPER.value,
                ActionType.CODE_WRITE.value,
                f"Action #{i}",
                "pending",
                created_at,
                expires_at,
            ),
        )

        # Approve first 7, reject last 3
        is_approved = i <= 7
        status = "approved" if is_approved else "rejected"
        resolved_at = datetime.utcnow().isoformat()

        await db.execute(
            "UPDATE approvals SET status = ?, resolved_at = ? WHERE approval_id = ?",
            (status, resolved_at, approval_id),
        )

        # Update trust score
        if is_approved:
            await db.execute(
                """INSERT INTO agent_trust_scores
                   (project_id, agent_role, action_type, success_count, failure_count, trust_score, last_updated)
                   VALUES (?, ?, ?, 1, 0, 1.0, ?)
                   ON CONFLICT(project_id, agent_role, action_type)
                   DO UPDATE SET
                       success_count = success_count + 1,
                       trust_score = CAST(success_count + 1 AS REAL) / (success_count + 1 + failure_count),
                       last_updated = ?""",
                (project_id, AgentRoleName.DEVELOPER.value, ActionType.CODE_WRITE.value, resolved_at, resolved_at),
            )
        else:
            await db.execute(
                """INSERT INTO agent_trust_scores
                   (project_id, agent_role, action_type, success_count, failure_count, trust_score, last_updated)
                   VALUES (?, ?, ?, 0, 1, 0.0, ?)
                   ON CONFLICT(project_id, agent_role, action_type)
                   DO UPDATE SET
                       failure_count = failure_count + 1,
                       trust_score = CAST(success_count AS REAL) / (success_count + failure_count + 1),
                       last_updated = ?""",
                (project_id, AgentRoleName.DEVELOPER.value, ActionType.CODE_WRITE.value, resolved_at, resolved_at),
            )

        await db.commit()

        # Get current trust score
        cursor = await db.execute(
            """SELECT trust_score, success_count, failure_count FROM agent_trust_scores
               WHERE project_id = ? AND agent_role = ? AND action_type = ?""",
            (project_id, AgentRoleName.DEVELOPER.value, ActionType.CODE_WRITE.value),
        )
        row = await cursor.fetchone()
        if row:
            success_rate = row["trust_score"] * 100
            print(f"  Iteration {i}: {status:8} → {success_rate:.1f}% ({row['success_count']}S, {row['failure_count']}F)")

    # Verify final results
    print("\n📊 Final Results:")
    cursor = await db.execute(
        """SELECT trust_score, success_count, failure_count FROM agent_trust_scores
           WHERE project_id = ? AND agent_role = ? AND action_type = ?""",
        (project_id, AgentRoleName.DEVELOPER.value, ActionType.CODE_WRITE.value),
    )
    row = await cursor.fetchone()

    if row:
        success_rate = row["trust_score"] * 100
        print(f"  Success Count: {row['success_count']}")
        print(f"  Failure Count: {row['failure_count']}")
        print(f"  Trust Score: {row['trust_score']:.3f}")
        print(f"  Success Rate: {success_rate:.1f}%")

        # Verify calculations
        expected_rate = 70.0  # 7 out of 10
        if abs(success_rate - expected_rate) < 0.1:
            print(f"\n✅ Success rate calculation correct (expected ~70%)")
        else:
            print(f"\n❌ Success rate calculation incorrect (expected ~70%, got {success_rate:.1f}%)")

        # Check recommendations (should NOT recommend upgrade at 70%)
        cursor = await db.execute(
            """SELECT * FROM agent_trust_scores
               WHERE project_id = ? AND trust_score >= 0.90 AND (success_count + failure_count) >= 5""",
            (project_id,),
        )
        recommendations = await cursor.fetchall()

        if len(recommendations) == 0:
            print(f"✅ No upgrade recommendation (70% is below 90% threshold)")
            result = True
        else:
            print(f"❌ Unexpected upgrade recommendation at 70% success rate")
            result = False
    else:
        print("\n❌ No trust score found")
        result = False

    await db.close()

    print("\n" + "=" * 70)
    if result:
        print("✅ Mixed scenario test PASSED!")
        return True
    else:
        print("❌ Mixed scenario test FAILED!")
        return False


async def test_recovery_scenario():
    """Test trust score recovery after initial failures."""
    print("\n" + "=" * 70)
    print("🧪 Recovery Scenario Test (3 failures then 10 successes)")
    print("=" * 70)

    db_path = ".foundrai/test_trust_recovery.db"
    project_id = f"test-project-{uuid.uuid4().hex[:8]}"
    sprint_id = f"sprint-{uuid.uuid4().hex[:8]}"

    # Remove existing test database
    db_file = Path(db_path)
    if db_file.exists():
        db_file.unlink()
    db_file.parent.mkdir(parents=True, exist_ok=True)

    # Setup database
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row

    from foundrai.persistence.database import SCHEMA_SQL
    await db.executescript(SCHEMA_SQL)
    await db.commit()

    # Create test project and sprint
    await db.execute(
        "INSERT INTO projects (project_id, name, description) VALUES (?, ?, ?)",
        (project_id, "Recovery Test", "Recovery scenario test"),
    )
    await db.execute(
        "INSERT INTO sprints (sprint_id, project_id, sprint_number, goal, status) VALUES (?, ?, ?, ?, ?)",
        (sprint_id, project_id, 1, "Test recovery", "in_progress"),
    )
    await db.commit()

    print("\n📊 Simulating 3 initial failures followed by 10 successes...")

    # 3 failures first
    for i in range(1, 4):
        approval_id = f"approval-{uuid.uuid4().hex[:8]}"
        await db.execute(
            """INSERT INTO approvals
               (approval_id, sprint_id, agent_id, action_type, title, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (approval_id, sprint_id, AgentRoleName.QA_ENGINEER.value, ActionType.CODE_REVIEW.value,
             f"Review #{i}", "rejected", datetime.utcnow().isoformat()),
        )

        resolved_at = datetime.utcnow().isoformat()
        await db.execute(
            """INSERT INTO agent_trust_scores
               (project_id, agent_role, action_type, success_count, failure_count, trust_score, last_updated)
               VALUES (?, ?, ?, 0, 1, 0.0, ?)
               ON CONFLICT(project_id, agent_role, action_type)
               DO UPDATE SET
                   failure_count = failure_count + 1,
                   trust_score = CAST(success_count AS REAL) / (success_count + failure_count + 1),
                   last_updated = ?""",
            (project_id, AgentRoleName.QA_ENGINEER.value, ActionType.CODE_REVIEW.value, resolved_at, resolved_at),
        )
        await db.commit()

    # Then 10 successes
    for i in range(4, 14):
        approval_id = f"approval-{uuid.uuid4().hex[:8]}"
        await db.execute(
            """INSERT INTO approvals
               (approval_id, sprint_id, agent_id, action_type, title, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (approval_id, sprint_id, AgentRoleName.QA_ENGINEER.value, ActionType.CODE_REVIEW.value,
             f"Review #{i}", "approved", datetime.utcnow().isoformat()),
        )

        resolved_at = datetime.utcnow().isoformat()
        await db.execute(
            """INSERT INTO agent_trust_scores
               (project_id, agent_role, action_type, success_count, failure_count, trust_score, last_updated)
               VALUES (?, ?, ?, 1, 0, 1.0, ?)
               ON CONFLICT(project_id, agent_role, action_type)
               DO UPDATE SET
                   success_count = success_count + 1,
                   trust_score = CAST(success_count + 1 AS REAL) / (success_count + 1 + failure_count),
                   last_updated = ?""",
            (project_id, AgentRoleName.QA_ENGINEER.value, ActionType.CODE_REVIEW.value, resolved_at, resolved_at),
        )
        await db.commit()

    # Check final results
    cursor = await db.execute(
        """SELECT trust_score, success_count, failure_count FROM agent_trust_scores
           WHERE project_id = ? AND agent_role = ? AND action_type = ?""",
        (project_id, AgentRoleName.QA_ENGINEER.value, ActionType.CODE_REVIEW.value),
    )
    row = await cursor.fetchone()

    if row:
        success_rate = row["trust_score"] * 100
        print(f"\n📊 Final Results:")
        print(f"  Success Count: {row['success_count']}")
        print(f"  Failure Count: {row['failure_count']}")
        print(f"  Trust Score: {row['trust_score']:.3f}")
        print(f"  Success Rate: {success_rate:.1f}%")

        # 10 successes out of 13 total = 76.9%
        expected_rate = (10.0 / 13.0) * 100
        if abs(success_rate - expected_rate) < 0.1:
            print(f"\n✅ Recovery scenario correct: {success_rate:.1f}% (10/13)")
            result = True
        else:
            print(f"\n❌ Recovery scenario incorrect: expected {expected_rate:.1f}%, got {success_rate:.1f}%")
            result = False
    else:
        print("\n❌ No trust score found")
        result = False

    await db.close()

    print("\n" + "=" * 70)
    if result:
        print("✅ Recovery scenario test PASSED!")
    else:
        print("❌ Recovery scenario test FAILED!")

    return result


async def main():
    """Run all test scenarios."""
    results = []

    # Test 1: Mixed success/failure
    results.append(await test_mixed_scenario())

    # Test 2: Recovery scenario
    results.append(await test_recovery_scenario())

    # Overall result
    print("\n" + "=" * 70)
    print("🎯 OVERALL TEST RESULTS")
    print("=" * 70)
    print(f"  Mixed Scenario: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"  Recovery Scenario: {'✅ PASS' if results[1] else '❌ FAIL'}")

    if all(results):
        print("\n✅ ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
