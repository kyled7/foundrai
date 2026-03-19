# Quick Start - E2E Verification

**Time Required:** 10-15 minutes
**Prerequisites:** Python 3.11+, Node.js 18+, API keys configured

---

## One-Command Start

```bash
# Automated E2E verification with test data
./e2e-verification.sh
```

This script will:
1. ✅ Check prerequisites (Python, Node, npm, API keys)
2. ✅ Install frontend dependencies if needed
3. ✅ Start backend server (port 8420)
4. ✅ Start frontend dev server (port 5173)
5. ✅ Create test project and sprint
6. ✅ Generate 28 test tasks across all statuses
7. ✅ Generate 15 test events for agent feed
8. ✅ Open dashboard in browser automatically

---

## Manual Start (If Script Doesn't Work)

### Terminal 1: Backend
```bash
foundrai serve --port 8420
```

### Terminal 2: Frontend
```bash
cd frontend
npm run dev
```

### Terminal 3: Create Test Data
```bash
# Create project
curl -X POST http://localhost:8420/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"E2E Test","description":"Test project"}'
# Note the project_id from response

# Create sprint
curl -X POST http://localhost:8420/api/sprints \
  -H "Content-Type: application/json" \
  -d '{"project_id":"<project_id>","goal":"Build a todo app","status":"active"}'
# Note the sprint_id from response

# Create tasks
for status in backlog in_progress in_review done failed; do
  curl -X POST http://localhost:8420/api/tasks \
    -H "Content-Type: application/json" \
    -d "{\"sprint_id\":\"<sprint_id>\",\"title\":\"Task in $status\",\"status\":\"$status\"}"
done
```

### Browser
```
http://localhost:5173/sprints/<sprint_id>
```

---

## Quick Verification Checklist

### 1. Kanban Board (30 seconds)
- [ ] See 5 columns: Backlog, In Progress, Review, Done, Failed
- [ ] Tasks appear in correct columns
- [ ] No console errors

### 2. Drag-and-Drop (1 minute)
- [ ] Drag task from Backlog → In Progress
- [ ] Task moves smoothly
- [ ] Status updates immediately
- [ ] Open DevTools Network tab → see API PATCH request

### 3. Agent Feed (30 seconds)
- [ ] Scroll through feed (right sidebar or below board)
- [ ] See timestamped events
- [ ] Click "Show trace" to expand reasoning
- [ ] No lag when scrolling

### 4. Goal Tree (30 seconds)
- [ ] Click "Goal Tree" tab
- [ ] See hierarchical tree structure
- [ ] Pan/zoom works smoothly
- [ ] Nodes show correct status colors

### 5. Dark Mode (30 seconds)
- [ ] Toggle dark mode (button in header)
- [ ] All components readable in dark mode
- [ ] Toggle back to light mode
- [ ] No stuck elements

### 6. Responsive Design (1 minute)
- [ ] Open DevTools (F12)
- [ ] Toggle device toolbar (Cmd+Shift+M / Ctrl+Shift+M)
- [ ] Test 1280px width → all columns visible
- [ ] Test 768px width → columns scroll horizontally
- [ ] No overflow issues

### 7. Performance (2 minutes)
- [ ] Open DevTools → Network tab
- [ ] Hard refresh (Cmd+Shift+R / Ctrl+Shift+R)
- [ ] Check load time < 2 seconds
- [ ] Open DevTools → Network → WS tab
- [ ] See WebSocket connection established
- [ ] No errors in Console tab

### 8. Error Handling (1 minute)
- [ ] Stop backend server (Ctrl+C in Terminal 1)
- [ ] See error state in dashboard
- [ ] Click "Retry" button
- [ ] Restart backend → dashboard reconnects

---

## Success Criteria

**All 7 Acceptance Criteria Must Pass:**
1. ✅ Kanban board shows 5 columns with tasks
2. ✅ Tasks update in real-time via WebSocket
3. ✅ Agent feed shows timestamped events with traces
4. ✅ Goal tree renders hierarchy
5. ✅ Dashboard loads < 2 seconds, handles 100+ tasks
6. ✅ Responsive on 1280px+ and 768px+ viewports
7. ✅ Dark mode and light mode work correctly

---

## Troubleshooting

### "foundrai: command not found"
```bash
pip install -e .
```

### "Port 8420 already in use"
```bash
lsof -ti :8420 | xargs kill -9
```

### "Cannot connect to backend"
```bash
# Check backend is running
curl http://localhost:8420/api/docs

# Check API keys
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY
```

### "Frontend won't start"
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### "No tasks showing on board"
```bash
# Verify tasks exist
curl http://localhost:8420/api/tasks?sprint_id=<sprint_id>

# Check browser console for errors
```

---

## Full Documentation

- **Detailed verification:** [E2E_VERIFICATION.md](./E2E_VERIFICATION.md)
- **Implementation results:** [E2E_VERIFICATION_RESULTS.md](./E2E_VERIFICATION_RESULTS.md)
- **Performance guide:** [PERFORMANCE_VERIFICATION.md](./PERFORMANCE_VERIFICATION.md)
- **Implementation plan:** [.auto-claude/specs/004-polished-live-sprint-dashboard/implementation_plan.json](./.auto-claude/specs/004-polished-live-sprint-dashboard/implementation_plan.json)

---

**Last Updated:** 2026-03-18
**Estimated Time:** 10-15 minutes
**Status:** ✅ Ready to verify
