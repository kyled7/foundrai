/**
 * FoundrAI Dashboard Performance Check
 *
 * Copy and paste this script into your browser console to measure
 * dashboard load time and verify it meets the < 2 second requirement.
 *
 * Usage:
 * 1. Navigate to http://localhost:5173/sprints/{sprintId}
 * 2. Open browser DevTools (F12)
 * 3. Go to Console tab
 * 4. Paste this entire script and press Enter
 * 5. Review the results
 */

(function() {
  'use strict';

  console.log('%c🚀 FoundrAI Dashboard Performance Check', 'font-size: 16px; font-weight: bold; color: #3b82f6;');
  console.log('%c━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'color: #9ca3af;');

  const perfData = performance.getEntriesByType('navigation')[0];

  if (!perfData) {
    console.error('❌ No navigation timing data available.');
    console.log('💡 Try refreshing the page and running this script again.');
    return;
  }

  // Calculate metrics
  const metrics = {
    dnsLookup: perfData.domainLookupEnd - perfData.domainLookupStart,
    tcpConnection: perfData.connectEnd - perfData.connectStart,
    requestTime: perfData.responseStart - perfData.requestStart,
    responseTime: perfData.responseEnd - perfData.responseStart,
    domProcessing: perfData.domComplete - perfData.domLoading,
    domContentLoaded: perfData.domContentLoadedEventEnd - perfData.fetchStart,
    totalLoadTime: perfData.loadEventEnd - perfData.fetchStart,
  };

  // Helper to format time
  function fmt(ms) {
    return ms < 1000 ? `${Math.round(ms)}ms` : `${(ms / 1000).toFixed(2)}s`;
  }

  // Helper to check threshold
  function check(actual, threshold) {
    return actual < threshold ? '✅' : '❌';
  }

  console.log('\n%c📊 Core Web Vitals', 'font-weight: bold; color: #10b981;');
  console.log('├─ DNS Lookup:        ', fmt(metrics.dnsLookup));
  console.log('├─ TCP Connection:    ', fmt(metrics.tcpConnection));
  console.log('├─ Request Time:      ', fmt(metrics.requestTime));
  console.log('├─ Response Time:     ', fmt(metrics.responseTime));
  console.log('└─ DOM Processing:    ', fmt(metrics.domProcessing));

  console.log('\n%c⏱️  Critical Metrics', 'font-weight: bold; color: #f59e0b;');
  console.log('├─ DOMContentLoaded:  ', fmt(metrics.domContentLoaded), check(metrics.domContentLoaded, 1000), '(Target: < 1s)');
  console.log('└─ Total Load Time:   ', fmt(metrics.totalLoadTime), check(metrics.totalLoadTime, 2000), '(Target: < 2s)');

  // Check Paint timing
  const paintEntries = performance.getEntriesByType('paint');
  const fcp = paintEntries.find(entry => entry.name === 'first-contentful-paint');
  const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
  const lcp = lcpEntries[lcpEntries.length - 1];

  if (fcp || lcp) {
    console.log('\n%c🎨 Paint Metrics', 'font-weight: bold; color: #8b5cf6;');
    if (fcp) {
      console.log('├─ First Contentful Paint (FCP):', fmt(fcp.startTime), check(fcp.startTime, 1000), '(Target: < 1s)');
    }
    if (lcp) {
      console.log('└─ Largest Contentful Paint (LCP):', fmt(lcp.startTime), check(lcp.startTime, 1500), '(Target: < 1.5s)');
    }
  }

  // Resource analysis
  const resources = performance.getEntriesByType('resource');
  const jsResources = resources.filter(r => r.name.includes('.js'));
  const cssResources = resources.filter(r => r.name.includes('.css'));
  const apiCalls = resources.filter(r => r.name.includes('/api/'));

  const totalJsSize = jsResources.reduce((acc, r) => acc + (r.transferSize || 0), 0);
  const totalCssSize = cssResources.reduce((acc, r) => acc + (r.transferSize || 0), 0);

  console.log('\n%c📦 Resource Summary', 'font-weight: bold; color: #ec4899;');
  console.log('├─ Total Resources:   ', resources.length);
  console.log('├─ JavaScript Files:  ', jsResources.length, `(${Math.round(totalJsSize / 1024)} KB)`);
  console.log('├─ CSS Files:         ', cssResources.length, `(${Math.round(totalCssSize / 1024)} KB)`);
  console.log('└─ API Calls:         ', apiCalls.length);

  // Slowest resources
  const slowestResources = [...resources]
    .sort((a, b) => b.duration - a.duration)
    .slice(0, 5);

  console.log('\n%c🐌 Slowest Resources (Top 5)', 'font-weight: bold; color: #ef4444;');
  slowestResources.forEach((r, i) => {
    const name = r.name.split('/').pop() || r.name;
    const prefix = i === slowestResources.length - 1 ? '└─' : '├─';
    console.log(`${prefix} ${name.substring(0, 40)}: ${fmt(r.duration)}`);
  });

  // Final verdict
  console.log('\n%c━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'color: #9ca3af;');

  const passed = metrics.totalLoadTime < 2000;
  const emoji = passed ? '✅' : '❌';
  const status = passed ? 'PASS' : 'FAIL';
  const color = passed ? '#10b981' : '#ef4444';
  const message = passed
    ? `Dashboard loaded in ${fmt(metrics.totalLoadTime)} (under 2 second target)`
    : `Dashboard took ${fmt(metrics.totalLoadTime)} (exceeds 2 second target)`;

  console.log(`%c${emoji} ${status}: ${message}`, `font-size: 14px; font-weight: bold; color: ${color};`);
  console.log('%c━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'color: #9ca3af;');

  // Recommendations if failed
  if (!passed) {
    console.log('\n%c💡 Performance Recommendations', 'font-weight: bold; color: #f59e0b;');

    if (metrics.responseTime > 500) {
      console.log('├─ Backend API response is slow. Check server performance.');
    }
    if (totalJsSize > 200000) {
      console.log('├─ JavaScript bundle is large. Consider code splitting.');
    }
    if (metrics.domProcessing > 1000) {
      console.log('├─ DOM processing is slow. Check for expensive React renders.');
    }
    if (apiCalls.length > 10) {
      console.log('├─ Too many API calls. Consider batching or caching.');
    }
    console.log('└─ Run Lighthouse audit for detailed analysis.');
  }

  // Export data for further analysis
  window.__FOUNDRAI_PERF__ = {
    metrics,
    resources: resources.length,
    totalLoadTime: metrics.totalLoadTime,
    passed,
    timestamp: new Date().toISOString(),
  };

  console.log('\n%cℹ️  Performance data exported to: window.__FOUNDRAI_PERF__', 'color: #6b7280; font-size: 11px;');
})();
