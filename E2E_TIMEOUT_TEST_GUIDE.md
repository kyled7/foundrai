# Approval Timeout Expiration - E2E Test Guide

## Overview
This guide provides step-by-step instructions for manually testing the approval timeout expiration flow. This verifies that approvals automatically expire after the configured timeout period when not responded to.

---

## Prerequisites

- Backend server running (`foundrai serve`)
- Frontend dev server running (`cd frontend && npm run dev`)
- Browser with DevTools open (for monitoring WebSocket events)
- SQLite CLI or DB browser (optional, for direct database inspection)

---

## Test Setup: Configure Short Timeout

For testing purposes, we'll configure a **30-second timeout** instead of the default 5 minutes.

### Option 1: Modify Config File (Recommended for Testing)

Create or edit `.foundrai/config.yaml`:

```yaml
team:
  developer:
    enabled: true
    autonomy: REQUIRE_APPROVAL
    approval_timeout_seconds: 30  # Short timeout for testing
    model: "anthropic/claude-sonnet-4-20250514"
  product_manager:
    enabled: true
    autonomy: NOTIFY
    model: "anthropic/claude-sonnet-4-20250514"
```

**Restart the backend server** after modifying the config.

### Option 2: Use Direct Database Manipulation (Advanced)

If you want to test without restarting:
1. Create an approval normally
2. Monitor the database directly
3. Wait for SprintEngine to mark it as expired

---

## Test Scenario 1: Basic Timeout Expiration

### Step 1: Create Sprint with Approval Required

1. Navigate to Projects page in the web dashboard
2. Create a new sprint:
   - **Goal:** "Test approval timeout expiration"
   - **Autonomy Level:** REQUIRE_APPROVAL
   - **Agents:** Enable Developer agent
3. Click "Create Sprint"

**Expected Result:**
- Sprint created successfully
- Sprint ID displayed

---

### Step 2: Trigger Approval Request

1. Start the sprint execution
2. Agent will attempt a task and request approval

**Expected Result:**
- WebSocket event `approval.requested` fires
- ApprovalBanner shows "1 approval pending"
- Browser notification appears (if enabled)
- Sound plays (if enabled)

**Monitor in Browser DevTools:**
```json
{
  "event_type": "approval.requested",
  "approval_id": "...",
  "agent_id": "developer",
  "action_type": "task_execution",
  "title": "..."
}
```

---

### Step 3: Navigate to Approvals Tab

1. Click "Approvals" tab in sprint dashboard
2. View the pending approval

**Expected Result:**
- ApprovalCard displays with countdown timer
- Timer shows "0:30" (or configured timeout in MM:SS format)
- Context displays in readable format
- Approve/Reject buttons visible

---

### Step 4: Wait for Timeout (DO NOT RESPOND)

⚠️ **Important:** Do not click Approve or Reject. Just wait and observe.

**Monitor the countdown timer:**
- [ ] Timer counts down: 0:30 → 0:29 → 0:28 → ... → 0:01 → 0:00
- [ ] Timer updates every second
- [ ] Timer remains visible throughout countdown

**Expected Behavior During Countdown:**
- Countdown displays in amber/yellow color
- Clock icon visible
- Card remains interactive (but don't interact)

---

### Step 5: Verify Timeout Expiration

**After timer reaches 0:00:**

**Expected UI Changes:**
- [ ] ApprovalCard status updates to "expired" or "timed out"
- [ ] Card may change visual appearance (e.g., grayed out)
- [ ] Approve/Reject buttons become disabled OR card disappears from pending list
- [ ] ApprovalBanner pending count decreases: "1 approval pending" → "0 approvals pending"

**Monitor WebSocket Events:**
```json
{
  "event_type": "approval.expired",
  "approval_id": "...",
  "sprint_id": "...",
  "task_id": "..."
}
```

---

### Step 6: Verify Backend Database State

**Using SQLite CLI:**
```bash
sqlite3 .foundrai/data.db
```

```sql
-- Check approval status
SELECT approval_id, status, created_at, resolved_at
FROM approvals
ORDER BY created_at DESC
LIMIT 5;
```

**Expected Database Record:**
```
approval_id         status    created_at              resolved_at
-----------------  --------  ----------------------  ----------------------
<uuid>             expired   2026-03-19T12:30:00Z    2026-03-19T12:30:30Z
```

- [ ] `status` column shows "expired"
- [ ] `resolved_at` timestamp is set (approximately 30 seconds after `created_at`)

---

### Step 7: Verify Agent Task Status

**In the sprint dashboard:**

1. Navigate to "Tasks" tab
2. Find the task that required approval

**Expected Task State:**
- [ ] Task status is **BLOCKED** (not completed)
- [ ] Agent did NOT proceed with task execution
- [ ] Task shows as awaiting approval or blocked due to expired approval

**Check Activity Feed:**
- [ ] Shows "Approval requested" event
- [ ] Shows "Approval expired" event
- [ ] Shows "Task blocked" or similar message

---

### Step 8: Verify Immutability of Expired Approval

**Attempt to approve the expired approval:**

1. If the ApprovalCard is still visible, try clicking "Approve"
2. If the card is hidden, try accessing it via direct URL: `/api/approvals/{approval_id}`

**Expected Behavior:**
- [ ] Approval action fails (409 Conflict or similar error)
- [ ] Error message: "Approval has already been resolved" or "Cannot approve expired approval"
- [ ] Status remains "expired" in database

---

## Test Scenario 2: Multiple Approvals with Different Timeouts

### Setup

Configure different timeouts for different agents:

```yaml
team:
  developer:
    autonomy: REQUIRE_APPROVAL
    approval_timeout_seconds: 30
  qa_engineer:
    autonomy: REQUIRE_APPROVAL
    approval_timeout_seconds: 60
```

### Test Steps

1. Create sprint with both Developer and QA Engineer enabled
2. Start sprint and trigger approval requests from both agents
3. Observe two ApprovalCards with different countdown timers:
   - Developer: 0:30
   - QA Engineer: 1:00

**Expected Results:**
- [ ] Developer approval expires after 30 seconds
- [ ] QA Engineer approval still pending (30 seconds remaining)
- [ ] After 60 seconds total, QA Engineer approval also expires
- [ ] Both show "expired" status
- [ ] Both tasks are BLOCKED

---

## Test Scenario 3: Timeout vs. User Response Race

### Test Steps

1. Create approval with 30-second timeout
2. Wait for countdown to reach **0:05** (5 seconds remaining)
3. **Quickly click "Approve"** before timeout expires

**Expected Results:**

**Case A: User Wins (approval submitted before timeout)**
- [ ] Approval status changes to "approved"
- [ ] Task proceeds to execution
- [ ] No "expired" event logged

**Case B: Timeout Wins (timeout expires first)**
- [ ] Approval status changes to "expired"
- [ ] Approve button click returns 409 Conflict
- [ ] Task is BLOCKED
- [ ] "expired" event logged

---

## Test Scenario 4: Page Reload During Countdown

### Test Steps

1. Create approval request
2. Observe countdown timer (e.g., at 0:20)
3. **Reload the browser page**
4. Navigate back to Approvals tab

**Expected Results:**
- [ ] Countdown timer **recalculates** based on `created_at` timestamp
- [ ] Timer shows correct remaining time (not reset to full timeout)
- [ ] Example: If 10 seconds elapsed before reload, timer shows 0:20 (not 0:30)
- [ ] Timeout expiration still occurs at the correct absolute time

---

## Test Scenario 5: WebSocket Disconnection During Timeout

### Test Steps

1. Create approval request
2. Open Browser DevTools → Network → WS tab
3. Note the WebSocket connection
4. **Stop the backend server** while countdown is active
5. Wait for original timeout to pass
6. **Restart the backend server**
7. Observe frontend behavior

**Expected Results:**
- [ ] Frontend detects WebSocket disconnection
- [ ] Frontend attempts to reconnect
- [ ] After reconnection, approval status reloads from backend
- [ ] If timeout expired during downtime, status shows "expired"
- [ ] UI reflects current state (not stale countdown)

---

## Verification Checklist

### Backend Verification
- [ ] Approval created with `status = 'pending'`
- [ ] After timeout, status updated to `'expired'`
- [ ] `resolved_at` timestamp set to expiration time
- [ ] `approval.expired` event logged in event_log table
- [ ] Expired approvals cannot be approved/rejected (409 Conflict)

### Frontend Verification
- [ ] Countdown timer displays and updates correctly
- [ ] Timer format: MM:SS (e.g., "0:30", "4:58")
- [ ] Timer updates every second
- [ ] UI updates when approval expires (card removed or status changed)
- [ ] ApprovalBanner pending count decreases
- [ ] Cannot interact with expired approval

### Agent Behavior Verification
- [ ] Agent pauses execution while waiting for approval
- [ ] After timeout, agent does NOT proceed with task
- [ ] Task status is BLOCKED (not completed)
- [ ] Agent can proceed with other non-blocked tasks

### Event Log Verification
- [ ] `approval.requested` event logged when approval created
- [ ] `approval.expired` event logged when timeout occurs
- [ ] Events include correct approval_id, sprint_id, task_id
- [ ] Event timestamps are accurate

---

## Troubleshooting

### Issue: Timeout Not Expiring

**Check:**
1. Backend server running and not paused
2. SprintEngine is actively polling (check logs)
3. Agent role has approval timeout configured
4. Database connection working

**Debug:**
```bash
# Check backend logs
tail -f .foundrai/logs/foundrai.log | grep approval
```

Look for:
- "Approval request created"
- "Polling for approval decision"
- "Approval expired"

---

### Issue: Countdown Timer Not Updating

**Check:**
1. JavaScript not paused in DevTools
2. Component mounted correctly (React DevTools)
3. No JavaScript errors in console
4. `created_at` timestamp valid in database

**Debug:**
```javascript
// In browser console
console.log('Approval created at:', approval.created_at);
console.log('Timeout seconds:', approval.timeout_seconds);
console.log('Time remaining:', /* calculated value */);
```

---

### Issue: UI Not Updating After Expiration

**Check:**
1. WebSocket connection active (Network → WS tab)
2. `approval.expired` event received via WebSocket
3. Frontend approval store handling event correctly
4. React component re-rendering on state change

**Debug:**
```javascript
// Monitor WebSocket messages
// In browser console, check if event was received
// Look for approval.expired in WS messages tab
```

---

### Issue: Expired Approval Still Pending in Database

**Possible Causes:**
1. Backend timeout configuration not applied
2. SprintEngine not polling (sprint not executing)
3. Database write failed (check logs)

**Manual Fix:**
```sql
-- Manually expire approval
UPDATE approvals
SET status = 'expired', resolved_at = datetime('now')
WHERE approval_id = '<your-approval-id>';
```

---

## Success Criteria

✅ **Test Passed** if all of the following are true:

1. ✓ Countdown timer displays and updates correctly
2. ✓ After configured timeout, approval status changes to 'expired'
3. ✓ Agent does NOT proceed with task (task status = BLOCKED)
4. ✓ UI updates to reflect expired status
5. ✓ ApprovalBanner pending count decreases
6. ✓ Expired approval cannot be approved/rejected
7. ✓ `approval.expired` event logged in event log
8. ✓ Database record shows `status = 'expired'` with `resolved_at` timestamp
9. ✓ Multiple approvals timeout independently
10. ✓ Countdown persists correctly across page reloads

---

## Configuration Reference

### Short Timeout for Testing (30 seconds)
```yaml
team:
  developer:
    approval_timeout_seconds: 30
```

### Medium Timeout (5 minutes - default)
```yaml
team:
  developer:
    approval_timeout_seconds: 300
```

### Long Timeout (30 minutes)
```yaml
team:
  developer:
    approval_timeout_seconds: 1800
```

### No Timeout (infinite wait)
```yaml
team:
  developer:
    approval_timeout_seconds: null  # or omit the field
```

---

## Next Steps

After successful timeout expiration testing:
1. Mark subtask-4-2 as completed in implementation_plan.json
2. Proceed to subtask-4-3: Rejection flow with feedback testing
3. Complete final QA verification

---

**Document Version:** 1.0
**Last Updated:** 2026-03-19
**Test ID:** subtask-4-2
**Author:** Auto-Claude (Task 006)
