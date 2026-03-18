import { api } from './client';

export interface ReplayEvent {
  event_id: number;
  event_type: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export async function getReplayEvents(sprintId: string) {
  return api.get<{ events: ReplayEvent[]; total: number }>(`/sprints/${sprintId}/replay`);
}

export function createReplayWebSocket(sprintId: string, speed: number = 1): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return new WebSocket(`${protocol}//${window.location.host}/ws/replay/${sprintId}?speed=${speed}`);
}
