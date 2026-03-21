import { api } from './client';
import type { DecisionTraceSummary, DecisionTrace, TracesResponse } from '../types';

// Re-export types for backward compatibility
export type TraceDetail = DecisionTrace;
export type TraceSummary = DecisionTraceSummary;

export async function getTaskTraces(taskId: string): Promise<TracesResponse> {
  return api.get(`/tasks/${taskId}/traces`);
}

export async function getSprintTraces(
  sprintId: string,
  limit = 50,
  agentRole?: string,
  since?: string
): Promise<TracesResponse> {
  const params = new URLSearchParams({ limit: limit.toString() });
  if (agentRole) params.append('agent_role', agentRole);
  if (since) params.append('since', since);

  return api.get(`/sprints/${sprintId}/traces?${params.toString()}`);
}

export async function getTraceDetail(traceId: number): Promise<DecisionTrace> {
  return api.get(`/traces/${traceId}`);
}

export async function exportTrace(traceId: number): Promise<DecisionTrace> {
  return api.get(`/traces/${traceId}/export`);
}
