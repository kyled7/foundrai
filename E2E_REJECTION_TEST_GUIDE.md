# Approval Rejection Flow - E2E Test Guide

## Overview
This guide provides step-by-step instructions for manually testing the approval rejection flow with feedback. This verifies that users can reject approval requests with detailed comments that are stored and displayed correctly throughout the system.

---

## Prerequisites

- Backend server running (`foundrai serve`)
- Frontend dev server running (`cd frontend && npm run dev`)
- Browser with DevTools open (for monitoring WebSocket events)
- SQLite CLI or DB browser (optional, for direct database inspection)

---

## Test Scenario 1: Basic Rejection with Feedback

### Step 1: Create Sprint with Approval Required

1. Navigate to Projects page in the web dashboard
2. Create a new sprint:
   - **Goal:** "Test approval rejection flow"
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
  "title": "...",
  "context": { ... }
}
```

---

### Step 3: Navigate to Approvals Tab

1. Click "Approvals" tab in sprint dashboard
2. View the pending approval

**Expected Result:**
- ApprovalCard displays with full details:
  - Agent name and icon
  - Action type badge
  - Task title and description
  - Context (code, files, or structured data)
  - Countdown timer (if timeout configured)
  - Approve and Reject buttons visible and enabled

---

### Step 4: Reject with Detailed Feedback

1. Click the **"Reject"** button
2. Enter detailed feedback in the comment field (if modal appears) OR comment may be optional
3. Example feedback:
   ```
   This approach is too risky. Please:
   1. Add unit tests first
   2. Use a safer algorithm
   3. Add error handling for edge cases
   ```
4. Confirm rejection

**Expected Result:**
- Modal closes (if opened)
- ApprovalCard updates immediately
- Visual feedback indicates rejection (e.g., red accent, "Rejected" badge)

---

### Step 5: Verify UI Updates

**Check ApprovalCard:**
- [ ] Status badge shows "Rejected" (in red or similar color)
- [ ] Rejection comment is displayed
- [ ] Timestamp shows when rejection occurred
- [ ] Approve/Reject buttons are disabled or hidden

**Check ApprovalBanner:**
- [ ] Pending count decreases: "1 approval pending" → "0 approvals pending"
- [ ] Banner may hide if no more pending approvals

**Check Activity Feed:**
- [ ] Shows "Approval requested" event
- [ ] Shows "Approval rejected" event with user comment
- [ ] Events have correct timestamps

---

### Step 6: Verify Backend Database State

**Using SQLite CLI:**
```bash
sqlite3 .foundrai/data.db
```

```sql
-- Check approval status and comment
SELECT approval_id, status, comment, created_at, resolved_at
FROM approvals
ORDER BY created_at DESC
LIMIT 5;
```

**Expected Database Record:**
```
approval_id         status    comment                           created_at              resolved_at
-----------------  --------  -------------------------------   ----------------------  ----------------------
<uuid>             rejected  This approach is too risky...     2026-03-19T12:30:00Z    2026-03-19T12:31:15Z
```

- [ ] `status` column shows "rejected"
- [ ] `comment` column contains the exact feedback text
- [ ] `resolved_at` timestamp is set

---

### Step 7: Verify Agent Task Status

**In the sprint dashboard:**

1. Navigate to "Tasks" tab
2. Find the task that required approval

**Expected Task State:**
- [ ] Task status is **BLOCKED** (not completed)
- [ ] Agent did NOT proceed with task execution
- [ ] Task shows rejection reason or awaiting re-approval

**Check Activity Feed:**
- [ ] Shows "Approval requested" event
- [ ] Shows "Approval rejected" event with comment
- [ ] Shows "Task blocked" or similar message
- [ ] Agent may log acknowledgment of rejection

---

### Step 8: Verify Immutability of Rejected Approval

**Attempt to approve the rejected approval:**

1. Refresh the page to ensure latest state
2. Navigate back to Approvals tab
3. Try clicking "Approve" on the rejected approval (if button is visible)

**Expected Behavior:**
- [ ] Approve button is disabled or not shown
- [ ] If somehow clicked (via console/API), returns 409 Conflict error
- [ ] Error message: "Approval has already been resolved"
- [ ] Status remains "rejected" in database

**Test via API (optional):**
```bash
# Try to approve rejected approval
curl -X POST http://localhost:8420/api/approvals/{approval_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"comment": "Changed my mind"}'
```

**Expected Response:**
```json
{
  "detail": "Approval already resolved"
}
```
Status: 409 Conflict

---

## Test Scenario 2: Rejection Without Comment

### Test Steps

1. Create approval request (same as Scenario 1, Steps 1-3)
2. Click "Reject" button
3. Leave comment field empty (or skip modal if optional)
4. Confirm rejection

**Expected Results:**
- [ ] Rejection succeeds (no comment required)
- [ ] Status changes to "rejected"
- [ ] `comment` field in database is empty string or NULL
- [ ] UI shows "No comment provided" or similar message
- [ ] Agent receives rejection without feedback

---

## Test Scenario 3: Multiple Approvals with Mixed Decisions

### Test Steps

1. Configure sprint with multiple agents or tasks requiring approval
2. Trigger 3 approval requests:
   - Approval A: Developer task
   - Approval B: Code review
   - Approval C: Deployment
3. Handle approvals differently:
   - **Approve A** with comment: "Looks good!"
   - **Reject B** with comment: "Code quality issues found"
   - **Leave C pending**

**Expected Results:**

**ApprovalBanner:**
- [ ] Shows "1 approval pending" (only C)

**Approvals Tab:**
- [ ] Approval A: Shows "Approved" badge with comment "Looks good!"
- [ ] Approval B: Shows "Rejected" badge with comment "Code quality issues found"
- [ ] Approval C: Shows "Pending" badge with countdown timer

**Database:**
```sql
SELECT approval_id, status, comment FROM approvals;
```
- [ ] A: status='approved', comment='Looks good!'
- [ ] B: status='rejected', comment='Code quality issues found'
- [ ] C: status='pending', comment=NULL

**Agent Tasks:**
- [ ] Task A: Proceeds to execution (approved)
- [ ] Task B: Blocked (rejected)
- [ ] Task C: Still waiting (pending)

---

## Test Scenario 4: Long Feedback Comment

### Test Setup

Prepare a detailed, multi-line rejection comment:
```
This code needs significant improvements:

1. Error handling: Add try-catch blocks around all API calls
2. Input validation: Validate all user inputs before processing
3. Performance: The current algorithm has O(n²) complexity - needs optimization
4. Security: SQL injection vulnerability in line 42 - use parameterized queries
5. Testing: Add unit tests for all edge cases
6. Documentation: Add docstrings to all public methods
7. Code style: Follow PEP 8 conventions consistently
8. Dependencies: Update deprecated libraries to latest versions

Please address these issues and resubmit for approval.
```

### Test Steps

1. Create approval request
2. Click "Reject"
3. Paste the long comment (500+ characters)
4. Confirm rejection

**Expected Results:**
- [ ] Comment is accepted (no length limit error)
- [ ] Full comment stored in database
- [ ] UI displays full comment (may be scrollable or collapsed)
- [ ] Formatting preserved (line breaks, numbering)
- [ ] No truncation or corruption

**Verify in UI:**
- [ ] Comment is readable
- [ ] Has scroll or "Show more" if very long
- [ ] Copy/paste works correctly

---

## Test Scenario 5: Special Characters in Comment

### Test Setup

Prepare comment with special characters:
```
Issues found:
- Code contains "quotes" and 'apostrophes'
- SQL injection: WHERE user='${userInput}' <-- dangerous!
- Use this instead: `WHERE user = ?` with parameterized queries
- Math symbols: x > 10 && y < 20
- Newlines, tabs, and other escapes
- Unicode: 🚀 Ready to launch? ✅ Yes!
```

### Test Steps

1. Create approval request
2. Click "Reject"
3. Paste comment with special characters
4. Confirm rejection

**Expected Results:**
- [ ] All special characters accepted
- [ ] No encoding/escaping errors
- [ ] Quotes don't break JSON parsing
- [ ] Unicode emoji preserved
- [ ] HTML/SQL special chars don't cause issues
- [ ] Newlines and formatting preserved

---

## Test Scenario 6: Rejection → Agent Response Flow

This scenario tests the complete feedback loop.

### Test Steps

1. Create approval request for a code implementation task
2. Reject with specific feedback:
   ```
   Please add input validation for the email field.
   Current implementation doesn't check for proper format.
   ```
3. Observe agent behavior after rejection

**Expected Results:**

**Immediate Response:**
- [ ] Agent receives rejection event via SprintEngine
- [ ] Task status changes to BLOCKED
- [ ] Agent does NOT proceed with original task

**Agent Next Steps (if implemented):**
- [ ] Agent may acknowledge rejection in activity feed
- [ ] Agent may create a new task addressing feedback
- [ ] Agent may request human clarification
- [ ] Sprint may continue with other tasks

**Event Log:**
```sql
SELECT event_type, agent_id, data FROM event_log
WHERE sprint_id = '...'
ORDER BY timestamp DESC;
```

- [ ] Event: `approval.requested`
- [ ] Event: `approval.rejected` (with comment in data)
- [ ] Event: `task.blocked`
- [ ] Event: `agent.acknowledged_rejection` (if implemented)

---

## Test Scenario 7: Page Reload During Rejection

### Test Steps

1. Create approval request
2. Click "Reject" and type feedback comment
3. **Before confirming**, reload the browser page
4. Navigate back to Approvals tab
5. Reject the approval again with feedback

**Expected Results:**
- [ ] Draft comment is lost (expected - no autosave)
- [ ] Approval still shows "Pending" (not rejected yet)
- [ ] Can successfully reject after reload
- [ ] No duplicate rejection events

---

## Test Scenario 8: WebSocket Disconnection During Rejection

### Test Steps

1. Create approval request
2. Open Browser DevTools → Network → WS tab
3. Note the WebSocket connection
4. **Stop the backend server** while approval is pending
5. Try to reject the approval in UI
6. **Restart the backend server**
7. Observe behavior

**Expected Results:**

**During Disconnection:**
- [ ] Frontend detects WebSocket disconnection
- [ ] UI shows connection lost indicator (if implemented)
- [ ] Reject button may be disabled or show warning

**After Reconnection:**
- [ ] Frontend reconnects to WebSocket
- [ ] Approval status reloads from backend
- [ ] If rejection was attempted during downtime, it may have failed
- [ ] User can retry rejection

**Best Case (with retry logic):**
- [ ] Frontend queues rejection request
- [ ] Sends it after reconnection
- [ ] Approval is rejected successfully

---

## Verification Checklist

### Backend Verification
- [ ] Approval created with `status = 'pending'`
- [ ] After rejection, status updated to `'rejected'`
- [ ] `comment` field stores feedback text exactly
- [ ] `resolved_at` timestamp set to rejection time
- [ ] `approval.rejected` event logged in event_log table
- [ ] Rejected approvals cannot be approved/rejected again (409 Conflict)

### Frontend Verification
- [ ] Reject button visible and enabled for pending approvals
- [ ] Comment input field available (modal or inline)
- [ ] Rejection updates UI immediately (no page reload needed)
- [ ] Rejected approval shows "Rejected" badge with red accent
- [ ] Rejection comment displayed in ApprovalCard
- [ ] ApprovalBanner pending count decreases
- [ ] Cannot interact with rejected approval
- [ ] Activity feed shows rejection event with comment

### Agent Behavior Verification
- [ ] Agent pauses execution while waiting for approval
- [ ] After rejection, agent does NOT proceed with task
- [ ] Task status is BLOCKED (not completed)
- [ ] Agent can proceed with other non-blocked tasks
- [ ] Agent may log acknowledgment of rejection

### Event Log Verification
- [ ] `approval.requested` event logged when approval created
- [ ] `approval.rejected` event logged when rejected
- [ ] Event data includes:
  - `approval_id`
  - `sprint_id`
  - `task_id`
  - `agent_id`
  - `comment` (rejection feedback)
- [ ] Event timestamps are accurate
- [ ] Events appear in activity feed in correct order

### Database Integrity Verification
```sql
-- Check data integrity
SELECT
  approval_id,
  status,
  LENGTH(comment) as comment_length,
  created_at,
  resolved_at,
  (JULIANDAY(resolved_at) - JULIANDAY(created_at)) * 86400 as resolution_time_seconds
FROM approvals
WHERE status = 'rejected'
ORDER BY created_at DESC;
```

- [ ] All rejected approvals have `resolved_at` timestamp
- [ ] `resolution_time_seconds` is positive and reasonable
- [ ] Comments are not truncated or corrupted
- [ ] No orphaned records (all have valid `sprint_id`)

---

## Troubleshooting

### Issue: Reject Button Not Working

**Check:**
1. Approval status is 'pending' (not already resolved)
2. JavaScript not paused in DevTools
3. No console errors blocking interaction
4. WebSocket connection active
5. Backend server running

**Debug:**
```javascript
// In browser console
console.log('Approval status:', approval.status);
console.log('WebSocket state:', ws.readyState);
```

---

### Issue: Comment Not Saved

**Check:**
1. Request payload includes `comment` field
2. Backend received POST request
3. Database write succeeded (check logs)
4. No JSON encoding issues

**Debug:**
```bash
# Check backend logs
tail -f .foundrai/logs/foundrai.log | grep reject

# Check database
sqlite3 .foundrai/data.db "SELECT comment FROM approvals WHERE approval_id = '...'"
```

---

### Issue: UI Not Updating After Rejection

**Check:**
1. WebSocket connection active (Network → WS tab)
2. `approval.rejected` event received via WebSocket
3. Frontend approval store handling event correctly
4. React component re-rendering on state change

**Debug:**
```javascript
// Monitor WebSocket messages
// In browser console, check if event was received
// Look for approval.rejected in WS messages tab

// Check store state
import { useApprovalStore } from '@/stores/approvalStore';
console.log('Approvals:', useApprovalStore.getState().approvals);
```

---

### Issue: Agent Continues After Rejection

**Possible Causes:**
1. Agent not checking approval status before task execution
2. SprintEngine not polling approval results
3. Task already started before rejection
4. Approval gate not properly implemented

**Debug:**
```bash
# Check event log
sqlite3 .foundrai/data.db "
  SELECT event_type, agent_id, timestamp, data
  FROM event_log
  WHERE sprint_id = '...'
  ORDER BY timestamp;
"
```

Look for sequence:
1. `task.started`
2. `approval.requested`
3. `approval.rejected`
4. `task.blocked` (should appear, not `task.completed`)

---

## Success Criteria

✅ **Test Passed** if all of the following are true:

1. ✓ User can reject pending approval requests
2. ✓ Rejection comment can be provided (optional)
3. ✓ Comment is stored in database exactly as entered
4. ✓ UI updates immediately to show "Rejected" status
5. ✓ Rejection comment is displayed in ApprovalCard
6. ✓ ApprovalBanner pending count decreases
7. ✓ Agent does NOT proceed with task (task status = BLOCKED)
8. ✓ `approval.rejected` event logged with comment
9. ✓ Database record shows `status = 'rejected'` with `resolved_at` timestamp
10. ✓ Rejected approval cannot be approved or rejected again (immutable)
11. ✓ Multiple approvals can have mixed decisions (approve/reject)
12. ✓ Long comments (500+ chars) are handled correctly
13. ✓ Special characters and formatting preserved in comments
14. ✓ WebSocket events trigger UI updates in real-time

---

## Configuration Reference

### Enable Approval Gate for Testing

**Configure agent with REQUIRE_APPROVAL autonomy:**

```yaml
# .foundrai/config.yaml
team:
  developer:
    enabled: true
    autonomy: REQUIRE_APPROVAL
    approval_timeout_seconds: 300  # 5 minutes (optional)
    model: "anthropic/claude-sonnet-4-20250514"
```

### Approval Decision API Endpoints

**Approve:**
```bash
POST /api/approvals/{approval_id}/approve
{
  "comment": "Looks good!"  # Optional
}
```

**Reject:**
```bash
POST /api/approvals/{approval_id}/reject
{
  "comment": "Please fix issues"  # Optional
}
```

**Get Details:**
```bash
GET /api/approvals/{approval_id}
```

Response includes `comment` field with feedback.

---

## Next Steps

After successful rejection flow testing:
1. Mark subtask-4-3 as completed in implementation_plan.json
2. Review all Phase 4 E2E tests (approval flow, timeout, rejection)
3. Complete final QA verification and documentation
4. Prepare for production deployment

---

**Document Version:** 1.0
**Last Updated:** 2026-03-19
**Test ID:** subtask-4-3
**Author:** Auto-Claude (Task 006)
