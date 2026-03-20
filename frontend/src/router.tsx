import { lazy, Suspense } from 'react';
import { createRouter, createRoute, createRootRoute } from '@tanstack/react-router';
import { AppShell } from '@/components/layout/AppShell';
import { RouteLoadingFallback } from '@/components/shared/RouteLoadingFallback';
import { NotFoundPage } from '@/routes/not-found';

// Eager (lightweight)
import { DashboardPage } from '@/routes/index';
import { NewProjectPage } from '@/routes/projects/new';
import { ProjectDetailPage } from '@/routes/projects/$projectId/index';
import { SettingsPage } from '@/routes/settings';
import { TemplatesPage } from '@/routes/templates';

// Lazy (heavy: Recharts, CodeMirror, replay)
const AnalyticsPage = lazy(() =>
  import('@/routes/projects/$projectId/analytics').then((m) => ({ default: m.AnalyticsPage }))
);
const SprintDetailPage = lazy(() =>
  import('@/routes/projects/$projectId/sprint/$sprintId/index').then((m) => ({ default: m.SprintDetailPage }))
);
const SprintReplayPage = lazy(() =>
  import('@/routes/projects/$projectId/sprint/$sprintId/replay').then((m) => ({ default: m.SprintReplayPage }))
);
const SprintCommandCenter = lazy(() =>
  import('@/routes/projects/$projectId/sprint').then((m) => ({ default: m.SprintCommandCenter }))
);
const TeamConfigPage = lazy(() =>
  import('@/routes/projects/$projectId/team').then((m) => ({ default: m.TeamConfigPage }))
);
const ProjectKnowledgeBasePage = lazy(() =>
  import('@/routes/projects/$projectId/knowledge').then((m) => ({ default: m.ProjectKnowledgeBasePage }))
);

const rootRoute = createRootRoute({
  component: AppShell,
  notFoundComponent: NotFoundPage,
});

const dashboardRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: DashboardPage,
});

const newProjectRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/new',
  component: NewProjectPage,
});

const projectDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId',
  component: ProjectDetailPage,
});

const sprintRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/sprint',
  component: () => (
    <Suspense fallback={<RouteLoadingFallback />}>
      <SprintCommandCenter />
    </Suspense>
  ),
});

const analyticsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/analytics',
  component: () => (
    <Suspense fallback={<RouteLoadingFallback />}>
      <AnalyticsPage />
    </Suspense>
  ),
});

const teamRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/team',
  component: () => (
    <Suspense fallback={<RouteLoadingFallback />}>
      <TeamConfigPage />
    </Suspense>
  ),
});

const knowledgeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/knowledge',
  component: () => (
    <Suspense fallback={<RouteLoadingFallback />}>
      <ProjectKnowledgeBasePage />
    </Suspense>
  ),
});

const templatesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/templates',
  component: TemplatesPage,
});

const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings',
  component: SettingsPage,
});

const sprintDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/sprint/$sprintId',
  component: () => (
    <Suspense fallback={<RouteLoadingFallback />}>
      <SprintDetailPage />
    </Suspense>
  ),
});

const sprintReplayRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/sprint/$sprintId/replay',
  component: () => (
    <Suspense fallback={<RouteLoadingFallback />}>
      <SprintReplayPage />
    </Suspense>
  ),
});

const routeTree = rootRoute.addChildren([
  dashboardRoute,
  newProjectRoute,
  projectDetailRoute,
  sprintRoute,
  sprintDetailRoute,
  sprintReplayRoute,
  analyticsRoute,
  teamRoute,
  knowledgeRoute,
  templatesRoute,
  settingsRoute,
]);

export const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
