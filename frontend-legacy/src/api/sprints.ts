import { api } from './client';
import type { SprintResponse, SprintMetricsResponse, GoalTreeResponse } from '../types';

export async function listSprints(projectId: string): Promise<{ sprints: SprintResponse[]; total: number }> {
  return api.get(`/projects/${projectId}/sprints`);
}

export async function getSprint(sprintId: string): Promise<SprintResponse> {
  return api.get(`/sprints/${sprintId}`);
}

export async function createSprint(projectId: string, goal: string): Promise<SprintResponse> {
  return api.post(`/projects/${projectId}/sprints`, { goal });
}

export async function getSprintMetrics(sprintId: string): Promise<SprintMetricsResponse> {
  return api.get(`/sprints/${sprintId}/metrics`);
}

export async function getGoalTree(sprintId: string): Promise<GoalTreeResponse> {
  return api.get(`/sprints/${sprintId}/goal-tree`);
}

export interface EventResponse {
  event_id: number;
  event_type: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export async function listEvents(sprintId: string, limit = 200): Promise<{ events: EventResponse[] }> {
  return api.get(`/sprints/${sprintId}/events?limit=${limit}`);
}
