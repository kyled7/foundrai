# Quick Start Guide - E2E Testing

## ✅ What's Complete

All code implementation is done! **14 out of 17 subtasks (82.4%) completed.**

- ✅ Phase 1: Backend API Enhancement (4/4 subtasks)
- ✅ Phase 2: Frontend Core Enhancements (5/5 subtasks)
- ✅ Phase 3: Notification System (4/4 subtasks)
- 🔄 Phase 4: Integration & E2E Testing (1/3 subtasks)

### Automated Verification ✓

All automated checks pass:
```bash
# Backend verification
.venv/bin/python verify_backend.py
# ✅ All backend verifications passed!

# Integration verification
.venv/bin/python verify_integration.py
# ✅ All integration checks passed!
```

---

## 🎯 Next Steps - Manual E2E Testing

### Step 1: Start Backend Server

```bash
# In worktree directory
source .venv/bin/activate
foundrai serve
```

**Expected:** Server starts on http://localhost:8420

### Step 2: Start Frontend Dev Server

```bash
# In new terminal, from worktree directory
cd frontend

# Note: npm may need nvm environment
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

npm run dev
```

**Expected:** Dev server starts on http://localhost:5173

### Step 3: Follow Testing Guide

Open and follow: **`E2E_VERIFICATION_GUIDE.md`**

This comprehensive guide covers:
- Sprint configuration with REQUIRE_APPROVAL
- Approval request verification
- Browser notifications testing
- Sound alerts testing
- UI component verification
- Approval/rejection flow
- Edge cases and troubleshooting

---

## 📋 Quick Testing Checklist

1. **Create Sprint** with autonomy = REQUIRE_APPROVAL
2. **Trigger Approval** by starting sprint execution
3. **Verify Notifications**:
   - [ ] ApprovalBanner shows pending count
   - [ ] Browser notification appears (if enabled)
   - [ ] Sound plays (if enabled)
4. **Verify Approval UI**:
   - [ ] Navigate to Approvals tab
   - [ ] ApprovalCard shows with countdown timer
   - [ ] Context displays in readable format
5. **Test Approve Flow**:
   - [ ] Add comment
   - [ ] Click "✓ Approve"
   - [ ] Agent proceeds with task
6. **Test Reject Flow**:
   - [ ] Trigger another approval
   - [ ] Add feedback comment
   - [ ] Click "✗ Reject"
   - [ ] Agent receives rejection

---

## 📚 Full Documentation

- **E2E_VERIFICATION_GUIDE.md** - Complete 9-phase testing guide (13.7 KB)
- **VERIFICATION_SUMMARY.md** - Status and acceptance criteria (8.2 KB)
- **verify_backend.py** - Backend verification script
- **verify_integration.py** - Integration verification script

---

## 🐛 Troubleshooting

### No Approvals Appearing?
- Check sprint autonomy level = REQUIRE_APPROVAL
- Check WebSocket connection (DevTools → Network → WS)
- Check backend logs for approval creation

### No Browser Notifications?
- Grant browser permissions
- Enable in Settings → Notifications → Browser Notifications
- Enable Settings → Notifications → Approval Requests

### No Sound?
- Enable in Settings → Notifications → Sound Notifications
- Check browser allows audio (may need user interaction first)
- Verify file exists: `frontend/src/assets/notification.mp3`

See **E2E_VERIFICATION_GUIDE.md** for full troubleshooting guide.

---

## ✨ What You're Testing

### New Features
1. **Countdown Timer** - Shows time remaining on approval (5 min default)
2. **Smart Context Display** - Intelligently formats code, diffs, JSON
3. **Browser Notifications** - System notifications when approval needed
4. **Sound Alerts** - Audio notification on approval request
5. **Configurable Timeout** - Backend supports per-agent timeout config
6. **Enhanced API** - New GET /approvals/{id} endpoint

### Existing Features (Should Still Work)
- ApprovalBanner shows pending count
- ApprovalQueue displays all pending approvals
- Approve/reject with optional comments
- WebSocket real-time updates
- Event logging

---

## 🎉 Success Criteria

Test passes if:
- ✅ All approval flow steps work end-to-end
- ✅ Notifications (browser + sound) function correctly
- ✅ UI updates in real-time via WebSocket
- ✅ No console errors during normal operation
- ✅ Settings persist across page reloads
- ✅ Agents respond correctly to approval decisions

---

## 📝 After Testing

Once manual testing completes successfully:

1. Document any issues found
2. Verify all acceptance criteria met
3. Mark subtask-4-1 complete
4. Proceed to remaining subtasks:
   - subtask-4-2: Timeout expiration testing
   - subtask-4-3: Rejection flow with feedback

---

**Ready to test?** Start servers and open E2E_VERIFICATION_GUIDE.md!
