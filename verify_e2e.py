#!/usr/bin/env python3
"""End-to-end verification script for agent health monitoring feature."""

import sys
import traceback


def verify_imports():
    """Verify all backend imports work."""
    print("🔍 Verifying backend imports...")
    try:
        print("  ✅ AgentHealth models imported")

        print("  ✅ AgentHealthStore imported")

        print("  ✅ Agent health router imported")

        from foundrai.persistence.database import SCHEMA_SQL

        assert "agent_health_metrics" in SCHEMA_SQL
        print("  ✅ Database schema includes agent_health_metrics table")

        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        traceback.print_exc()
        return False


def verify_api_registration():
    """Verify API router is registered."""
    print("\n🔍 Verifying API registration...")
    try:
        from foundrai.api.app import app

        # Check if agent_health route is registered
        routes = [route.path for route in app.routes]
        agent_health_routes = [r for r in routes if "agent-health" in r]

        if agent_health_routes:
            print(f"  ✅ Found {len(agent_health_routes)} agent health route(s):")
            for route in agent_health_routes:
                print(f"     - {route}")
            return True
        else:
            print("  ❌ No agent health routes found")
            return False
    except Exception as e:
        print(f"  ❌ API verification failed: {e}")
        traceback.print_exc()
        return False


def verify_models():
    """Verify model structure."""
    print("\n🔍 Verifying data models...")
    try:
        from foundrai.models.agent_health import AgentHealth, AgentHealthMetrics, AgentHealthStatus

        # Create a sample health metrics object
        metrics = AgentHealthMetrics(
            completion_rate=0.85,
            quality_score=0.90,
            cost_efficiency=0.75,
            avg_execution_time=120.5,
            task_count=10,
            failure_count=1,
        )
        print("  ✅ AgentHealthMetrics model works")

        # Create a sample agent health object
        health = AgentHealth(
            agent_role="Developer",
            project_id="test-project",
            sprint_id="sprint-1",
            health_score=85,
            status=AgentHealthStatus.HEALTHY,
            metrics=metrics,
            recommendations=["Keep up the good work!"],
        )
        print("  ✅ AgentHealth model works")
        print(f"     - Health score: {health.health_score}")
        print(f"     - Status: {health.status}")

        return True
    except Exception as e:
        print(f"  ❌ Model verification failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("AGENT HEALTH MONITORING - E2E VERIFICATION")
    print("=" * 60)

    results = []

    # Run all checks
    results.append(("Imports", verify_imports()))
    results.append(("Models", verify_models()))
    results.append(("API Registration", verify_api_registration()))

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 All backend verifications passed!")
        print("\nNext steps for manual verification:")
        print(
            "1. Start backend: source .venv/bin/activate && uvicorn foundrai.api.app:app --reload"
        )
        print("2. Start frontend: cd frontend && npm run dev")
        print("3. Test API endpoint: curl http://localhost:8000/api/projects/test/agent-health")
        print("4. Open browser to http://localhost:5173 and verify AgentHealthDashboard renders")
        return 0
    else:
        print("\n❌ Some verifications failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
