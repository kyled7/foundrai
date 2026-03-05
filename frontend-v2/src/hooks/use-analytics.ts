import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
    onSuccess: () => qc.invalidateQueries({ queryKey: ['approvals'] }),
  });
}

export function useReject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data?: ApprovalDecision }) =>
      api.approvals.reject(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['approvals'] }),
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

// Replay
export function useReplayEvents(sprintId: string) {
  return useQuery({
    queryKey: ['replay', sprintId],
    queryFn: () => api.replay.events(sprintId),
    enabled: !!sprintId,
  });
}
