/** API client for sprint execution endpoints. */

import { api } from './client';

export interface ExecuteResponse {
  sprint_id: string;
  status: string;
  message: string;
}

export interface SprintExecutionStatus {
  sprint_id: string;
  status: string;
  running: boolean;
}

export function executeSprint(sprintId: string, goal?: string): Promise<ExecuteResponse> {
  return api.post<ExecuteResponse>(`/sprints/${sprintId}/execute`, goal ? { goal } : {});
}

export function getExecutionStatus(sprintId: string): Promise<SprintExecutionStatus> {
  return api.get<SprintExecutionStatus>(`/sprints/${sprintId}/execution-status`);
}

export async function cancelSprint(sprintId: string): Promise<ExecuteResponse> {
  return api.post<ExecuteResponse>(`/sprints/${sprintId}/cancel`);
}
