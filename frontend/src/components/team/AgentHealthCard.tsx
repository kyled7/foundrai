import { cn } from '@/lib/utils';
import type { AgentHealth } from '@/lib/types';
import { AgentAvatar } from '../shared/AgentAvatar';

interface AgentHealthCardProps {
  agentHealth: AgentHealth;
  loading?: boolean;
  className?: string;
}

function getHealthStatusColor(status: string): string {
  switch (status) {
    case 'healthy':
      return 'text-green-600 dark:text-green-400';
    case 'warning':
      return 'text-yellow-600 dark:text-yellow-400';
    case 'unhealthy':
      return 'text-red-600 dark:text-red-400';
    case 'no_data':
      return 'text-gray-400 dark:text-gray-500';
    default:
      return 'text-gray-400 dark:text-gray-500';
  }
}

function getHealthStatusBg(status: string): string {
  switch (status) {
    case 'healthy':
      return 'bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800';
    case 'warning':
      return 'bg-yellow-50 dark:bg-yellow-950 border-yellow-200 dark:border-yellow-800';
    case 'unhealthy':
      return 'bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800';
    case 'no_data':
      return 'bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700';
    default:
      return 'bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700';
  }
}

export function AgentHealthCard({ agentHealth, loading, className }: AgentHealthCardProps) {
  if (loading) {
    return (
      <div className={cn('bg-card border border-border rounded-lg p-4', className)}>
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 animate-pulse bg-border rounded-full" />
          <div className="flex-1">
            <div className="h-5 w-24 animate-pulse bg-border rounded mb-1" />
            <div className="h-4 w-16 animate-pulse bg-border rounded" />
          </div>
        </div>
        <div className="space-y-2">
          <div className="h-4 w-full animate-pulse bg-border rounded" />
          <div className="h-4 w-3/4 animate-pulse bg-border rounded" />
        </div>
      </div>
    );
  }

  const { agent_role, health_score, status, metrics, recommendations } = agentHealth;

  return (
    <div
      className={cn(
        'rounded-lg p-4 border transition-colors',
        getHealthStatusBg(status),
        className
      )}
    >
      <div className="flex items-center gap-3 mb-3">
        <AgentAvatar role={agent_role} size="md" />
        <div className="flex-1">
          <h3 className="font-medium capitalize text-foreground">
            {agent_role.replace('_', ' ')}
          </h3>
          <p className={cn('text-sm font-semibold', getHealthStatusColor(status))}>
            {status.replace('_', ' ').toUpperCase()}
          </p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-foreground">{health_score}</p>
          <p className="text-xs text-muted">Health Score</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-3 text-sm">
        <div>
          <p className="text-muted">Completion Rate</p>
          <p className="font-semibold text-foreground">
            {metrics.completion_rate.toFixed(1)}%
          </p>
        </div>
        <div>
          <p className="text-muted">Quality Score</p>
          <p className="font-semibold text-foreground">
            {metrics.quality_score.toFixed(1)}%
          </p>
        </div>
        <div>
          <p className="text-muted">Tasks</p>
          <p className="font-semibold text-foreground">
            {metrics.completed_tasks}/{metrics.total_tasks}
          </p>
        </div>
        <div>
          <p className="text-muted">Cost</p>
          <p className="font-semibold text-foreground">
            ${metrics.total_cost_usd.toFixed(2)}
          </p>
        </div>
      </div>

      {recommendations.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs font-medium text-muted mb-1">Recommendations:</p>
          <ul className="space-y-1">
            {recommendations.slice(0, 2).map((rec, idx) => (
              <li key={idx} className="text-xs text-foreground flex items-start gap-1">
                <span className="text-muted">•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
