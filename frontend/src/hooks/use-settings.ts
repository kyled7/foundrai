import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import type { GlobalSettings } from '@/lib/types';

export function useSettings() {
  return useQuery({
    queryKey: ['settings'],
    queryFn: () => api.settings.get(),
  });
}

export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<GlobalSettings>) => api.settings.update(data),
    onSuccess: () => {
      toast.success('Settings saved');
      qc.invalidateQueries({ queryKey: ['settings'] });
    },
    onError: (err: Error) => toast.error('Failed to save settings', { description: err.message }),
  });
}

export function useApiKeys() {
  return useQuery({
    queryKey: ['settings', 'keys'],
    queryFn: () => api.settings.keys.list(),
  });
}

export function useAddApiKey() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ provider, key }: { provider: string; key: string }) =>
      api.settings.keys.add(provider, key),
    onSuccess: () => {
      toast.success('API key added');
      qc.invalidateQueries({ queryKey: ['settings', 'keys'] });
    },
    onError: (err: Error) => toast.error('Failed to add API key', { description: err.message }),
  });
}

export function useRemoveApiKey() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (provider: string) => api.settings.keys.remove(provider),
    onSuccess: () => {
      toast.success('API key removed');
      qc.invalidateQueries({ queryKey: ['settings', 'keys'] });
    },
    onError: (err: Error) => toast.error('Failed to remove API key', { description: err.message }),
  });
}

export function useTestApiKey() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (provider: string) => api.settings.keys.test(provider),
    onSuccess: (result) => {
      if (result.valid) {
        toast.success('API key is valid');
      } else {
        toast.error('API key is invalid', { description: result.error });
      }
      qc.invalidateQueries({ queryKey: ['settings', 'keys'] });
    },
    onError: (err: Error) => toast.error('Failed to test API key', { description: err.message }),
  });
}
