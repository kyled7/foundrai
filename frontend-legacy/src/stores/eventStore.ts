import { create } from 'zustand';
import type { WSMessage } from '../types';

interface EventStore {
  events: WSMessage[];
  filters: { agentId?: string; eventType?: string };

  addEvent: (event: WSMessage) => void;
  setFilters: (filters: Partial<EventStore['filters']>) => void;
  clearEvents: () => void;
  filteredEvents: () => WSMessage[];
}

export const useEventStore = create<EventStore>((set, get) => ({
  events: [],
  filters: {},

  addEvent: (event) =>
    set((state) => ({
      events: [...state.events, event].slice(-500),
    })),

  setFilters: (filters) =>
    set((state) => ({ filters: { ...state.filters, ...filters } })),

  clearEvents: () => set({ events: [] }),

  filteredEvents: () => {
    const { events, filters } = get();
    return events.filter((e) => {
      if (filters.agentId && (e.data as Record<string, unknown>).agent_id !== filters.agentId) return false;
      if (filters.eventType && e.type !== filters.eventType) return false;
      return true;
    });
  },
}));
