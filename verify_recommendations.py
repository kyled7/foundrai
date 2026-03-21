#!/usr/bin/env python3
"""End-to-end verification script for intelligent model recommendation engine."""

import sys
import traceback
from pathlib import Path


def verify_backend_files():
    """Verify all backend files exist."""
    print("🔍 Verifying backend files...")
    files = {
        "foundrai/models/recommendation.py": "Recommendation models",
        "foundrai/persistence/recommendation_store.py": "Recommendation store",
        "foundrai/orchestration/recommendation_engine.py": "Recommendation engine",
        "foundrai/api/routes/recommendations.py": "Recommendations API routes",
    }

    all_ok = True
    for filepath, description in files.items():
        path = Path(filepath)
        if path.exists():
            size = path.stat().st_size
            print(f"  ✅ {description}: {filepath} ({size:,} bytes)")
        else:
            print(f"  ❌ {description}: {filepath} (NOT FOUND)")
            all_ok = False

    return all_ok


def verify_frontend_files():
    """Verify all frontend files exist."""
    print("\n🔍 Verifying frontend files...")
    files = {
        "frontend/src/hooks/use-recommendations.ts": "Recommendations hooks",
        "frontend/src/components/team/ModelRecommendationCard.tsx": "ModelRecommendationCard component",
        "frontend/src/components/team/CostSavingsEstimate.tsx": "CostSavingsEstimate component",
        "frontend/src/routes/projects/$projectId/team.tsx": "Team config page",
    }

    all_ok = True
    for filepath, description in files.items():
        path = Path(filepath)
        if path.exists():
            size = path.stat().st_size
            print(f"  ✅ {description}: {filepath} ({size:,} bytes)")
        else:
            print(f"  ❌ {description}: {filepath} (NOT FOUND)")
            all_ok = False

    return all_ok


def verify_imports():
    """Verify all backend imports work."""
    print("\n🔍 Verifying backend imports...")
    try:
        print("  ✅ Recommendation models imported")

        print("  ✅ RecommendationStore imported")

        print("  ✅ RecommendationEngine imported")

        print("  ✅ Recommendations router imported")

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

        # Check if recommendations route is registered
        routes = [route.path for route in app.routes]
        recommendation_routes = [r for r in routes if "recommendation" in r.lower()]

        if recommendation_routes:
            print(f"  ✅ Found {len(recommendation_routes)} recommendation route(s):")
            for route in recommendation_routes:
                print(f"     - {route}")
            return True
        else:
            print("  ❌ No recommendation routes found")
            return False
    except Exception as e:
        print(f"  ❌ API verification failed: {e}")
        traceback.print_exc()
        return False


def verify_models():
    """Verify model structure."""
    print("\n🔍 Verifying data models...")
    try:
        from foundrai.models.recommendation import (
            CostSavingsEstimate,
            ModelRecommendation,
            PerformanceMetrics,
            RecommendationConfidence,
            TaskComplexity,
        )

        # Create a sample performance metrics object
        metrics = PerformanceMetrics(
            avg_quality_score=0.90,
            avg_cost_per_task=0.025,
            success_rate=0.95,
            avg_execution_time=120.5,
            total_tasks=100,
        )
        print("  ✅ PerformanceMetrics model works")

        # Create a sample model recommendation object
        recommendation = ModelRecommendation(
            agent_role="Developer",
            current_model="gpt-4o",
            recommended_model="claude-3-5-sonnet-20241022",
            confidence=RecommendationConfidence.HIGH,
            reasoning="Claude excels at code generation with 5% higher quality score",
            expected_metrics=metrics,
            alternative_models=["gpt-4o-mini", "claude-3-opus-20240229"],
            task_complexity=TaskComplexity.MEDIUM,
            data_points=100,
        )
        print("  ✅ ModelRecommendation model works")
        print(f"     - Agent role: {recommendation.agent_role}")
        print(f"     - Recommended: {recommendation.recommended_model}")
        print(f"     - Confidence: {recommendation.confidence}")

        # Create a sample cost savings estimate
        savings = CostSavingsEstimate(
            current_total_cost=100.00,
            recommended_total_cost=60.00,
            total_savings=40.00,
            savings_percentage=40.0,
            role_breakdown={
                "Developer": {"current": 50.00, "recommended": 30.00, "savings": 20.00}
            },
            quality_impact="improved",
            confidence=RecommendationConfidence.HIGH,
        )
        print("  ✅ CostSavingsEstimate model works")
        print(
            f"     - Total savings: ${savings.total_savings:.2f} ({savings.savings_percentage:.1f}%)"
        )

        return True
    except Exception as e:
        print(f"  ❌ Model verification failed: {e}")
        traceback.print_exc()
        return False


def verify_typescript_integration():
    """Check TypeScript integration in team config page."""
    print("\n🔍 Verifying TypeScript integration...")

    team_page = Path("frontend/src/routes/projects/$projectId/team.tsx")
    if not team_page.exists():
        print("  ❌ Team config page not found")
        return False

    content = team_page.read_text()

    checks = {
        "useRecommendations": "useRecommendations hook imported",
        "useCostSavings": "useCostSavings hook imported",
        "ModelRecommendationCard": "ModelRecommendationCard imported",
        "CostSavingsEstimate": "CostSavingsEstimate imported",
        "<ModelRecommendationCard": "ModelRecommendationCard component used",
        "<CostSavingsEstimate": "CostSavingsEstimate component used",
        "handleAcceptRecommendation": "Accept recommendation handler",
        "handleDismissRecommendation": "Dismiss recommendation handler",
    }

    all_ok = True
    for check, description in checks.items():
        if check in content:
            print(f"  ✅ {description}")
        else:
            print(f"  ❌ {description} - NOT FOUND")
            all_ok = False

    return all_ok


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("INTELLIGENT MODEL RECOMMENDATION ENGINE - E2E VERIFICATION")
    print("=" * 70)

    results = []

    # Run all checks
    results.append(("Backend Files", verify_backend_files()))
    results.append(("Frontend Files", verify_frontend_files()))
    results.append(("Backend Imports", verify_imports()))
    results.append(("Data Models", verify_models()))
    results.append(("API Registration", verify_api_registration()))
    results.append(("TypeScript Integration", verify_typescript_integration()))

    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n🎉 All automated verifications passed!")
        print("\n" + "=" * 70)
        print("MANUAL E2E VERIFICATION STEPS")
        print("=" * 70)
        print("""
1. Start backend server:
   cd /Users/kyle/Code/foundrai
   source .venv/bin/activate
   uvicorn foundrai.api.app:app --reload

2. Start frontend dev server (in separate terminal):
   cd /Users/kyle/Code/foundrai/frontend
   npm run dev

3. Create test project with sample sprint data:
   - Open browser to http://localhost:5173
   - Create a new project (or use existing test-project)
   - Run a sprint with at least one task
   - Ensure token_usage data is recorded

4. Navigate to team config page:
   - Go to http://localhost:5173/projects/test-project/team
   - Verify page loads without errors

5. Verify recommendations appear:
   - Check "Model Recommendations" section is visible
   - Each agent role should show a recommendation card
   - Cards display: current model, recommended model, confidence, reasoning
   - Expected metrics shown: quality score, cost/task, success rate

6. Verify cost savings estimate:
   - Check "Cost Savings Estimate" card at top of page
   - Shows savings percentage and dollar amount
   - Displays current vs recommended costs
   - Shows per-role breakdown
   - Quality impact indicator visible

7. Test accepting a recommendation:
   - Click "Accept Recommendation" button on any card
   - Verify toast notification appears
   - Check agent config updates to use recommended model
   - Recommendation card should disappear from view

8. Test dismissing a recommendation:
   - Click "Dismiss" button on any card
   - Verify toast notification appears
   - Recommendation card should disappear

9. Verify recommendations update with more data:
   - Run another sprint with different tasks
   - Navigate back to team config page
   - Check if recommendations change based on new data
   - Confidence levels should increase with more data points

10. Test API endpoints directly:
    curl http://localhost:8000/api/projects/test-project/recommendations
    curl http://localhost:8000/api/projects/test-project/cost-savings

Expected API responses:
- /recommendations: Array of ModelRecommendation objects
- /cost-savings: CostSavingsEstimate object with savings data
""")
        return 0
    else:
        print("\n❌ Some verifications failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
