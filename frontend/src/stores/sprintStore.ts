import { create } from 'zustand';
import type { SprintResponse, TaskResponse, TaskStatus } from '@/lib/types';
import { api } from '@/lib/api';

interface SprintStore {
  sprint: SprintResponse | null;
  tasks: TaskResponse[];
  loading: boolean;
  error: string | null;

  setSprint: (sprint: SprintResponse) => void;
  updateTaskStatus: (taskId: string, status: TaskStatus) => Promise<void>;
  addTask: (task: TaskResponse) => void;
  setTasks: (tasks: TaskResponse[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clear: () => void;
}

export const useSprintStore = create<SprintStore>((set) => ({
  sprint: null,
  tasks: [],
  loading: true,
  error: null,

  setSprint: (sprint) => set({ sprint, tasks: sprint.tasks, loading: false, error: null }),

  updateTaskStatus: async (taskId, status) => {
    // Optimistic update
    const previousTasks = useSprintStore.getState().tasks;
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.task_id === taskId ? { ...t, status } : t
      ),
    }));

    try {
      // Persist to backend
      await api.tasks.updateStatus(taskId, status);
    } catch (error) {
      // Revert on error
      set({ tasks: previousTasks });
      throw error;
    }
  },

  addTask: (task) =>
    set((state) => ({ tasks: [...state.tasks, task] })),

  setTasks: (tasks) => set({ tasks }),

  setLoading: (loading) => set({ loading }),

  setError: (error) => set({ error, loading: false }),

  clear: () => set({ sprint: null, tasks: [], loading: true, error: null }),
}));
