import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import type { SprintCreate } from '@/lib/types';

export function useSprints(projectId: string) {
  return useQuery({
    queryKey: ['sprints', projectId],
    queryFn: () => api.sprints.list(projectId),
    enabled: !!projectId,
  });
}

export function useSprint(id: string) {
  return useQuery({
    queryKey: ['sprint', id],
    queryFn: () => api.sprints.get(id),
    enabled: !!id,
  });
}

export function useSprintMetrics(id: string) {
  return useQuery({
    queryKey: ['sprint', id, 'metrics'],
    queryFn: () => api.sprints.metrics(id),
    enabled: !!id,
  });
}

export function useGoalTree(sprintId: string) {
  return useQuery({
    queryKey: ['sprint', sprintId, 'goal-tree'],
    queryFn: () => api.sprints.goalTree(sprintId),
    enabled: !!sprintId,
  });
}

export function useCreateSprint(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: SprintCreate) => api.sprints.create(projectId, data),
    onSuccess: () => {
      toast.success('Sprint created');
      qc.invalidateQueries({ queryKey: ['sprints', projectId] });
    },
    onError: (err: Error) => toast.error('Failed to create sprint', { description: err.message }),
  });
}

export function useStartSprint() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (sprintId: string) => api.sprints.start(sprintId),
    onSuccess: (_, sprintId) => {
      toast.success('Sprint started');
      qc.invalidateQueries({ queryKey: ['sprint', sprintId] });
    },
    onError: (err: Error) => toast.error('Failed to start sprint', { description: err.message }),
  });
}

export function usePauseSprint() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (sprintId: string) => api.sprints.pause(sprintId),
    onSuccess: (_, sprintId) => {
      toast.success('Sprint paused');
      qc.invalidateQueries({ queryKey: ['sprint', sprintId] });
    },
    onError: (err: Error) => toast.error('Failed to pause sprint', { description: err.message }),
  });
}

export function useCancelSprint() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (sprintId: string) => api.sprints.cancel(sprintId),
    onSuccess: (_, sprintId) => {
      toast.success('Sprint cancelled');
      qc.invalidateQueries({ queryKey: ['sprint', sprintId] });
    },
    onError: (err: Error) => toast.error('Failed to cancel sprint', { description: err.message }),
  });
}
