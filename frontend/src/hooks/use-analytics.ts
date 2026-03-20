import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import type { ApprovalDecision } from '@/lib/types';

// Analytics
export function useSprintCost(sprintId: string) {
  return useQuery({
    queryKey: ['sprint', sprintId, 'cost'],
    queryFn: () => api.analytics.sprintCost(sprintId),
    enabled: !!sprintId,
  });
}

export function useProjectCost(projectId: string) {
  return useQuery({
    queryKey: ['project', projectId, 'cost'],
    queryFn: () => api.analytics.projectCost(projectId),
    enabled: !!projectId,
  });
}

// Approvals
export function useApprovals(sprintId: string) {
  return useQuery({
    queryKey: ['approvals', sprintId],
    queryFn: () => api.approvals.list(sprintId),
    enabled: !!sprintId,
  });
}

export function useApprove() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data?: ApprovalDecision }) =>
      api.approvals.approve(id, data),
    onSuccess: () => {
      toast.success('Approved');
      qc.invalidateQueries({ queryKey: ['approvals'] });
    },
    onError: (err: Error) => toast.error('Failed to approve', { description: err.message }),
  });
}

export function useReject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data?: ApprovalDecision }) =>
      api.approvals.reject(id, data),
    onSuccess: () => {
      toast.success('Rejected');
      qc.invalidateQueries({ queryKey: ['approvals'] });
    },
    onError: (err: Error) => toast.error('Failed to reject', { description: err.message }),
  });
}

// Templates
export function useTemplates() {
  return useQuery({
    queryKey: ['templates'],
    queryFn: () => api.templates.list(),
  });
}

// Learnings
export function useLearnings(projectId: string) {
  return useQuery({
    queryKey: ['learnings', projectId],
    queryFn: () => api.learnings.list(projectId),
    enabled: !!projectId,
  });
}

export function useUpdateLearning() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, learningId, data }: { projectId: string; learningId: string; data: Partial<import('@/lib/types').Learning> }) =>
      api.learnings.update(projectId, learningId, data),
    onSuccess: (_, variables) => {
      toast.success('Learning updated');
      qc.invalidateQueries({ queryKey: ['learnings', variables.projectId] });
    },
    onError: (err: Error) => toast.error('Failed to update learning', { description: err.message }),
  });
}

export function useDeleteLearning() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, learningId }: { projectId: string; learningId: string }) =>
      api.learnings.delete(projectId, learningId),
    onSuccess: (_, variables) => {
      toast.success('Learning deleted');
      qc.invalidateQueries({ queryKey: ['learnings', variables.projectId] });
    },
    onError: (err: Error) => toast.error('Failed to delete learning', { description: err.message }),
  });
}

export function usePinLearning() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, learningId }: { projectId: string; learningId: string }) =>
      api.learnings.pin(projectId, learningId),
    onSuccess: (_, variables) => {
      toast.success('Learning pinned');
      qc.invalidateQueries({ queryKey: ['learnings', variables.projectId] });
    },
    onError: (err: Error) => toast.error('Failed to pin learning', { description: err.message }),
  });
}

export function useSearchLearnings(projectId: string, query: string) {
  return useQuery({
    queryKey: ['learnings', projectId, 'search', query],
    queryFn: () => api.learnings.search(projectId, query),
    enabled: !!projectId && !!query,
  });
}

// Analytics v0.2.3
export function useCostOverTime(projectId: string) {
  return useQuery({
    queryKey: ['project', projectId, 'cost-over-time'],
    queryFn: () => api.analytics.costOverTime(projectId),
    enabled: !!projectId,
  });
}

export function useSprintHistory(projectId: string) {
  return useQuery({
    queryKey: ['project', projectId, 'sprint-history'],
    queryFn: () => api.analytics.sprintHistory(projectId),
    enabled: !!projectId,
  });
}

export function useSprintComparison(projectId: string) {
  return useQuery({
    queryKey: ['project', projectId, 'sprint-comparison'],
    queryFn: () => api.analytics.sprintComparison(projectId),
    enabled: !!projectId,
  });
}

export function useAgentPerformance(projectId: string) {
  return useQuery({
    queryKey: ['project', projectId, 'agent-performance'],
    queryFn: () => api.analytics.agentPerformance(projectId),
    enabled: !!projectId,
  });
}

export function useBudgetHistory(projectId: string) {
  return useQuery({
    queryKey: ['project', projectId, 'budget-history'],
    queryFn: async () => {
      const response = await api.analytics.budgetHistory(projectId);
      return response.history;
    },
    enabled: !!projectId,
  });
}

export function useGlobalAnalytics() {
  return useQuery({
    queryKey: ['analytics', 'global'],
    queryFn: () => api.analytics.global(),
  });
}

// Replay
export function useReplayEvents(sprintId: string) {
  return useQuery({
    queryKey: ['replay', sprintId],
    queryFn: () => api.replay.events(sprintId),
    enabled: !!sprintId,
  });
}

// Health Monitoring
export function useAgentHealth(projectId: string, agentRole: string) {
  return useQuery({
    queryKey: ['agent', projectId, agentRole, 'health'],
    queryFn: () => api.agentHealth.get(projectId, agentRole),
    enabled: !!projectId && !!agentRole,
  });
}

export function useProjectHealth(projectId: string) {
  return useQuery({
    queryKey: ['project', projectId, 'health'],
    queryFn: () => api.agentHealth.listProject(projectId),
    enabled: !!projectId,
  });
}
