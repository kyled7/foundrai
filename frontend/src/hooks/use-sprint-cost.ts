import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useSprintWebSocket } from './useSprintWebSocket';
import { api } from '@/lib/api';
import type { CostBreakdown, WSMessage } from '@/lib/types';

interface UseSprintCostOptions {
  sprintId: string;
  enabled?: boolean;
}

/**
 * Hook for real-time sprint cost tracking.
 * Combines React Query for initial data fetch with WebSocket subscription for live updates.
 * Updates query cache automatically when cost_updated events arrive.
 */
export function useSprintCost({ sprintId, enabled = true }: UseSprintCostOptions) {
  const queryClient = useQueryClient();

  // Initial data fetch with React Query
  const query = useQuery({
    queryKey: ['sprint', sprintId, 'cost'],
    queryFn: () => api.analytics.sprintCost(sprintId),
    enabled: enabled && !!sprintId,
  });

  // Handle WebSocket events
  const handleEvent = (event: WSMessage) => {
    if (event.type === 'cost_updated') {
      const eventSprintId = event.data.sprint_id as string;

      // Only update if the event is for this sprint
      if (eventSprintId === sprintId) {
        // Update the query cache with new cost data
        queryClient.setQueryData<CostBreakdown>(
          ['sprint', sprintId, 'cost'],
          (oldData) => {
            if (!oldData) return oldData;

            // Extract cost update from event
            const costUsd = (event.data.cost_usd as number) || 0;
            const agentRole = event.data.agent_role as string;

            // Update total cost
            const newTotalCost = oldData.total_cost_usd + costUsd;

            // Update by_agent breakdown
            const newByAgent = { ...oldData.by_agent };
            if (agentRole) {
              const currentAgent = newByAgent[agentRole] || { cost_usd: 0, tokens: 0 };
              newByAgent[agentRole] = {
                cost_usd: currentAgent.cost_usd + costUsd,
                tokens: currentAgent.tokens + ((event.data.tokens as number) || 0),
              };
            }

            return {
              ...oldData,
              total_cost_usd: newTotalCost,
              total_tokens: oldData.total_tokens + ((event.data.tokens as number) || 0),
              by_agent: newByAgent,
            };
          }
        );
      }
    } else if (event.type === 'budget.warning' || event.type === 'budget.exceeded') {
      const eventSprintId = event.data.sprint_id as string;

      // Refetch cost data to ensure accuracy when budget events occur
      if (eventSprintId === sprintId) {
        queryClient.invalidateQueries({ queryKey: ['sprint', sprintId, 'cost'] });
      }
    }
  };

  // Subscribe to WebSocket events
  useSprintWebSocket({
    sprintId,
    onEvent: handleEvent,
    enabled: enabled && !!sprintId,
  });

  return query;
}
