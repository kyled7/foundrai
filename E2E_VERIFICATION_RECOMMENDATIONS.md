# End-to-End Verification Guide: Intelligent Model Recommendation Engine

This guide provides step-by-step instructions for manually verifying the intelligent model recommendation engine feature.

## Prerequisites

1. Backend server running
2. Frontend dev server running
3. Test project with historical sprint/task data

## Automated Verification

First, run the automated verification script:

```bash
python3 verify_recommendations.py
```

Expected results:
- ✅ Backend Files - All files exist
- ✅ Frontend Files - All components created
- ✅ TypeScript Integration - All hooks and components properly integrated
- ⚠️ Backend Imports - May fail if not in virtualenv (expected)

## Manual E2E Verification Steps

### Step 1: Start Services

**Terminal 1 - Backend:**
```bash
cd /Users/kyle/Code/foundrai
source .venv/bin/activate
uvicorn foundrai.api.app:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd /Users/kyle/Code/foundrai/frontend
npm run dev
```

Verify:
- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:5173
- [ ] No startup errors in either terminal

### Step 2: Create Test Data

You need historical performance data for the recommendation engine to work. This requires:

**Option A: Use existing project with sprint data**
- Navigate to existing project that has completed sprints
- Skip to Step 3

**Option B: Create new test data**
```bash
# In backend terminal, open Python shell
python3
```

```python
from foundrai.persistence.database import Database
from foundrai.models.token_usage import TokenUsage
from datetime import datetime

db = Database("test.db")

# Create sample token usage data for different agents and models
test_data = [
    # Developer with GPT-4o (current)
    TokenUsage(
        agent_role="Developer",
        model="gpt-4o",
        input_tokens=1000,
        output_tokens=500,
        total_cost=0.025,
        task_id="task-1",
        sprint_id="sprint-1",
        project_id="test-project",
        timestamp=datetime.now()
    ),
    # Developer with Claude (better performance)
    TokenUsage(
        agent_role="Developer",
        model="claude-3-5-sonnet-20241022",
        input_tokens=1000,
        output_tokens=500,
        total_cost=0.018,
        task_id="task-2",
        sprint_id="sprint-1",
        project_id="test-project",
        timestamp=datetime.now()
    ),
    # PM with Claude (current)
    TokenUsage(
        agent_role="ProductManager",
        model="claude-3-5-sonnet-20241022",
        input_tokens=800,
        output_tokens=400,
        total_cost=0.015,
        task_id="task-3",
        sprint_id="sprint-1",
        project_id="test-project",
        timestamp=datetime.now()
    ),
    # QA with GPT-4o-mini (cheaper alternative)
    TokenUsage(
        agent_role="QAEngineer",
        model="gpt-4o-mini",
        input_tokens=500,
        output_tokens=300,
        total_cost=0.005,
        task_id="task-4",
        sprint_id="sprint-1",
        project_id="test-project",
        timestamp=datetime.now()
    ),
]

# Save test data
for usage in test_data:
    db.token_usage.create(usage)

print("Test data created!")
```

### Step 3: Navigate to Team Config Page

1. Open browser to http://localhost:5173
2. Navigate to Projects
3. Select "test-project" (or your test project)
4. Click on "Team Configuration" or navigate to `/projects/test-project/team`

**Verify:**
- [ ] Page loads without errors
- [ ] No console errors in browser DevTools
- [ ] Existing agent configuration cards are visible

### Step 4: Verify Model Recommendations Section

Look for the "Model Recommendations" section above the agent configuration cards.

**Verify each recommendation card shows:**
- [ ] Agent role name with avatar icon
- [ ] ✨ Sparkles icon indicating AI recommendation
- [ ] Current model badge
- [ ] Recommended model badge (different color)
- [ ] Confidence level indicator (High/Medium/Low/Insufficient Data)
- [ ] Reasoning text explaining why this model is recommended
- [ ] Expected metrics section with:
  - Quality Score (with trend arrow)
  - Cost per Task (with trend arrow)
  - Success Rate (with trend arrow)
- [ ] Alternative models list (if available)
- [ ] "Accept Recommendation" button (green)
- [ ] "Dismiss" button (gray)

**Expected behavior:**
- Cards only shown for agents where recommended model differs from current
- Confidence indicator color-coded:
  - 🟢 Green = HIGH confidence
  - 🟡 Yellow = MEDIUM confidence
  - 🟠 Orange = LOW confidence
  - ⚪ Gray = INSUFFICIENT_DATA

### Step 5: Verify Cost Savings Estimate

Look for the "Cost Savings Estimate" card at the top of the recommendations section.

**Verify the card shows:**
- [ ] Large prominent savings percentage (e.g., "40% Savings")
- [ ] Total savings amount in dollars
- [ ] Current total cost
- [ ] Recommended total cost
- [ ] Per-role breakdown section with:
  - Agent role name
  - Current cost
  - Recommended cost
  - Savings amount (with green arrow)
- [ ] Quality Impact indicator:
  - ✓ "Quality Improved" (if better)
  - ⚠ "Quality May Degrade" (if worse)
- [ ] Confidence level badge

**Expected calculations:**
- Savings percentage = (Total Savings / Current Cost) × 100
- Individual role savings should sum to total savings
- Green color scheme for positive savings

### Step 6: Test Accepting a Recommendation

1. Find a recommendation card with "Accept Recommendation" button
2. Click the button

**Verify:**
- [ ] Toast notification appears: "Applied recommendation for [AgentRole]"
- [ ] Agent configuration section updates to show new model
- [ ] Recommendation card disappears (or is removed from view)
- [ ] Cost savings estimate updates (if multiple recommendations)
- [ ] No console errors

**Backend check:**
```bash
# Check that agent config was updated
curl http://localhost:8000/api/projects/test-project/agents/Developer
```

Expected: `"model": "claude-3-5-sonnet-20241022"` (or whatever was recommended)

### Step 7: Test Dismissing a Recommendation

1. Find another recommendation card
2. Click "Dismiss" button

**Verify:**
- [ ] Toast notification appears: "Dismissed recommendation for [AgentRole]"
- [ ] Recommendation card disappears from view
- [ ] Agent configuration unchanged (still uses current model)
- [ ] Cost savings estimate updates (excludes dismissed recommendation)
- [ ] No console errors

### Step 8: Verify API Endpoints Directly

**Test GET /recommendations endpoint:**
```bash
curl http://localhost:8000/api/projects/test-project/recommendations | jq
```

**Verify response contains:**
- [ ] Array of recommendation objects
- [ ] Each has: agent_role, current_model, recommended_model, confidence, reasoning
- [ ] expected_metrics with: avg_quality_score, avg_cost_per_task, success_rate
- [ ] alternative_models array
- [ ] HTTP 200 status

**Test POST /cost-savings endpoint:**
```bash
curl -X POST http://localhost:8000/api/projects/test-project/cost-savings \
  -H "Content-Type: application/json" \
  -d '{
    "current_config": {
      "Developer": "gpt-4o",
      "ProductManager": "claude-3-5-sonnet-20241022",
      "QAEngineer": "gpt-4o"
    },
    "recommended_config": {
      "Developer": "claude-3-5-sonnet-20241022",
      "QAEngineer": "gpt-4o-mini"
    }
  }' | jq
```

**Verify response contains:**
- [ ] current_total_cost (number)
- [ ] recommended_total_cost (number)
- [ ] total_savings (number)
- [ ] savings_percentage (number)
- [ ] role_breakdown (object with per-agent costs)
- [ ] quality_impact ("improved", "degraded", or "neutral")
- [ ] confidence level
- [ ] HTTP 200 status

### Step 9: Verify Recommendations Update with More Data

This verifies the recommendation engine adapts to new historical data.

1. Create more token usage entries (either run another sprint or add test data)
2. Navigate away from team config page
3. Navigate back to team config page
4. Check if recommendations changed

**Verify:**
- [ ] Recommendations may differ based on new data
- [ ] Confidence levels increase with more data points
- [ ] New models may be recommended if performance shifts
- [ ] "INSUFFICIENT_DATA" recommendations may become "LOW"/"MEDIUM"/"HIGH"

**Add more test data:**
```python
# Run in Python shell
from foundrai.persistence.database import Database
from foundrai.models.token_usage import TokenUsage
from datetime import datetime

db = Database("test.db")

# Add 50 more Developer tasks with Claude showing better performance
for i in range(50):
    usage = TokenUsage(
        agent_role="Developer",
        model="claude-3-5-sonnet-20241022",
        input_tokens=1000,
        output_tokens=500,
        total_cost=0.015,
        task_id=f"task-dev-{i}",
        sprint_id="sprint-2",
        project_id="test-project",
        timestamp=datetime.now()
    )
    db.token_usage.create(usage)

print("Added 50 more data points!")
```

Refresh the team page and verify confidence level increases.

### Step 10: Edge Cases and Error Handling

**Test with no historical data:**
1. Create a brand new project with no sprints
2. Navigate to team config page
3. Verify:
   - [ ] No recommendations section shown (or empty state)
   - [ ] No cost savings estimate shown
   - [ ] No errors in console

**Test with insufficient data:**
1. Project with only 1-2 tasks
2. Verify:
   - [ ] Recommendations may show "INSUFFICIENT_DATA" confidence
   - [ ] Reasoning explains lack of data
   - [ ] Still provides recommendations based on defaults/heuristics

**Test with all agents using optimal models:**
1. Manually set all agents to their recommended models
2. Refresh team config page
3. Verify:
   - [ ] No recommendation cards shown (all models already optimal)
   - [ ] Cost savings estimate shows 0% or is hidden
   - [ ] No errors

## Acceptance Criteria Verification

Go through each acceptance criterion from the spec:

- [ ] ✅ Team configuration UI shows model recommendations per agent role
- [ ] ✅ Recommendations consider: task type, quality requirements, and cost constraints
- [ ] ✅ Historical performance data informs recommendations (which models succeeded for which tasks)
- [ ] ✅ Cost savings estimate shown: 'Recommended config saves ~40% vs all-GPT-4o'
- [ ] ✅ User can accept, modify, or ignore recommendations
- [ ] ✅ Recommendations update as more sprint data accumulates

## Success Criteria

All of the following should be true:

1. ✅ All automated verification checks pass (except virtualenv-dependent ones)
2. ✅ All UI components render without errors
3. ✅ Recommendations are based on actual historical data
4. ✅ Cost savings calculations are accurate
5. ✅ Accept/Dismiss actions work correctly
6. ✅ API endpoints return correct data structures
7. ✅ Recommendations adapt to new data
8. ✅ Edge cases handled gracefully
9. ✅ No console errors or warnings
10. ✅ All acceptance criteria met

## Troubleshooting

### Recommendations not showing
- Check if there's historical token_usage data
- Verify agent roles match between token_usage and team config
- Check browser console for API errors

### Cost savings not calculating
- Ensure recommendations exist
- Check that recommended models differ from current models
- Verify API endpoint returns valid response

### Accept recommendation not working
- Check that updateAgent mutation is working
- Verify toast notifications are configured
- Check network tab for API call success

### TypeScript errors
- Run `cd frontend && npx tsc --noEmit`
- Check all types are imported from `@/lib/types`
- Verify API client methods exist in `@/lib/api.ts`

## Cleanup

After verification:

```bash
# Stop services
Ctrl+C in both terminals

# Optional: Remove test data
rm test.db test.db-shm test.db-wal
```

## Next Steps

If all verifications pass:
1. Update implementation_plan.json to mark subtask-5-1 as completed
2. Create git commit
3. Update build-progress.txt with verification results
4. Consider creating unit/integration tests for regression prevention
