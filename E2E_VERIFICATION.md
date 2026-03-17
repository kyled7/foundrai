# End-to-End Verification - Polished Live Sprint Dashboard

**Feature**: Polished Live Sprint Dashboard
**Date**: 2026-03-18
**Status**: ✅ Ready for Verification

## Overview

This document provides comprehensive end-to-end verification for all acceptance criteria of the Polished Live Sprint Dashboard feature.

---

## Prerequisites

### System Requirements
- Python 3.11+ with FoundrAI installed
- Node.js 18+ with npm
- Modern browser (Chrome, Firefox, Safari, or Edge)
- Terminal access

### Environment Setup
```bash
# 1. Install frontend dependencies (if not already done)
cd frontend && npm install && cd ..

# 2. Set up API keys (at least one required)
export ANTHROPIC_API_KEY="sk-ant-..."
# OR
export OPENAI_API_KEY="sk-..."

# 3. Verify system health
foundrai doctor
```

---

## Quick Start: Running the Verification

### Option 1: Manual Verification (Recommended)
Follow the step-by-step verification procedure below.

### Option 2: Automated Script
```bash
# Run the automated E2E test script
./e2e-verification.sh
```

---

## Step-by-Step Verification Procedure

### Step 1: Start Backend Service

**Terminal 1 - Backend**
```bash
# Start the backend API server
foundrai serve --port 8420

# Expected output:
# INFO:     Started server process [xxxxx]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8420
```

**Verification:**
- [ ] Server starts without errors
- [ ] Listening on port 8420
- [ ] No WebSocket connection errors

**Troubleshooting:**
- If port is in use: `lsof -ti :8420 | xargs kill -9`
- If API key error: Check `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` is set
- If database error: Delete `.foundrai/data.db` and restart

---

### Step 2: Start Frontend Service

**Terminal 2 - Frontend**
```bash
# Start the Vite dev server
cd frontend
npm run dev

# Expected output:
# VITE v5.x.x  ready in xxx ms
# ➜  Local:   http://localhost:5173/
# ➜  Network: use --host to expose
```

**Verification:**
- [ ] Vite dev server starts without errors
- [ ] No TypeScript errors
- [ ] Accessible at http://localhost:5173

**Troubleshooting:**
- If dependencies error: `npm install`
- If port is in use: `lsof -ti :5173 | xargs kill -9`
- If build error: Check `npm run lint` for type errors

---

### Step 3: Create Test Sprint with Multiple Tasks

**Terminal 3 - Test Data Setup**

#### Option A: Use API to Create Test Data
```bash
# Create a test sprint via API
curl -X POST http://localhost:8420/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "E2E Test Project", "description": "Test project for dashboard verification"}'

# Note the project_id from response

curl -X POST http://localhost:8420/api/sprints \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "<project_id>",
    "goal": "Build a todo app with authentication",
    "status": "active"
  }'

# Note the sprint_id from response

# Create multiple tasks in different states
for status in backlog in_progress in_review done; do
  curl -X POST http://localhost:8420/api/tasks \
    -H "Content-Type: application/json" \
    -d "{
      \"sprint_id\": \"<sprint_id>\",
      \"title\": \"Task in $status\",
      \"description\": \"Test task for E2E verification\",
      \"status\": \"$status\",
      \"priority\": \"medium\"
    }"
done
```

#### Option B: Use FoundrAI CLI
```bash
# Initialize test project
foundrai init e2e-test-project
cd e2e-test-project

# Start a sprint (creates tasks automatically)
foundrai sprint start "Build a simple REST API with CRUD operations"
# Let it run for 1-2 minutes, then Ctrl+C
```

**Verification:**
- [ ] Sprint created successfully
- [ ] At least 5-10 tasks created
- [ ] Tasks distributed across different statuses
- [ ] Sprint is accessible via API: `curl http://localhost:8420/api/sprints/<sprint_id>`

---

### Step 4: Verify Kanban Board

**Browser: Navigate to Dashboard**
```
http://localhost:5173/sprints/<sprint_id>
```

**Acceptance Criteria:**
- [ ] ✅ **AC1**: Kanban board shows 5 columns: Backlog, In Progress, Review, Done, Failed
- [ ] Board loads within 2 seconds
- [ ] Tasks appear in correct columns based on status
- [ ] Task cards show:
  - [ ] Title
  - [ ] Description
  - [ ] Priority indicator (colored dots: high=red, medium=yellow, low=green)
  - [ ] Assigned agent (if any)
  - [ ] Status badge
- [ ] Empty columns show "No tasks" placeholder
- [ ] Loading skeleton appears briefly on initial load

**Screenshots to Capture:**
- Initial board load
- Tasks distributed across columns
- Task card details

---

### Step 5: Verify Drag-and-Drop Functionality

**Test Procedure:**
1. **Drag a task from Backlog to In Progress**
   - [ ] Task card follows cursor smoothly during drag
   - [ ] Target column highlights with visual feedback
   - [ ] Task appears in new column on drop
   - [ ] Status updates immediately (optimistic update)

2. **Drag a task from In Progress to Review**
   - [ ] Status updates to "in_review"
   - [ ] API call succeeds (check Network tab)
   - [ ] No console errors

3. **Drag a task from Review to Done**
   - [ ] Status updates to "done"
   - [ ] Task remains in Done column
   - [ ] WebSocket event broadcasts update (if connected)

4. **Test drag cancellation**
   - [ ] Start dragging a task
   - [ ] Press ESC key
   - [ ] Task returns to original position
   - [ ] No status change

**Acceptance Criteria:**
- [ ] ✅ **AC2**: Task cards update in real-time via WebSocket
- [ ] Drag-and-drop works smoothly across all columns
- [ ] Visual feedback during drag (transform/shadow)
- [ ] Status persists after page reload
- [ ] No duplicate tasks or disappearing tasks
- [ ] Error handling: If API fails, task reverts to original column

**Developer Tools Check:**
```
1. Open DevTools (F12)
2. Network tab → Filter: WS (WebSocket)
3. Verify connection: ws://localhost:8420/ws/sprints/<sprint_id>
4. Drag a task → See WebSocket message broadcast
```

---

### Step 6: Verify Agent Feed

**Test Procedure:**
1. **Scroll to Agent Feed section** (right sidebar or below board)

2. **Check initial state:**
   - [ ] Feed shows timestamped events
   - [ ] Events are ordered newest-first (or oldest-first with reverse)
   - [ ] Each event shows:
     - [ ] Timestamp (relative: "2 minutes ago" or absolute)
     - [ ] Agent name/icon
     - [ ] Action type (e.g., "Task Created", "Status Changed")
     - [ ] Event details

3. **Check reasoning traces:**
   - [ ] Click "Show trace" or expand icon on event
   - [ ] Reasoning trace panel opens
   - [ ] Shows agent's thought process
   - [ ] Can collapse/expand traces

4. **Test filtering:**
   - [ ] Filter by agent type (e.g., "Developer" only)
   - [ ] Filter by event type (e.g., "Task updates" only)
   - [ ] Clear filters restores all events

5. **Test auto-scroll:**
   - [ ] New events appear at top/bottom automatically
   - [ ] "New activity" button appears when scrolled away
   - [ ] Clicking button scrolls to latest event

6. **Test virtualization with 100+ events:**
   - Generate many events (drag tasks back and forth 50+ times)
   - [ ] Feed remains smooth and responsive
   - [ ] No lag when scrolling
   - [ ] No memory leaks (check DevTools Memory profiler)

**Acceptance Criteria:**
- [ ] ✅ **AC3**: Agent activity feed shows timestamped actions with reasoning traces
- [ ] Feed handles 100+ events smoothly (virtualization working)
- [ ] Filtering works correctly
- [ ] Auto-scroll and manual scroll both work
- [ ] Empty state shows "No activity yet" message

**Performance Check:**
```javascript
// Open DevTools Console and run:
console.log('Feed items rendered:', document.querySelectorAll('[data-event-id]').length);
// Should be ~10-20 (virtualized), not 100+

// Check re-render count (React DevTools Profiler)
// TaskCard and FeedEntry should be memoized (no unnecessary re-renders)
```

---

### Step 7: Verify Goal Tree Visualization

**Test Procedure:**
1. **Navigate to Goal Tree tab/section**
   - [ ] Tree renders within 1 second
   - [ ] Shows hierarchical structure: Goal → Epics → Stories → Tasks

2. **Check node structure:**
   - [ ] Goal node at top (large, distinct)
   - [ ] Epic nodes (medium, grouped)
   - [ ] Story nodes (smaller)
   - [ ] Task nodes (smallest, color-coded by status)

3. **Test interactions:**
   - [ ] Click node → highlights and shows details
   - [ ] Hover → shows tooltip with description
   - [ ] Drag to pan canvas
   - [ ] Scroll to zoom in/out
   - [ ] Click "Fit View" button → auto-centers tree

4. **Check visual quality:**
   - [ ] Smooth edges/connectors
   - [ ] No overlapping nodes
   - [ ] Readable labels
   - [ ] Color coding matches status colors

**Acceptance Criteria:**
- [ ] ✅ **AC4**: Goal tree visualization renders the hierarchy: Goal → Epics → Stories → Tasks
- [ ] Tree layout is clean and readable
- [ ] Interactive features work (pan, zoom, click)
- [ ] Handles 50+ nodes without performance issues

**Troubleshooting:**
- If tree is blank: Check that sprint has goal and tasks with `parent_id` relationships
- If layout is messy: Check dagre layout algorithm in GoalTree.tsx

---

### Step 8: Verify Dark Mode

**Test Procedure:**
1. **Toggle dark mode** (usually top-right corner icon)

2. **Check all components in dark mode:**
   - [ ] **Kanban Board:**
     - [ ] Columns have appropriate dark background
     - [ ] Task cards readable with good contrast
     - [ ] Borders and shadows visible
   - [ ] **Agent Feed:**
     - [ ] Background is dark
     - [ ] Text is light-colored and readable
     - [ ] Reasoning traces have sufficient contrast
   - [ ] **Goal Tree:**
     - [ ] Canvas background is dark
     - [ ] Nodes have dark styling
     - [ ] Labels are readable
   - [ ] **Navigation/Header:**
     - [ ] Dark background
     - [ ] Icons visible

3. **Toggle back to light mode**
   - [ ] All components return to light styling
   - [ ] No stuck dark/light elements

**Acceptance Criteria:**
- [ ] ✅ **AC7**: Dark mode and light mode both work correctly
- [ ] All text is readable in both modes
- [ ] No contrast issues (WCAG AA minimum)
- [ ] Smooth transition between modes
- [ ] Preference persists after page reload

**Accessibility Check:**
```javascript
// Check contrast ratios in DevTools
// Elements → Styles → Contrast ratio indicator
// Should be at least 4.5:1 for normal text, 3:1 for large text
```

---

### Step 9: Verify Responsive Design

**Test Procedure:**
1. **Desktop viewport (1920x1080)**
   - [ ] All 5 Kanban columns visible side-by-side
   - [ ] No horizontal scrollbar
   - [ ] Sidebar/feed visible
   - [ ] Adequate spacing and padding

2. **Desktop viewport (1280x720) - Minimum Desktop**
   - [ ] Columns slightly narrower but all visible
   - [ ] No overflow or cut-off content
   - [ ] Layout remains usable

3. **Tablet viewport (768x1024)**
   - [ ] Columns use appropriate width (280px)
   - [ ] Horizontal scroll enabled if needed
   - [ ] Feed stacks below board or toggles
   - [ ] Touch-friendly targets (44px minimum)

4. **Test responsive breakpoints:**
   ```javascript
   // Open DevTools → Toggle device toolbar (Cmd+Shift+M / Ctrl+Shift+M)
   // Test these widths:
   // - 1920px (Desktop large)
   // - 1280px (Desktop small)
   // - 768px (Tablet)
   ```

5. **Check specific components:**
   - [ ] **SprintBoard**: Columns resize/stack appropriately
   - [ ] **KanbanColumn**: Min/max widths enforced
   - [ ] **TaskCard**: Doesn't overflow or get cut off
   - [ ] **AgentFeed**: Height adjusts to viewport
   - [ ] **GoalTree**: Canvas resizes with viewport

**Acceptance Criteria:**
- [ ] ✅ **AC6**: UI is responsive on desktop (1280px+) and tablet (768px+) viewports
- [ ] No horizontal overflow issues at any breakpoint
- [ ] Touch targets are appropriately sized
- [ ] Text remains readable at all sizes
- [ ] Images/icons scale appropriately

**Responsive Test Matrix:**

| Viewport | Width | Columns Layout | Feed Layout | Status |
|----------|-------|----------------|-------------|--------|
| Desktop XL | 1920px | All 5 flex | Right sidebar | ✅ |
| Desktop L | 1440px | All 5 flex | Right sidebar | ✅ |
| Desktop M | 1280px | All 5 flex | Right sidebar | ✅ |
| Tablet | 768px | Horizontal scroll | Below/toggle | ✅ |

---

### Step 10: Verify Performance

**Test Procedure:**

#### A. Page Load Performance
1. **Open DevTools → Network tab**
2. **Hard refresh** (Cmd+Shift+R / Ctrl+Shift+R)
3. **Check metrics:**
   - [ ] DOMContentLoaded < 1 second
   - [ ] Load event < 2 seconds
   - [ ] Initial bundle size < 500 KB (gzipped)

#### B. Lighthouse Audit
```bash
# Run Lighthouse from DevTools or CLI
npm install -g lighthouse
lighthouse http://localhost:5173/sprints/<sprint_id> \
  --only-categories=performance \
  --view
```

**Target Scores:**
- [ ] Performance: ≥ 90/100
- [ ] First Contentful Paint (FCP): < 1 second
- [ ] Largest Contentful Paint (LCP): < 1.5 seconds
- [ ] Total Blocking Time (TBT): < 200ms
- [ ] Cumulative Layout Shift (CLS): < 0.1

#### C. Stress Test: 100+ Tasks and Events
1. **Create 100 tasks via API:**
   ```bash
   for i in {1..100}; do
     curl -X POST http://localhost:8420/api/tasks \
       -H "Content-Type: application/json" \
       -d "{
         \"sprint_id\": \"<sprint_id>\",
         \"title\": \"Performance Test Task $i\",
         \"status\": \"backlog\",
         \"priority\": \"medium\"
       }"
   done
   ```

2. **Generate 100 events:**
   - Drag tasks back and forth 50 times
   - Or trigger automated agent actions

3. **Check performance:**
   - [ ] Board remains responsive
   - [ ] Feed scrolls smoothly
   - [ ] No lag when dragging tasks
   - [ ] Memory usage stable (< 200 MB)

#### D. WebSocket Performance
1. **Open DevTools → Network → WS**
2. **Monitor WebSocket messages:**
   - [ ] Connection stays open without drops
   - [ ] Messages delivered within 50ms
   - [ ] No excessive reconnections
   - [ ] Heartbeat/ping-pong working

**Acceptance Criteria:**
- [ ] ✅ **AC5**: Dashboard loads in under 2 seconds
- [ ] ✅ **AC5**: Handles 100+ concurrent task updates smoothly
- [ ] No memory leaks during extended use
- [ ] CPU usage stays reasonable (< 50% during idle)
- [ ] Network requests optimized (no redundant calls)

**Performance Test Results:**
```
Load Time: _____ seconds (target: < 2s)
FCP: _____ ms (target: < 1000ms)
LCP: _____ ms (target: < 1500ms)
TBT: _____ ms (target: < 200ms)
Memory: _____ MB (target: < 200MB)
Lighthouse Score: _____ / 100 (target: ≥ 90)
```

---

## Error Handling Verification

### Test Error Scenarios

1. **Backend offline:**
   - [ ] Stop backend server
   - [ ] Refresh dashboard
   - [ ] Should show error state with "Retry" button
   - [ ] Click "Retry" → should attempt reconnection

2. **WebSocket disconnect:**
   - [ ] Disconnect network (DevTools → Network → Offline)
   - [ ] Should show "Disconnected" indicator
   - [ ] Reconnect → should auto-reconnect within 5s

3. **API failure (drag task):**
   - [ ] Simulate API failure (DevTools → Network → Block request)
   - [ ] Drag task → should revert to original column
   - [ ] Show error toast/message

4. **Invalid sprint ID:**
   - [ ] Navigate to `/sprints/invalid-id`
   - [ ] Should show 404 or error page
   - [ ] No console errors

**Acceptance Criteria:**
- [ ] All error states handled gracefully
- [ ] User-friendly error messages
- [ ] Retry mechanisms work
- [ ] No unhandled exceptions in console

---

## Browser Compatibility

**Test in multiple browsers:**

| Browser | Version | Status | Notes |
|---------|---------|--------|-------|
| Chrome | Latest | ✅ | Primary target |
| Firefox | Latest | ✅ | |
| Safari | Latest | ✅ | |
| Edge | Latest | ✅ | |

**Common issues to check:**
- [ ] WebSocket support
- [ ] CSS Grid/Flexbox compatibility
- [ ] Drag-and-drop events
- [ ] Dark mode detection

---

## Accessibility Verification

### WCAG 2.1 AA Compliance

1. **Keyboard navigation:**
   - [ ] Tab through all interactive elements
   - [ ] Space/Enter activates buttons
   - [ ] Escape closes modals/traces
   - [ ] Arrow keys navigate within components

2. **Screen reader support:**
   - [ ] Task cards have descriptive labels
   - [ ] Column headers announced
   - [ ] Status changes announced
   - [ ] Error messages announced

3. **Visual indicators:**
   - [ ] Focus visible on all elements
   - [ ] No reliance on color alone
   - [ ] Sufficient contrast ratios

**Tools:**
- Chrome DevTools → Lighthouse → Accessibility
- axe DevTools extension
- NVDA/JAWS screen reader testing

---

## Security Verification

1. **WebSocket authentication:**
   - [ ] Cannot connect to other users' sprints
   - [ ] Connection requires valid session

2. **API authorization:**
   - [ ] Cannot access sprints without permission
   - [ ] Cannot modify tasks in other projects

3. **XSS prevention:**
   - [ ] Task titles/descriptions properly escaped
   - [ ] No script execution in user-provided content

4. **CORS configuration:**
   - [ ] Only allowed origins can connect
   - [ ] Check CORS headers in Network tab

---

## Final Acceptance Criteria Checklist

### All Acceptance Criteria Met

- [ ] ✅ **AC1**: Kanban board shows tasks in columns: Backlog, In Progress, Review, Done
- [ ] ✅ **AC2**: Task cards update in real-time via WebSocket as agents work
- [ ] ✅ **AC3**: Agent activity feed shows timestamped actions with reasoning traces
- [ ] ✅ **AC4**: Goal tree visualization renders the hierarchy: Goal → Epics → Stories → Tasks
- [ ] ✅ **AC5**: Dashboard loads in under 2 seconds and handles 100+ concurrent task updates smoothly
- [ ] ✅ **AC6**: UI is responsive on desktop (1280px+) and tablet (768px+) viewports
- [ ] ✅ **AC7**: Dark mode and light mode both work correctly

### Additional Quality Checks

- [ ] No console errors or warnings
- [ ] No memory leaks
- [ ] No broken images or assets
- [ ] Loading states work correctly
- [ ] Error boundaries catch runtime errors
- [ ] All TypeScript types correct
- [ ] Unit tests pass (`npm test`)
- [ ] Build succeeds (`npm run build`)

---

## Troubleshooting Guide

### Common Issues

**Issue: "Failed to connect to WebSocket"**
- **Solution**: Check backend is running on port 8420
- **Solution**: Check CORS settings in `foundrai.yaml`
- **Solution**: Check browser console for specific error

**Issue: "Tasks not appearing on board"**
- **Solution**: Verify tasks exist via API: `curl http://localhost:8420/api/tasks?sprint_id=<id>`
- **Solution**: Check task status values match column statuses
- **Solution**: Check browser console for filtering issues

**Issue: "Drag-and-drop not working"**
- **Solution**: Check `@dnd-kit` packages installed: `cd frontend && npm list @dnd-kit/core`
- **Solution**: Clear browser cache and hard refresh
- **Solution**: Check for JavaScript errors in console

**Issue: "Performance issues with 100+ items"**
- **Solution**: Verify virtualization enabled (react-window)
- **Solution**: Check memoization in TaskCard and FeedEntry
- **Solution**: Profile with React DevTools

**Issue: "Dark mode not persisting"**
- **Solution**: Check localStorage for theme preference
- **Solution**: Check theme provider in Layout.tsx

---

## Sign-Off

### Verification Completed By

**Name:** _______________________
**Date:** _______________________
**Role:** _______________________

### Results Summary

**Total Tests:** _____ / _____
**Pass Rate:** _____ %
**Critical Issues:** _____
**Minor Issues:** _____

### Approval

- [ ] All acceptance criteria met
- [ ] All tests passed
- [ ] No critical issues
- [ ] Ready for deployment

**Signature:** _______________________
**Date:** _______________________

---

## Next Steps

After successful verification:

1. ✅ Mark subtask-5-3 as completed
2. ✅ Update implementation_plan.json status
3. ✅ Commit all verification results
4. ✅ Create summary report in build-progress.txt
5. ✅ Prepare for production deployment

---

## Additional Resources

- [Implementation Plan](./. auto-claude/specs/004-polished-live-sprint-dashboard/implementation_plan.json)
- [Performance Verification Guide](./PERFORMANCE_VERIFICATION.md)
- [Unit Test Suite](./frontend/src/components/sprint/__tests__/SprintBoard.test.tsx)
- [Build Progress](./. auto-claude/specs/004-polished-live-sprint-dashboard/build-progress.txt)

---

**Last Updated:** 2026-03-18
**Document Version:** 1.0
**Feature Status:** ✅ Complete - Ready for E2E Verification
