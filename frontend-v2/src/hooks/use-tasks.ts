import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function useTasks(sprintId: string) {
  return useQuery({
    queryKey: ['tasks', sprintId],
    queryFn: () => api.tasks.list(sprintId),
    enabled: !!sprintId,
  });
}

export function useTask(id: string) {
  return useQuery({
    queryKey: ['task', id],
    queryFn: () => api.tasks.get(id),
    enabled: !!id,
  });
}
