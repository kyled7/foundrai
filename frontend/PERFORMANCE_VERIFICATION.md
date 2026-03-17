# Dashboard Performance Verification Guide

## Objective
Verify that the FoundrAI sprint dashboard loads in under 2 seconds with real data, meeting the acceptance criteria for production quality.

## Prerequisites
- Backend server running on `http://localhost:8000`
- Frontend dev server running on `http://localhost:5173`
- An active sprint with multiple tasks (recommended: 20+ tasks across different statuses)
- Agent feed with events (recommended: 50+ historical events)

## Performance Verification Steps

### 1. Browser DevTools Network Tab Method

#### Setup
1. Open Google Chrome or Firefox (recommended for accurate performance metrics)
2. Navigate to `http://localhost:5173`
3. Open DevTools (F12 or Cmd+Option+I on Mac)
4. Click on the **Network** tab
5. Ensure "Disable cache" is **UNCHECKED** (we want to test with normal caching behavior)
6. Clear browser cache once before starting: Settings → Privacy → Clear browsing data

#### Measurement Process
1. In the Network tab, check the checkbox **"Disable cache"** for the first test (cold load)
2. Navigate to a sprint page: `http://localhost:5173/sprints/{sprintId}`
3. **Look at the bottom status bar** of the Network tab for:
   - **DOMContentLoaded**: Time when HTML is parsed and DOM is ready
   - **Load**: Time when all resources (CSS, JS, images) are loaded
4. Record the **Load** time - this should be **< 2 seconds**

#### What to Check
- ✅ **Load time < 2 seconds**
- ✅ **DOMContentLoaded < 1 second** (ideal)
- ✅ **Largest Contentful Paint (LCP) < 1.5 seconds**
- ✅ **First Input Delay (FID) < 100ms**
- ✅ **Cumulative Layout Shift (CLS) < 0.1**

### 2. Chrome Lighthouse Performance Audit

#### Steps
1. Open Chrome DevTools
2. Click on the **Lighthouse** tab
3. Select:
   - Mode: Navigation
   - Device: Desktop
   - Categories: Performance (only)
4. Click **Analyze page load**
5. Wait for the report

#### Target Metrics
- **Performance Score**: ≥ 90/100
- **First Contentful Paint**: < 1.0s
- **Largest Contentful Paint**: < 1.5s
- **Time to Interactive**: < 2.5s
- **Speed Index**: < 2.0s
- **Total Blocking Time**: < 200ms

### 3. React DevTools Profiler

#### Setup
1. Install React Developer Tools extension
2. Open DevTools → **Profiler** tab
3. Click the record button (blue circle)
4. Navigate to sprint page
5. Stop recording after page loads

#### What to Check
- ✅ **Initial render time < 500ms**
- ✅ **No components taking > 100ms** to render
- ✅ **Memoized components** (TaskCard, FeedEntry) should show minimal re-renders
- ✅ **Virtualized list** (AgentFeed) should only render visible items

### 4. Performance API Method (Programmatic)

Add this code to browser console after page loads:

```javascript
// Get page load timing
const perfData = performance.getEntriesByType('navigation')[0];
console.log('Page Load Metrics:');
console.log('-------------------');
console.log('DNS Lookup:', perfData.domainLookupEnd - perfData.domainLookupStart, 'ms');
console.log('TCP Connection:', perfData.connectEnd - perfData.connectStart, 'ms');
console.log('Request Time:', perfData.responseStart - perfData.requestStart, 'ms');
console.log('Response Time:', perfData.responseEnd - perfData.responseStart, 'ms');
console.log('DOM Processing:', perfData.domComplete - perfData.domLoading, 'ms');
console.log('-------------------');
console.log('Total Load Time:', perfData.loadEventEnd - perfData.fetchStart, 'ms');
console.log('DOMContentLoaded:', perfData.domContentLoadedEventEnd - perfData.fetchStart, 'ms');

// Check if under 2 seconds
if (perfData.loadEventEnd - perfData.fetchStart < 2000) {
  console.log('✅ PASS: Page loaded in under 2 seconds');
} else {
  console.log('❌ FAIL: Page took longer than 2 seconds to load');
}
```

## Test Scenarios

### Scenario 1: Cold Load (First Visit)
- Clear browser cache
- Navigate to sprint page
- Expected: < 2 seconds

### Scenario 2: Warm Load (With Cache)
- Visit sprint page once
- Navigate away
- Return to sprint page
- Expected: < 1 second (faster due to caching)

### Scenario 3: Load with Real Data
- Sprint with 50+ tasks across all statuses
- Agent feed with 100+ events
- Goal tree with 3-level hierarchy
- Expected: Still < 2 seconds

### Scenario 4: Heavy Load Test
- Sprint with 100+ tasks
- Agent feed with 500+ events
- Multiple tabs open
- Expected: < 3 seconds (acceptable for extreme load)

## Performance Optimizations Already Implemented

### ✅ Code Splitting & Lazy Loading
- React Router with code splitting
- Dynamic imports for route components

### ✅ Component Memoization
- `React.memo()` on TaskCard component
- `React.memo()` on FeedEntry component
- `useMemo()` for expensive computations
- `useCallback()` for stable function references

### ✅ List Virtualization
- AgentFeed uses `react-window` for virtualized rendering
- Only renders visible items (10-15 items instead of 100+)
- Significant DOM node reduction

### ✅ Loading States
- Skeleton screens for SprintBoard, AgentFeed, GoalTree
- Prevents layout shifts (CLS optimization)
- Smooth loading transitions

### ✅ Optimistic Updates
- Drag-and-drop updates UI immediately
- API calls happen in background
- Rollback on failure

### ✅ WebSocket Optimization
- Real-time updates without polling
- Efficient event handling
- Minimal re-renders on updates

### ✅ API Efficiency
- Parallel data fetching (sprint, events, approvals)
- No redundant API calls
- Proper error handling

## Common Performance Issues & Solutions

### Issue: Slow Initial Load
**Cause**: Backend API slow or cold start
**Solution**:
- Check backend response times in Network tab
- Ensure backend is running in production mode
- Consider API response caching

### Issue: Large JavaScript Bundle
**Cause**: Too many dependencies or no code splitting
**Solution**:
- Check bundle size: `cd frontend && npm run build`
- Ensure code splitting is working
- Remove unused dependencies

### Issue: Too Many Re-renders
**Cause**: Missing memoization or unstable dependencies
**Solution**:
- Use React DevTools Profiler
- Check component re-render counts
- Add more `useMemo`/`useCallback` where needed

### Issue: Slow Drag-and-Drop
**Cause**: No memoization or heavy event handlers
**Solution**:
- TaskCard is already memoized ✅
- Pointer sensor has activation constraint ✅
- DragOverlay prevents full re-renders ✅

## Expected Results

### Network Tab
```
Status  | Method | File              | Time   | Size
--------|--------|-------------------|--------|-------
200     | GET    | /                 | 50ms   | 2KB
200     | GET    | /assets/index.js  | 200ms  | 150KB
200     | GET    | /api/sprints/:id  | 150ms  | 5KB
200     | GET    | /api/events       | 200ms  | 25KB
200     | GET    | /api/approvals    | 100ms  | 2KB
--------|--------|-------------------|--------|-------
Total Load Time: 1.2s ✅
```

### Console Output (Performance API)
```
Page Load Metrics:
-------------------
DNS Lookup: 5 ms
TCP Connection: 15 ms
Request Time: 50 ms
Response Time: 100 ms
DOM Processing: 800 ms
-------------------
Total Load Time: 1250 ms
DOMContentLoaded: 900 ms
✅ PASS: Page loaded in under 2 seconds
```

## Documentation

After verification, document the results:

1. Take a screenshot of the Network tab showing load time
2. Copy the Lighthouse performance score
3. Record the Performance API output
4. Note any issues or anomalies
5. Update build-progress.txt with verification results

## Success Criteria

- ✅ Dashboard loads in < 2 seconds on cold load
- ✅ Dashboard loads in < 1 second on warm load
- ✅ No console errors or warnings
- ✅ Smooth 60fps animations and scrolling
- ✅ Responsive on desktop (1280px+) and tablet (768px+)
- ✅ Works with 100+ tasks and events without lag
- ✅ Lighthouse performance score ≥ 90/100

## Notes

- Performance may vary based on network speed and hardware
- Test on a mid-range machine for realistic results
- Mobile performance is not part of this acceptance criteria (desktop/tablet only)
- WebSocket connections may add slight overhead but shouldn't affect initial load
