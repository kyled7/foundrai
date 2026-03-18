# End-to-End Verification Guide
## Human Approval Gateway UI - E2E Testing

This guide provides step-by-step instructions for manually verifying the complete approval flow from backend to frontend.

---

## Prerequisites

Before starting, ensure you have:
- Python 3.11+ with virtual environment activated
- Node.js/npm installed
- No other services running on ports 8420 (backend) or 5173 (frontend)

---

## Phase 1: Server Setup

### Step 1.1: Start Backend Server

```bash
# Activate virtual environment
source .venv/bin/activate

# Start the backend server
foundrai serve
```

**Expected Result:**
- Server starts on http://localhost:8420
- Console shows: "Application startup complete"
- No error messages

**Verification:**
```bash
curl http://localhost:8420/api/health
# Should return: {"status": "healthy"}
```

---

### Step 1.2: Start Frontend Dev Server

```bash
# In a new terminal
cd frontend
npm run dev
```

**Expected Result:**
- Dev server starts on http://localhost:5173
- Console shows: "Local: http://localhost:5173/"
- No compilation errors

**Verification:**
- Open http://localhost:5173 in your browser
- Should see FoundrAI dashboard without errors
- Check browser console - no errors

---

## Phase 2: Sprint Configuration

### Step 2.1: Create Sprint with Approval Required

1. Navigate to Projects page
2. Click "Create Sprint" or use existing project
3. In Sprint Configuration:
   - Set **Autonomy Level** to `REQUIRE_APPROVAL`
   - Define a simple goal (e.g., "Create a hello world function")
   - Configure at least one agent (e.g., Developer)

**Expected Result:**
- Sprint created successfully
- Autonomy level shows "Require Approval" badge
- Sprint appears in dashboard

---

### Step 2.2: Start Sprint Execution

1. Navigate to the sprint page
2. Click "Start Sprint" button
3. Monitor the sprint dashboard

**Expected Result:**
- Sprint status changes to "running"
- Agents begin processing tasks
- Activity feed shows agent actions

---

## Phase 3: Approval Request Verification

### Step 3.1: Verify `approval.requested` Event

**Watch for:**
- When an agent attempts an action requiring approval
- WebSocket event `approval.requested` fires

**How to Monitor:**
1. Open browser DevTools → Network → WS tab
2. Look for WebSocket connection to backend
3. Filter messages for "approval.requested"

**Expected WebSocket Message:**
```json
{
  "event_type": "approval.requested",
  "approval_id": "...",
  "agent_id": "developer",
  "action_type": "code_write",
  "title": "Write code for hello world function",
  "description": "...",
  "context": {...}
}
```

---

### Step 3.2: Verify ApprovalBanner

**Location:** Top of sprint dashboard

**Expected Behavior:**
- Banner appears with amber/yellow color
- Shows pending approval count (e.g., "1 approval pending")
- Badge updates in real-time as approvals are added

**Visual Checks:**
- [ ] Banner is visible
- [ ] Pending count is accurate
- [ ] Color scheme is amber (light theme) or amber-dark (dark theme)

---

### Step 3.3: Verify Browser Notification (Optional)

**Requirements:**
- Browser notification permissions granted
- Settings → Notifications → "Browser Notifications" enabled
- Settings → Notifications → "Notify on Approval Request" enabled

**Expected Behavior:**
1. Browser notification appears (system notification)
2. Shows: "Approval Required"
3. Message: "developer needs approval for code_write"
4. Includes FoundrAI icon (if configured)

**Note:** If permissions not granted, browser will prompt for permission on first notification attempt.

---

### Step 3.4: Verify Sound Notification (Optional)

**Requirements:**
- Settings → Notifications → "Sound Notifications" enabled
- Browser allows audio playback

**Expected Behavior:**
- Notification sound plays when approval is requested
- Sound is brief, non-intrusive
- Volume respects system settings

**Debug:**
- If no sound: Check browser console for audio playback errors
- Verify audio file exists: `frontend/src/assets/notification.mp3`

---

## Phase 4: Approval UI Verification

### Step 4.1: Navigate to Approvals Tab

1. Click "Approvals" tab in sprint dashboard
2. View pending approval queue

**Expected Result:**
- Tab shows pending approvals list
- Each approval displayed as a card

---

### Step 4.2: Verify ApprovalCard Details

**Visual Elements:**

1. **Agent Avatar**
   - [ ] Shows agent icon/avatar
   - [ ] Agent name visible

2. **Approval Title**
   - [ ] Clear, descriptive title
   - [ ] Action type indicated (e.g., "code_write", "file_delete")

3. **Countdown Timer**
   - [ ] Clock icon visible
   - [ ] Time format: MM:SS (e.g., "4:58")
   - [ ] Updates every second
   - [ ] Default: 5 minutes (300 seconds)
   - [ ] Color: Amber/yellow

4. **Description**
   - [ ] Shows what the agent wants to do
   - [ ] Readable, not truncated

---

### Step 4.3: Verify Context Display

**Context Rendering Tests:**

The ContextRenderer should intelligently format different types of context:

**Test 1: Code Block**
- If context contains code (e.g., Python, JavaScript)
- [ ] Code displayed in monospace font
- [ ] Syntax highlighting (if available)
- [ ] Collapsible section for long code

**Test 2: File Diff**
- If context contains file changes
- [ ] Additions shown in green
- [ ] Deletions shown in red
- [ ] Line numbers visible

**Test 3: File Paths**
- If context contains file paths
- [ ] Paths in monospace font
- [ ] Easily readable

**Test 4: URLs**
- If context contains URLs
- [ ] Links are clickable
- [ ] Open in new tab

**Test 5: Structured Data**
- If context is JSON/object
- [ ] Formatted with indentation
- [ ] Nested structures visible
- [ ] Collapsible for complex data

---

### Step 4.4: Verify Feedback Input

1. **Comment Textarea**
   - [ ] Visible and editable
   - [ ] Placeholder text: "Optional feedback for the agent..."
   - [ ] Supports multi-line input
   - [ ] Dark mode styling correct

---

### Step 4.5: Verify Action Buttons

**Buttons Present:**
- [ ] "✓ Approve" button (green)
- [ ] "✗ Reject" button (red)

**Button States:**
- [ ] Enabled when pending
- [ ] Disabled during loading
- [ ] Hover effects work

---

## Phase 5: Approval Decision Flow

### Step 5.1: Test Approval with Comment

1. Type a comment in the feedback textarea (e.g., "Looks good!")
2. Click "✓ Approve" button

**Expected Behavior:**
- [ ] Button shows loading state
- [ ] API request sent to `/approvals/{id}/approve`
- [ ] Approval status changes to "approved"
- [ ] ApprovalCard disappears from pending list
- [ ] Agent proceeds with task
- [ ] Activity feed shows approval event
- [ ] Comment logged in database

**Verify in Backend:**
```bash
# If using SQLite, check database
sqlite3 .foundrai/foundrai.db "SELECT * FROM approvals WHERE approval_id = 'YOUR_APPROVAL_ID';"
```

**Expected DB Record:**
- `status`: "approved"
- `comment`: Your comment text
- `resolved_at`: ISO timestamp

---

### Step 5.2: Verify Agent Continuation

**After Approval:**
- [ ] Agent receives approval decision
- [ ] Agent proceeds with original action
- [ ] Task completes successfully
- [ ] Results visible in sprint dashboard

---

### Step 5.3: Test Rejection Flow

Create another approval (trigger new action), then:

1. Type rejection feedback (e.g., "Please use a different approach")
2. Click "✗ Reject" button

**Expected Behavior:**
- [ ] Button shows loading state
- [ ] API request sent to `/approvals/{id}/reject`
- [ ] Approval status changes to "rejected"
- [ ] ApprovalCard disappears from pending list
- [ ] Agent receives rejection
- [ ] Agent handles rejection (may retry or abort)
- [ ] Activity feed shows rejection event
- [ ] Feedback comment logged

---

## Phase 6: Edge Cases & Advanced Testing

### Step 6.1: Multiple Pending Approvals

**Test:**
- Configure sprint to require multiple approvals
- Trigger 3+ approval requests

**Verify:**
- [ ] ApprovalBanner shows correct count (e.g., "3 approvals pending")
- [ ] All approvals visible in queue
- [ ] Can approve/reject each independently
- [ ] Count decreases as each is resolved

---

### Step 6.2: Timeout Behavior

**Note:** Default timeout is 5 minutes (300 seconds)

**Test:**
1. Create approval request
2. Wait for countdown to reach 0:00
3. Observe behavior

**Expected (Current Implementation):**
- [ ] Timer shows 0:00
- [ ] Approval may auto-expire (check backend logs)
- [ ] UI updates to show expired status

**Note:** Full timeout auto-approval/rejection depends on backend configuration.

---

### Step 6.3: WebSocket Reconnection

**Test:**
1. Open sprint with pending approval
2. Stop backend server
3. Restart backend server

**Verify:**
- [ ] Frontend detects disconnection
- [ ] WebSocket reconnects automatically
- [ ] Approval state reloads
- [ ] No data loss

---

### Step 6.4: Dark Mode Consistency

**Test:**
1. Toggle dark mode (if available in settings)
2. Check all approval UI elements

**Verify:**
- [ ] ApprovalBanner colors adapt to dark theme
- [ ] ApprovalCard styling works in dark mode
- [ ] ContextRenderer code blocks readable
- [ ] Text contrast sufficient
- [ ] No visual glitches

---

## Phase 7: Settings Verification

### Step 7.1: Navigate to Settings

1. Go to Settings page
2. Find "Notifications" section

**Expected Settings:**

**General:**
- [ ] "Sound Notifications" toggle
- [ ] "Browser Notifications" toggle

**Events:**
- [ ] "Approval Requests" toggle
- [ ] "Sprint Completion" toggle
- [ ] "Errors" toggle
- [ ] "Budget Warnings" toggle

---

### Step 7.2: Test Notification Settings Persistence

1. Toggle "Browser Notifications" OFF
2. Toggle "Approval Requests" OFF
3. Refresh page
4. Return to settings

**Verify:**
- [ ] Settings retained after refresh
- [ ] Toggles show correct state
- [ ] Settings saved to backend

**Test Behavior:**
1. Create new approval with notifications OFF
2. Verify NO browser notification appears
3. Verify NO sound plays
4. Toggle settings back ON
5. Create another approval
6. Verify notifications/sound work again

---

## Phase 8: Console & Error Checking

### Step 8.1: Browser Console Verification

**During entire E2E test:**

**Expected:**
- [ ] No JavaScript errors
- [ ] No React warnings (or only minor development warnings)
- [ ] WebSocket connection successful
- [ ] API requests return 200/201/204

**Acceptable Warnings:**
- React development mode warnings
- HMR (Hot Module Replacement) logs

**Unacceptable Errors:**
- Uncaught exceptions
- Network errors (except intentional disconnection tests)
- Component render errors

---

### Step 8.2: Network Tab Verification

**Check API Calls:**

1. `/api/approvals/{sprint_id}` - GET list
   - [ ] Returns approvals array
   - [ ] Includes pending_count

2. `/api/approvals/{approval_id}` - GET detail
   - [ ] Returns full approval object
   - [ ] Context parsed correctly

3. `/api/approvals/{approval_id}/approve` - POST
   - [ ] Accepts comment in body
   - [ ] Returns success

4. `/api/approvals/{approval_id}/reject` - POST
   - [ ] Accepts comment in body
   - [ ] Returns success

---

## Phase 9: Final Checklist

### Acceptance Criteria Verification

- [ ] **Agents pause execution** when action requires approval
- [ ] **Approval request shows:** agent name, action type, full context, proposed output
- [ ] **User can approve** with optional comment
- [ ] **User can reject** with feedback
- [ ] **Approval queue** shows all pending requests with timestamps
- [ ] **Configurable timeout** (backend: AgentConfig.approval_timeout_seconds)
- [ ] **Timeout countdown** visible in UI
- [ ] **Approval/rejection logged** in event log with user comments
- [ ] **WebSocket notification** triggers UI updates in real-time
- [ ] **Browser notifications** appear when approval requested (if enabled)
- [ ] **Sound alert** plays when approval requested (if enabled)
- [ ] **No console errors** in browser during normal operation

---

## Troubleshooting

### Issue: No Approvals Appearing

**Check:**
1. Sprint autonomy level set to `REQUIRE_APPROVAL`
2. Agent actually attempting an action
3. WebSocket connected (check Network → WS tab)
4. Backend logs for approval creation

### Issue: Browser Notifications Not Showing

**Check:**
1. Browser permissions granted (check browser settings)
2. Settings → Notifications → "Browser Notifications" ON
3. Settings → Notifications → "Approval Requests" ON
4. Browser console for permission errors

### Issue: No Sound Playing

**Check:**
1. Settings → Notifications → "Sound Notifications" ON
2. Browser allows audio playback (some require user interaction first)
3. File exists: `frontend/src/assets/notification.mp3`
4. Browser console for audio errors

### Issue: Countdown Timer Not Updating

**Check:**
1. Browser console for JavaScript errors
2. Component mounted correctly
3. Interval timer running (check with React DevTools)

### Issue: Context Not Rendering

**Check:**
1. Backend returning `context` field (not `context_json` string)
2. JSON parsing successful
3. ContextRenderer component imported correctly
4. Browser console for render errors

---

## Success Criteria

✅ **Test Passed** if:
- All approval flow steps work end-to-end
- Notifications (browser + sound) function correctly
- UI updates in real-time via WebSocket
- No console errors during normal operation
- Settings persist across page reloads
- Agents respond correctly to approval decisions

---

## Next Steps

After successful E2E verification:
1. Mark subtask-4-1 as completed
2. Proceed to subtask-4-2: Timeout expiration testing
3. Proceed to subtask-4-3: Rejection flow with feedback testing

---

**Document Version:** 1.0
**Last Updated:** 2026-03-19
**Author:** Auto-Claude (Task 006)
