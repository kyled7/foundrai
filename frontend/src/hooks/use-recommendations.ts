import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import type { TaskComplexity } from '@/lib/types';

export function useRecommendations(projectId: string) {
  return useQuery({
    queryKey: ['recommendations', projectId],
    queryFn: () => api.recommendations.list(projectId),
    enabled: !!projectId,
  });
}

export function useAgentRecommendation(
  projectId: string,
  agentRole: string,
  constraints?: {
    current_model?: string;
    task_complexity?: TaskComplexity;
    quality_requirements?: string;
    cost_constraints?: number;
  }
) {
  return useQuery({
    queryKey: ['recommendation', projectId, agentRole, constraints],
    queryFn: () => api.recommendations.get(projectId, agentRole, constraints),
    enabled: !!projectId && !!agentRole,
  });
}

export function useCostSavings(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      current_config: Record<string, string>;
      recommended_config?: Record<string, string>;
    }) => api.recommendations.costSavings(projectId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['recommendations', projectId] });
    },
    onError: (err: Error) => toast.error('Failed to calculate cost savings', { description: err.message }),
  });
}

export function useModelComparison(projectId: string, agentRole: string) {
  return useQuery({
    queryKey: ['model-comparison', projectId, agentRole],
    queryFn: () => api.recommendations.compareModels(projectId, agentRole),
    enabled: !!projectId && !!agentRole,
  });
}
