import { create } from 'zustand';
import type { SprintResponse, TaskResponse, TaskStatus } from '../types';
import { updateTaskStatus as updateTaskStatusApi } from '../api/tasks';

interface SprintStore {
  sprint: SprintResponse | null;
  tasks: TaskResponse[];
  loading: boolean;

  setSprint: (sprint: SprintResponse) => void;
  updateTaskStatus: (taskId: string, status: TaskStatus) => Promise<void>;
  addTask: (task: TaskResponse) => void;
  setTasks: (tasks: TaskResponse[]) => void;
  setLoading: (loading: boolean) => void;
  clear: () => void;
}

export const useSprintStore = create<SprintStore>((set) => ({
  sprint: null,
  tasks: [],
  loading: true,

  setSprint: (sprint) => set({ sprint, tasks: sprint.tasks, loading: false }),

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
      await updateTaskStatusApi(taskId, status);
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

  clear: () => set({ sprint: null, tasks: [], loading: true }),
}));
