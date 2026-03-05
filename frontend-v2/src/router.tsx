import { createRouter, createRoute, createRootRoute } from '@tanstack/react-router';
import { AppShell } from '@/components/layout/AppShell';
import { DashboardPage } from '@/routes/index';
import { NewProjectPage } from '@/routes/projects/new';
import { ProjectDetailPage } from '@/routes/projects/$projectId/index';
import { SprintCommandCenter } from '@/routes/projects/$projectId/sprint';
import { AnalyticsPage } from '@/routes/projects/$projectId/analytics';
import { TeamConfigPage } from '@/routes/projects/$projectId/team';
import { TemplatesPage } from '@/routes/templates';
import { SettingsPage } from '@/routes/settings';
import { SprintReplayPage } from '@/routes/projects/$projectId/sprint/$sprintId/replay';

const rootRoute = createRootRoute({ component: AppShell });

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
  component: SprintCommandCenter,
});

const analyticsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/analytics',
  component: AnalyticsPage,
});

const teamRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/team',
  component: TeamConfigPage,
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

const sprintReplayRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/sprint/$sprintId/replay',
  component: SprintReplayPage,
});

const routeTree = rootRoute.addChildren([
  dashboardRoute,
  newProjectRoute,
  projectDetailRoute,
  sprintRoute,
  analyticsRoute,
  teamRoute,
  templatesRoute,
  settingsRoute,
  sprintReplayRoute,
]);

export const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
