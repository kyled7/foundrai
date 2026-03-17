import { create } from 'zustand';
import type { SprintResponse, TaskResponse, TaskStatus } from '../types';

interface SprintStore {
  sprint: SprintResponse | null;
  tasks: TaskResponse[];
  loading: boolean;

  setSprint: (sprint: SprintResponse) => void;
  updateTaskStatus: (taskId: string, status: TaskStatus) => void;
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

  updateTaskStatus: (taskId, status) =>
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.task_id === taskId ? { ...t, status } : t
      ),
    })),

  addTask: (task) =>
    set((state) => ({ tasks: [...state.tasks, task] })),

  setTasks: (tasks) => set({ tasks }),

  setLoading: (loading) => set({ loading }),

  clear: () => set({ sprint: null, tasks: [], loading: true }),
}));
