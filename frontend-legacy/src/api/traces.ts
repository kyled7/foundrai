import { api } from './client';

export interface TraceSummary {
  trace_id: number;
  event_id: number | null;
  task_id: string | null;
  sprint_id: string | null;
  agent_role: string;
  model: string;
  tokens_used: number;
  cost_usd: number;
  duration_ms: number;
  thinking: string | null;
  timestamp: string;
}

export interface TraceDetail extends TraceSummary {
  prompt: string;
  response: string;
  tool_calls: unknown[];
}

export async function getTaskTraces(taskId: string) {
  return api.get<{ traces: TraceSummary[]; total: number }>(`/tasks/${taskId}/traces`);
}

export async function getSprintTraces(sprintId: string, limit = 50) {
  return api.get<{ traces: TraceSummary[]; total: number }>(`/sprints/${sprintId}/traces?limit=${limit}`);
}

export async function getTraceDetail(traceId: number) {
  return api.get<TraceDetail>(`/traces/${traceId}`);
}
