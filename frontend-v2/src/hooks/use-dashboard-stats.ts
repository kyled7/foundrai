import { useQueries } from '@tanstack/react-query';
import { useProjects } from './use-projects';
import { api } from '@/lib/api';

export function useDashboardStats() {
  const projectsQuery = useProjects();
  const projects = projectsQuery.data?.projects ?? [];

  const enriched = useQueries({
    queries: projects.map((p) => ({
      queryKey: ['project-enriched', p.project_id],
      queryFn: async () => {
        const [agents, cost, sprints] = await Promise.all([
          api.agents.list(p.project_id).catch(() => ({ agents: [] })),
          api.analytics.projectCost(p.project_id).catch(() => ({ total_cost_usd: 0, total_tokens: 0, by_agent: {} })),
          api.sprints.list(p.project_id).catch(() => ({ sprints: [], total: 0 })),
        ]);
        return {
          project: p,
          agentCount: agents.agents.length,
          totalCost: cost.total_cost_usd,
          lastSprint: sprints.sprints[0] ?? null,
        };
      },
      enabled: !!p.project_id,
      staleTime: 30_000,
    })),
  });

  const stats = {
    totalProjects: projects.length,
    activeSprints: projects.filter((p) => p.current_sprint_id).length,
    totalCost: enriched.reduce((sum, q) => sum + (q.data?.totalCost ?? 0), 0),
    totalSprints: projects.reduce((sum, p) => sum + p.sprint_count, 0),
  };

  return {
    projects: enriched,
    stats,
    isLoading: projectsQuery.isLoading,
  };
}
