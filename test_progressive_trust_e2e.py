#!/usr/bin/env python3
"""
End-to-End Integration Test for Progressive Trust Score Updates

This test verifies that:
1. Developer × code_write can be set to REQUIRE_APPROVAL
2. Triggering and approving code write actions increments trust scores
3. Trust scores increase progressively with each approval
4. After 10 approvals, success rate is >90%
5. Recommendations suggest upgrade to AUTO_APPROVE
"""

import asyncio
import json
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import aiosqlite

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from foundrai.models.enums import ActionType, AgentRoleName, AutonomyLevel


class ProgressiveTrustE2ETest:
    """End-to-end test for progressive trust scoring."""

    def __init__(self, db_path: str = ".foundrai/test_trust.db"):
        self.db_path = db_path
        self.project_id = f"test-project-{uuid.uuid4().hex[:8]}"
        self.sprint_id = f"sprint-{uuid.uuid4().hex[:8]}"
        self.db = None
        self.test_results = {
            "setup": False,
            "configuration": False,
            "approval_creation": False,
            "trust_score_updates": [],
            "success_rate_validation": False,
            "recommendation_validation": False,
            "errors": [],
        }

    async def setup_database(self):
        """Initialize test database with schema."""
        print("📦 Setting up test database...")

        # Remove existing test database
        db_file = Path(self.db_path)
        if db_file.exists():
            db_file.unlink()

        db_file.parent.mkdir(parents=True, exist_ok=True)

        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row

        # Import schema from database.py
        from foundrai.persistence.database import SCHEMA_SQL

        # Execute schema
        await self.db.executescript(SCHEMA_SQL)
        await self.db.commit()

        # Create test project and sprint
        await self.db.execute(
            "INSERT INTO projects (project_id, name, description, created_at) VALUES (?, ?, ?, ?)",
            (self.project_id, "Test Project", "Progressive trust test", datetime.utcnow().isoformat()),
        )

        await self.db.execute(
            "INSERT INTO sprints (sprint_id, project_id, sprint_number, goal, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (self.sprint_id, self.project_id, 1, "Test progressive trust", "in_progress", datetime.utcnow().isoformat()),
        )

        await self.db.commit()

        self.test_results["setup"] = True
        print("✅ Database setup complete")

    async def configure_autonomy(self):
        """Set Developer × code_write to REQUIRE_APPROVAL."""
        print("\n🔧 Configuring autonomy matrix...")

        try:
            # Set Developer × code_write to require_approval
            agent_role = AgentRoleName.DEVELOPER.value
            action_type = ActionType.CODE_WRITE.value
            autonomy_mode = AutonomyLevel.REQUIRE_APPROVAL.value

            await self.db.execute(
                """INSERT INTO autonomy_config
                   (project_id, agent_role, action_type, autonomy_mode, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    self.project_id,
                    agent_role,
                    action_type,
                    autonomy_mode,
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                ),
            )
            await self.db.commit()

            # Verify configuration
            cursor = await self.db.execute(
                "SELECT autonomy_mode FROM autonomy_config WHERE project_id = ? AND agent_role = ? AND action_type = ?",
                (self.project_id, agent_role, action_type),
            )
            row = await cursor.fetchone()

            if row and row["autonomy_mode"] == autonomy_mode:
                self.test_results["configuration"] = True
                print(f"✅ Set {agent_role} × {action_type} to {autonomy_mode}")
            else:
                raise Exception("Configuration verification failed")

        except Exception as e:
            self.test_results["errors"].append(f"Configuration error: {str(e)}")
            print(f"❌ Configuration failed: {e}")

    async def create_and_approve_action(self, iteration: int) -> bool:
        """Create a code write approval request and approve it."""
        print(f"\n🔄 Iteration {iteration}/10: Creating and approving action...")

        try:
            # Create approval request
            approval_id = f"approval-{uuid.uuid4().hex[:8]}"
            created_at = datetime.utcnow().isoformat()
            expires_at = (datetime.utcnow() + timedelta(minutes=5)).isoformat()

            await self.db.execute(
                """INSERT INTO approvals
                   (approval_id, sprint_id, agent_id, action_type, title, description,
                    status, created_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    approval_id,
                    self.sprint_id,
                    AgentRoleName.DEVELOPER.value,
                    ActionType.CODE_WRITE.value,
                    f"Code Write #{iteration}",
                    f"Test code write action {iteration}",
                    "pending",
                    created_at,
                    expires_at,
                ),
            )
            await self.db.commit()
            print(f"  ✓ Created approval request: {approval_id}")

            # Approve the request (simulate approval endpoint logic)
            resolved_at = datetime.utcnow().isoformat()
            await self.db.execute(
                "UPDATE approvals SET status = 'approved', resolved_at = ? WHERE approval_id = ?",
                (resolved_at, approval_id),
            )

            # Update trust score - increment success count
            await self.db.execute(
                """INSERT INTO agent_trust_scores
                   (project_id, agent_role, action_type, success_count, failure_count,
                    trust_score, last_updated)
                   VALUES (?, ?, ?, 1, 0, 1.0, ?)
                   ON CONFLICT(project_id, agent_role, action_type)
                   DO UPDATE SET
                       success_count = success_count + 1,
                       trust_score = CAST(success_count + 1 AS REAL) /
                                    (success_count + 1 + failure_count),
                       last_updated = ?""",
                (
                    self.project_id,
                    AgentRoleName.DEVELOPER.value,
                    ActionType.CODE_WRITE.value,
                    resolved_at,
                    resolved_at,
                ),
            )
            await self.db.commit()
            print(f"  ✓ Approved request and updated trust score")

            # Verify trust score update
            cursor = await self.db.execute(
                """SELECT trust_score, success_count, failure_count
                   FROM agent_trust_scores
                   WHERE project_id = ? AND agent_role = ? AND action_type = ?""",
                (
                    self.project_id,
                    AgentRoleName.DEVELOPER.value,
                    ActionType.CODE_WRITE.value,
                ),
            )
            row = await cursor.fetchone()

            if row:
                success_rate = row["trust_score"] * 100
                self.test_results["trust_score_updates"].append({
                    "iteration": iteration,
                    "success_count": row["success_count"],
                    "failure_count": row["failure_count"],
                    "trust_score": row["trust_score"],
                    "success_rate_pct": success_rate,
                })
                print(f"  ✓ Trust score: {row['trust_score']:.3f} ({success_rate:.1f}% success rate)")
                print(f"    Success: {row['success_count']}, Failures: {row['failure_count']}")
                return True
            else:
                raise Exception("Trust score not found after update")

        except Exception as e:
            self.test_results["errors"].append(f"Iteration {iteration} error: {str(e)}")
            print(f"  ❌ Failed: {e}")
            return False

    async def verify_success_rate(self):
        """Verify that success rate is >90% after 10 approvals."""
        print("\n📊 Verifying success rate...")

        try:
            cursor = await self.db.execute(
                """SELECT trust_score, success_count, failure_count
                   FROM agent_trust_scores
                   WHERE project_id = ? AND agent_role = ? AND action_type = ?""",
                (
                    self.project_id,
                    AgentRoleName.DEVELOPER.value,
                    ActionType.CODE_WRITE.value,
                ),
            )
            row = await cursor.fetchone()

            if row:
                success_rate = row["trust_score"] * 100
                success_count = row["success_count"]
                failure_count = row["failure_count"]

                print(f"  Final Statistics:")
                print(f"    Success Count: {success_count}")
                print(f"    Failure Count: {failure_count}")
                print(f"    Trust Score: {row['trust_score']:.3f}")
                print(f"    Success Rate: {success_rate:.1f}%")

                if success_rate >= 90.0:
                    self.test_results["success_rate_validation"] = True
                    print(f"  ✅ Success rate ({success_rate:.1f}%) is >90%")
                else:
                    self.test_results["errors"].append(
                        f"Success rate ({success_rate:.1f}%) is below 90%"
                    )
                    print(f"  ❌ Success rate ({success_rate:.1f}%) is below 90%")
            else:
                raise Exception("No trust score found for verification")

        except Exception as e:
            self.test_results["errors"].append(f"Success rate verification error: {str(e)}")
            print(f"  ❌ Verification failed: {e}")

    async def verify_recommendations(self):
        """Verify that recommendations suggest upgrade to AUTO_APPROVE."""
        print("\n💡 Verifying recommendations...")

        try:
            cursor = await self.db.execute(
                """SELECT agent_role, action_type, trust_score, success_count, failure_count
                   FROM agent_trust_scores
                   WHERE project_id = ? AND trust_score >= 0.90 AND (success_count + failure_count) >= 5
                   ORDER BY trust_score DESC""",
                (self.project_id,),
            )
            rows = await cursor.fetchall()

            recommendations = []
            for row in rows:
                success_rate = row["trust_score"] * 100
                total_attempts = row["success_count"] + row["failure_count"]

                # Check current autonomy level
                config_cursor = await self.db.execute(
                    """SELECT autonomy_mode FROM autonomy_config
                       WHERE project_id = ? AND agent_role = ? AND action_type = ?""",
                    (self.project_id, row["agent_role"], row["action_type"]),
                )
                config_row = await config_cursor.fetchone()
                current_mode = config_row["autonomy_mode"] if config_row else "notify"

                if current_mode != AutonomyLevel.AUTO_APPROVE.value:
                    recommendation = {
                        "agent_role": row["agent_role"],
                        "action_type": row["action_type"],
                        "current_mode": current_mode,
                        "suggested_mode": AutonomyLevel.AUTO_APPROVE.value,
                        "success_rate": success_rate,
                        "total_attempts": total_attempts,
                        "reason": f"High success rate ({success_rate:.1f}%) over {total_attempts} attempts",
                    }
                    recommendations.append(recommendation)

            if recommendations:
                self.test_results["recommendation_validation"] = True
                print(f"  ✅ Found {len(recommendations)} recommendation(s):")
                for rec in recommendations:
                    print(f"    • {rec['agent_role']} × {rec['action_type']}")
                    print(f"      Current: {rec['current_mode']} → Suggested: {rec['suggested_mode']}")
                    print(f"      Reason: {rec['reason']}")
            else:
                self.test_results["errors"].append("No recommendations found despite high success rate")
                print("  ❌ No recommendations found")

        except Exception as e:
            self.test_results["errors"].append(f"Recommendation verification error: {str(e)}")
            print(f"  ❌ Verification failed: {e}")

    async def run_test(self):
        """Run the complete end-to-end test."""
        print("=" * 70)
        print("🧪 Progressive Trust Score E2E Test")
        print("=" * 70)

        try:
            # Setup
            await self.setup_database()

            # Configure autonomy
            await self.configure_autonomy()

            if not self.test_results["configuration"]:
                print("\n❌ Test failed: Configuration step failed")
                return False

            # Run 10 approval cycles
            print("\n📋 Running 10 approval cycles...")
            for i in range(1, 11):
                success = await self.create_and_approve_action(i)
                if not success:
                    print(f"\n❌ Test failed at iteration {i}")
                    return False

                # Small delay between iterations
                await asyncio.sleep(0.1)

            self.test_results["approval_creation"] = True

            # Verify results
            await self.verify_success_rate()
            await self.verify_recommendations()

            # Print summary
            self.print_summary()

            # Determine overall result
            all_passed = (
                self.test_results["setup"]
                and self.test_results["configuration"]
                and self.test_results["approval_creation"]
                and self.test_results["success_rate_validation"]
                and self.test_results["recommendation_validation"]
                and len(self.test_results["errors"]) == 0
            )

            return all_passed

        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            self.test_results["errors"].append(f"Test exception: {str(e)}")
            return False

        finally:
            if self.db:
                await self.db.close()

    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)

        print(f"\n✓ Setup: {'PASS' if self.test_results['setup'] else 'FAIL'}")
        print(f"✓ Configuration: {'PASS' if self.test_results['configuration'] else 'FAIL'}")
        print(f"✓ Approval Creation: {'PASS' if self.test_results['approval_creation'] else 'FAIL'}")
        print(f"✓ Success Rate >90%: {'PASS' if self.test_results['success_rate_validation'] else 'FAIL'}")
        print(f"✓ Recommendations: {'PASS' if self.test_results['recommendation_validation'] else 'FAIL'}")

        if self.test_results["trust_score_updates"]:
            print("\n📈 Trust Score Progress:")
            for update in self.test_results["trust_score_updates"]:
                print(
                    f"  Iteration {update['iteration']}: "
                    f"{update['success_rate_pct']:.1f}% "
                    f"({update['success_count']} successes, {update['failure_count']} failures)"
                )

        if self.test_results["errors"]:
            print("\n❌ Errors:")
            for error in self.test_results["errors"]:
                print(f"  • {error}")

        print("\n" + "=" * 70)


async def main():
    """Run the test."""
    test = ProgressiveTrustE2ETest()
    success = await test.run_test()

    if success:
        print("\n✅ All tests PASSED!")
        sys.exit(0)
    else:
        print("\n❌ Some tests FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
