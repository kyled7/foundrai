import { useEffect, useRef, useCallback } from 'react';
import type { WSMessage } from '../lib/types';

interface UseSprintWSOptions {
  sprintId: string;
  onEvent: (event: WSMessage) => void;
  enabled?: boolean;
}

export function useSprintWebSocket({ sprintId, onEvent, enabled = true }: UseSprintWSOptions): void {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempt = useRef(0);
  const maxReconnectDelay = 30_000;
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  const connect = useCallback(() => {
    if (!sprintId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/sprints/${sprintId}`);

    ws.onopen = () => {
      reconnectAttempt.current = 0;
    };

    ws.onmessage = (event) => {
      const msg: WSMessage = JSON.parse(event.data);
      onEventRef.current(msg);
    };

    ws.onclose = () => {
      const delay = Math.min(1000 * 2 ** reconnectAttempt.current, maxReconnectDelay);
      reconnectAttempt.current++;
      setTimeout(connect, delay);
    };

    wsRef.current = ws;
  }, [sprintId]);

  useEffect(() => {
    if (!enabled || !sprintId) return;

    connect();
    return () => {
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [sprintId, enabled, connect]);
}
