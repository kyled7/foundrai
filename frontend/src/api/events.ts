import { api } from './client';

export interface EventResponse {
  event_id: number;
  event_type: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export async function listEvents(sprintId: string, limit = 200): Promise<{ events: EventResponse[] }> {
  return api.get(`/sprints/${sprintId}/events?limit=${limit}`);
}
