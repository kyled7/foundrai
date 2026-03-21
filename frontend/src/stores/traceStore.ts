import { create } from 'zustand';
import type { DecisionTraceSummary, DecisionTrace } from '../types';

interface TraceStore {
  traces: DecisionTraceSummary[];
  selectedTrace: DecisionTrace | null;
  filters: { agentRole?: string; since?: string };

  setTraces: (traces: DecisionTraceSummary[]) => void;
  setSelectedTrace: (trace: DecisionTrace | null) => void;
  setFilters: (filters: Partial<TraceStore['filters']>) => void;
  clearTraces: () => void;
  filteredTraces: () => DecisionTraceSummary[];
}

export const useTraceStore = create<TraceStore>((set, get) => ({
  traces: [],
  selectedTrace: null,
  filters: {},

  setTraces: (traces) => set({ traces }),

  setSelectedTrace: (trace) => set({ selectedTrace: trace }),

  setFilters: (filters) =>
    set((state) => ({ filters: { ...state.filters, ...filters } })),

  clearTraces: () => set({ traces: [], selectedTrace: null }),

  filteredTraces: () => {
    const { traces, filters } = get();
    return traces.filter((trace) => {
      if (filters.agentRole && trace.agent_role !== filters.agentRole) return false;
      if (filters.since && new Date(trace.timestamp) < new Date(filters.since)) return false;
      return true;
    });
  },
}));
