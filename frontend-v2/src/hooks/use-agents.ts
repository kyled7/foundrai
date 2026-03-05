import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { AgentConfigUpdate } from '@/lib/types';

export function useAgents(projectId: string) {
  return useQuery({
    queryKey: ['agents', projectId],
    queryFn: () => api.agents.list(projectId),
    enabled: !!projectId,
  });
}

export function useUpdateAgent(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ role, data }: { role: string; data: AgentConfigUpdate }) =>
      api.agents.update(projectId, role, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['agents', projectId] }),
  });
}
