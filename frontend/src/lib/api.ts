// Typed API client for FoundrAI backend

const BASE_URL = '/api';

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, body || res.statusText);
  }
  return res.json();
}

// === Projects ===
import type {
  Project, ProjectCreate, Sprint, SprintCreate, SprintMetrics, GoalTree,
  Task, AgentConfig, AgentConfigUpdate, Approval, ApprovalDecision,
  SprintEvent, AgentMessage, Artifact, CostBreakdown, BudgetStatus,
  TeamTemplate, CreateTemplateRequest, Team, CreateTeamRequest, Learning,
  SprintCostPoint, SprintSummary, SprintComparison, AgentMetrics, GlobalAnalytics,
  GlobalSettings, ApiKeyInfo, AgentHealth, ProjectAgentHealthResponse, SprintAgentHealthResponse,
} from './types';

export const api = {
  // Projects
  projects: {
    list: () => request<{ projects: Project[]; total: number }>('/projects'),
    get: (id: string) => request<Project>(`/projects/${id}`),
    create: (data: ProjectCreate) =>
      request<Project>('/projects', { method: 'POST', body: JSON.stringify(data) }),
  },

  // Sprints
  sprints: {
    list: (projectId: string) =>
      request<{ sprints: Sprint[]; total: number }>(`/projects/${projectId}/sprints`),
    get: (id: string) => request<Sprint>(`/sprints/${id}`),
    create: (projectId: string, data: SprintCreate) =>
      request<Sprint>(`/projects/${projectId}/sprints`, { method: 'POST', body: JSON.stringify(data) }),
    metrics: (id: string) => request<SprintMetrics>(`/sprints/${id}/metrics`),
    goalTree: (id: string) => request<GoalTree>(`/sprints/${id}/goal-tree`),
    start: (id: string) => request<Sprint>(`/sprints/${id}/start`, { method: 'POST' }),
    pause: (id: string) => request<Sprint>(`/sprints/${id}/pause`, { method: 'POST' }),
    resume: (id: string) => request<Sprint>(`/sprints/${id}/resume`, { method: 'POST' }),
    cancel: (id: string) => request<Sprint>(`/sprints/${id}/cancel`, { method: 'POST' }),
    message: (id: string, message: string, targetAgent?: string) =>
      request<void>(`/sprints/${id}/message`, {
        method: 'POST',
        body: JSON.stringify({ message, target_agent: targetAgent }),
      }),
  },

  // Tasks
  tasks: {
    list: (sprintId: string) => request<Task[]>(`/sprints/${sprintId}/tasks`),
    get: (id: string) => request<Task>(`/tasks/${id}`),
    updateStatus: (id: string, status: string) =>
      request<Task>(`/tasks/${id}/status`, { method: 'PUT', body: JSON.stringify({ status }) }),
  },

  // Agents
  agents: {
    list: (projectId: string) => request<{ agents: AgentConfig[] }>(`/projects/${projectId}/agents`),
    update: (projectId: string, role: string, data: AgentConfigUpdate) =>
      request<AgentConfig>(`/projects/${projectId}/agents/${role}`, {
        method: 'PUT', body: JSON.stringify(data),
      }),
  },

  // Agent Health
  agentHealth: {
    get: (projectId: string, role: string) =>
      request<AgentHealth>(`/projects/${projectId}/agents/${role}/health`),
    listProject: (projectId: string) =>
      request<ProjectAgentHealthResponse>(`/projects/${projectId}/agent-health`),
    listSprint: (sprintId: string) =>
      request<SprintAgentHealthResponse>(`/sprints/${sprintId}/agent-health`),
  },

  // Approvals
  approvals: {
    list: (sprintId: string) =>
      request<{ approvals: Approval[]; pending_count: number; total: number }>(`/sprints/${sprintId}/approvals`),
    approve: (id: string, data?: ApprovalDecision) =>
      request<Approval>(`/approvals/${id}/approve`, { method: 'POST', body: JSON.stringify(data ?? {}) }),
    reject: (id: string, data?: ApprovalDecision) =>
      request<Approval>(`/approvals/${id}/reject`, { method: 'POST', body: JSON.stringify(data ?? {}) }),
  },

  // Events & Messages
  events: {
    list: (sprintId: string) =>
      request<{ events: SprintEvent[]; total: number }>(`/sprints/${sprintId}/events`),
    messages: (sprintId: string) =>
      request<{ messages: AgentMessage[]; total: number }>(`/sprints/${sprintId}/messages`),
  },

  // Artifacts
  artifacts: {
    list: (sprintId: string) =>
      request<{ artifacts: Artifact[]; total: number }>(`/sprints/${sprintId}/artifacts`),
  },

  // Analytics
  analytics: {
    sprintCost: (sprintId: string) => request<CostBreakdown>(`/sprints/${sprintId}/cost`),
    projectCost: (projectId: string) => request<CostBreakdown>(`/projects/${projectId}/cost`),
    agentCosts: (projectId: string) =>
      request<{ project_id: string; agents: Record<string, unknown> }>(`/projects/${projectId}/agent-costs`),
    budget: (sprintId: string) => request<BudgetStatus>(`/sprints/${sprintId}/budget`),
    costOverTime: (projectId: string) =>
      request<SprintCostPoint[]>(`/projects/${projectId}/analytics/cost-over-time`),
    sprintHistory: (projectId: string) =>
      request<SprintSummary[]>(`/projects/${projectId}/analytics/sprint-history`),
    sprintComparison: (projectId: string) =>
      request<{ sprints: SprintComparison[] }>(`/projects/${projectId}/sprint-comparison`),
    agentPerformance: (projectId: string) =>
      request<AgentMetrics[]>(`/projects/${projectId}/analytics/agent-performance`),
    global: () => request<GlobalAnalytics>('/analytics/global'),
  },

  // Templates
  templates: {
    list: (params?: { source?: string; author?: string; public_only?: boolean }) => {
      const searchParams = new URLSearchParams();
      if (params?.source) searchParams.set('source', params.source);
      if (params?.author) searchParams.set('author', params.author);
      if (params?.public_only) searchParams.set('public_only', 'true');
      const qs = searchParams.toString();
      return request<TeamTemplate[]>(`/templates${qs ? `?${qs}` : ''}`);
    },
    get: (id: string) => request<TeamTemplate>(`/templates/${id}`),
    create: (data: CreateTemplateRequest) =>
      request<TeamTemplate>('/templates', { method: 'POST', body: JSON.stringify(data) }),
    delete: (id: string) => request<void>(`/templates/${id}`, { method: 'DELETE' }),
    apply: (id: string, projectId: string) =>
      request<unknown>(`/templates/${id}/apply`, {
        method: 'POST', body: JSON.stringify({ project_id: projectId }),
      }),
  },

  // Teams
  teams: {
    list: (projectId: string) => request<Team[]>(`/projects/${projectId}/teams`),
    create: (projectId: string, data: CreateTeamRequest) =>
      request<Team>(`/projects/${projectId}/teams`, { method: 'POST', body: JSON.stringify(data) }),
  },

  // Learnings
  learnings: {
    list: (projectId: string) =>
      request<{ learnings: Learning[]; total: number }>(`/projects/${projectId}/learnings`),
  },

  // Replay
  replay: {
    events: (sprintId: string) =>
      request<{ events: SprintEvent[]; total: number }>(`/sprints/${sprintId}/replay`),
  },
  // Settings
  settings: {
    get: () => request<GlobalSettings>('/settings'),
    update: (data: Partial<GlobalSettings>) =>
      request<GlobalSettings>('/settings', { method: 'POST', body: JSON.stringify(data) }),
    keys: {
      list: () => request<ApiKeyInfo[]>('/settings/keys'),
      add: (provider: string, key: string) =>
        request<ApiKeyInfo>('/settings/keys', {
          method: 'POST',
          body: JSON.stringify({ provider, key }),
        }),
      remove: (provider: string) =>
        request<void>(`/settings/keys/${provider}`, { method: 'DELETE' }),
      test: (provider: string) =>
        request<{ valid: boolean; error?: string }>('/settings/test-key', {
          method: 'POST',
          body: JSON.stringify({ provider }),
        }),
    },
  },
} as const;
