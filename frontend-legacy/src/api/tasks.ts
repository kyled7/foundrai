import { api } from './client';
import type { TaskResponse, TaskStatus } from '../types';

export async function listTasks(sprintId: string): Promise<TaskResponse[]> {
  return api.get(`/sprints/${sprintId}/tasks`);
}

export async function getTask(taskId: string): Promise<TaskResponse> {
  return api.get(`/tasks/${taskId}`);
}

export async function updateTaskStatus(taskId: string, status: TaskStatus): Promise<TaskResponse> {
  return api.patch(`/tasks/${taskId}`, { status });
}
