/** Analytics API client. */

import { api } from './client';

export interface CostBreakdown {
  total_tokens: number;
  total_cost: number;
  call_count: number;
  by_agent: Record<string, { total_tokens: number; total_cost: number; call_count: number }>;
  by_sprint?: Record<string, { total_tokens: number; total_cost: number; call_count: number }>;
}

export interface BudgetStatus {
  sprint_id: string;
  budget_usd: number;
  spent_usd: number;
  remaining_usd: number;
  percentage_used: number;
  is_warning: boolean;
  is_exceeded: boolean;
}

export function getSprintCost(sprintId: string) {
  return api.get<CostBreakdown>(`/sprints/${sprintId}/cost`);
}

export function getProjectCost(projectId: string) {
  return api.get<CostBreakdown>(`/projects/${projectId}/cost`);
}

export function getAgentCosts(projectId: string) {
  return api.get<{ project_id: string; agents: CostBreakdown['by_agent'] }>(
    `/projects/${projectId}/agent-costs`,
  );
}

export function getSprintBudget(sprintId: string) {
  return api.get<BudgetStatus>(`/sprints/${sprintId}/budget`);
}

export function setSprintBudget(sprintId: string, budgetUsd: number, agentRole?: string) {
  return api.put<{ status: string }>(`/sprints/${sprintId}/budget`, {
    budget_usd: budgetUsd,
    agent_role: agentRole ?? null,
  });
}
