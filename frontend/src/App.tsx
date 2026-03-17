import { lazy, Suspense, useEffect, useState } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { listKeys } from './api/settings';

// Lazy load page components for better performance
const DashboardPage = lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage })));
const SprintPage = lazy(() => import('./pages/SprintPage').then(m => ({ default: m.SprintPage })));
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage').then(m => ({ default: m.AnalyticsPage })));
const ReplayPage = lazy(() => import('./pages/ReplayPage').then(m => ({ default: m.ReplayPage })));
const SettingsPage = lazy(() => import('./pages/SettingsPage').then(m => ({ default: m.SettingsPage })));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage').then(m => ({ default: m.NotFoundPage })));

// Loading fallback component
function PageLoader() {
  return (
    <div className="flex items-center justify-center h-screen">
      <div className="text-gray-500 dark:text-gray-400">Loading...</div>
    </div>
  );
}

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <Suspense fallback={<PageLoader />}><DashboardPage /></Suspense> },
      { path: 'sprints/:sprintId', element: <Suspense fallback={<PageLoader />}><SprintPage /></Suspense> },
      { path: 'analytics', element: <Suspense fallback={<PageLoader />}><AnalyticsPage /></Suspense> },
      { path: 'replay/:sprintId', element: <Suspense fallback={<PageLoader />}><ReplayPage /></Suspense> },
      { path: 'settings', element: <Suspense fallback={<PageLoader />}><SettingsPage /></Suspense> },
    ],
  },
  { path: '*', element: <Suspense fallback={<PageLoader />}><NotFoundPage /></Suspense> },
]);

function FirstRunRedirect({ children }: { children: React.ReactNode }) {
  const [checking, setChecking] = useState(true);
  const [needsSetup, setNeedsSetup] = useState(false);

  useEffect(() => {
    listKeys()
      .then((data) => {
        const anyConfigured = data.keys.some((k) => k.configured);
        setNeedsSetup(!anyConfigured);
      })
      .catch(() => {
        // API not available — skip redirect
      })
      .finally(() => setChecking(false));
  }, []);

  if (checking) return null;
  if (needsSetup && !window.location.pathname.startsWith('/settings')) {
    window.location.href = '/settings';
    return null;
  }
  return <>{children}</>;
}

export default function App() {
  return (
    <FirstRunRedirect>
      <RouterProvider router={router} />
    </FirstRunRedirect>
  );
}
