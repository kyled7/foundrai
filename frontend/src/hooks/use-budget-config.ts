import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import type { BudgetConfig } from '@/lib/types';

interface BackendBudgetConfig {
  sprint_budget_usd: number;
  warning_threshold: number;
  model_tierdown_map: Record<string, string>;
  agent_budgets: Record<string, number>;
}

function toFrontendConfig(backend: BackendBudgetConfig): BudgetConfig {
  return {
    sprint_budget_usd: backend.sprint_budget_usd || null,
    per_agent_budgets: Object.fromEntries(
      Object.entries(backend.agent_budgets).map(([k, v]) => [k, v || null])
    ),
    warning_threshold_percent: backend.warning_threshold * 100,
    model_tier_down_mapping: backend.model_tierdown_map,
  };
}

function toBackendConfig(frontend: BudgetConfig): BackendBudgetConfig {
  return {
    sprint_budget_usd: frontend.sprint_budget_usd ?? 0,
    agent_budgets: Object.fromEntries(
      Object.entries(frontend.per_agent_budgets).map(([k, v]) => [k, v ?? 0])
    ),
    warning_threshold: frontend.warning_threshold_percent / 100,
    model_tierdown_map: frontend.model_tier_down_mapping ?? {},
  };
}

export function useBudgetConfig() {
  return useQuery({
    queryKey: ['budget', 'config'],
    queryFn: async () => {
      const data = await api.budget.getConfig();
      return toFrontendConfig(data);
    },
  });
}

export function useSaveBudgetConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: BudgetConfig) => api.budget.saveConfig(toBackendConfig(data)),
    onSuccess: () => {
      toast.success('Budget configuration saved');
      qc.invalidateQueries({ queryKey: ['budget', 'config'] });
    },
    onError: (err: Error) => toast.error('Failed to save budget configuration', { description: err.message }),
  });
}
