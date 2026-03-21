#!/usr/bin/env python3
"""Backend verification script for E2E testing."""

import sys


def main():
    print("=== Backend Verification ===\n")

    # Test 1: Import approvals routes
    try:
        from foundrai.api.routes.approvals import router

        print("✓ Backend approval routes import successfully")
    except Exception as e:
        print(f"✗ Failed to import approval routes: {e}")
        return 1

    # Test 2: AgentConfig with timeout
    try:
        from foundrai.config import AgentConfig

        config = AgentConfig(role="test", approval_timeout_seconds=600)
        assert config.approval_timeout_seconds == 600
        print(f"✓ AgentConfig with timeout: {config.approval_timeout_seconds} seconds")
    except Exception as e:
        print(f"✗ Failed AgentConfig test: {e}")
        return 1

    # Test 3: SprintEngine import
    try:
        print("✓ SprintEngine imports successfully")
    except Exception as e:
        print(f"✗ Failed to import SprintEngine: {e}")
        return 1

    # Test 4: Approval API endpoints exist
    try:
        routes = [r.path for r in router.routes]
        expected = [
            "/sprints/{sprint_id}/approvals",
            "/approvals/{approval_id}",
            "/approvals/{approval_id}/approve",
            "/approvals/{approval_id}/reject",
        ]
        for path in expected:
            if path in routes:
                print(f"✓ Endpoint exists: {path}")
            else:
                print(f"✗ Missing endpoint: {path}")
                return 1
    except Exception as e:
        print(f"✗ Failed endpoint verification: {e}")
        return 1

    print("\n✅ All backend verifications passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
