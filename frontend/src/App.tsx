import { useEffect, useState } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { SprintPage } from './pages/SprintPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ReplayPage } from './pages/ReplayPage';
import { SettingsPage } from './pages/SettingsPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { listKeys } from './api/settings';

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'sprints/:sprintId', element: <SprintPage /> },
      { path: 'analytics', element: <AnalyticsPage /> },
      { path: 'replay/:sprintId', element: <ReplayPage /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },
  { path: '*', element: <NotFoundPage /> },
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
