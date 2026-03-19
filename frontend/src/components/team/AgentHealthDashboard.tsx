import { useProjectHealth } from '@/hooks/use-analytics';
import { AgentHealthCard } from './AgentHealthCard';
import type { AgentHealth } from '@/lib/types';

interface AgentHealthDashboardProps {
  projectId: string;
}

export function AgentHealthDashboard({ projectId }: AgentHealthDashboardProps) {
  const { data, isLoading, error } = useProjectHealth(projectId);

  if (error) {
    return (
      <div className="p-4">
        <div className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <h3 className="text-sm font-medium text-red-800 dark:text-red-200 mb-1">
            Failed to load agent health data
          </h3>
          <p className="text-xs text-red-600 dark:text-red-400">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-4 space-y-4">
        <h2 className="text-lg font-semibold">Agent Health</h2>
        <p className="text-sm text-gray-500">
          Monitor the performance and health of your agent team.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <AgentHealthCard key={i} agentHealth={{} as AgentHealth} loading />
          ))}
        </div>
      </div>
    );
  }

  const agents = data?.agents || [];

  return (
    <div className="p-4 space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Agent Health</h2>
        <p className="text-sm text-gray-500">
          Monitor the performance and health of your agent team.
        </p>
      </div>

      {agents.length === 0 ? (
        <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-8 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            No agent health data available yet. Health metrics will appear after agents complete tasks.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <AgentHealthCard key={agent.agent_role} agentHealth={agent} />
          ))}
        </div>
      )}
    </div>
  );
}
