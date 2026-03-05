// Zustand store for realtime sprint events

import { create } from 'zustand';
import type { WSEvent } from '@/lib/types';
import { SprintWebSocket } from '@/lib/ws';

interface SprintFeedState {
  events: WSEvent[];
  isConnected: boolean;
  sprintId: string | null;
  ws: SprintWebSocket | null;

  connect: (sprintId: string) => void;
  disconnect: () => void;
  clearEvents: () => void;
}

export const useSprintFeed = create<SprintFeedState>((set, get) => ({
  events: [],
  isConnected: false,
  sprintId: null,
  ws: null,

  connect: (sprintId: string) => {
    const { ws: existing } = get();
    if (existing) existing.disconnect();

    const ws = new SprintWebSocket(sprintId);
    ws.subscribe((event) => {
      set((state) => ({
        events: [...state.events, event],
        isConnected: ws.isConnected,
      }));
    });
    ws.connect();
    set({ ws, sprintId, events: [], isConnected: false });
  },

  disconnect: () => {
    const { ws } = get();
    ws?.disconnect();
    set({ ws: null, isConnected: false, sprintId: null });
  },

  clearEvents: () => set({ events: [] }),
}));
