import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sprints', projectId] }),
  });
}
