import { api } from './client';
import type { ProjectResponse } from '../types';

export async function listProjects(): Promise<{ projects: ProjectResponse[]; total: number }> {
  return api.get('/projects');
}

export async function getProject(projectId: string): Promise<ProjectResponse> {
  return api.get(`/projects/${projectId}`);
}

export async function createProject(name: string, description = ''): Promise<ProjectResponse> {
  return api.post('/projects', { name, description });
}
