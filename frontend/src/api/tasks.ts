import { api } from './client';
import type { TaskResponse } from '../types';

export async function listTasks(sprintId: string): Promise<TaskResponse[]> {
  return api.get(`/sprints/${sprintId}/tasks`);
}

export async function getTask(taskId: string): Promise<TaskResponse> {
  return api.get(`/tasks/${taskId}`);
}
