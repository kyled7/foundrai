// FoundrAI API Types — derived from backend route handlers

// === Projects ===
export interface Project {
  project_id: string;
  name: string;
  description: string;
  created_at: string;
  sprint_count: number;
  current_sprint_id: string | null;
}

export interface ProjectCreate {
  name: string;
  description?: string;
}

// === Sprints ===
export type SprintStatus = 'created' | 'planning' | 'in_progress' | 'review' | 'completed' | 'failed' | 'cancelled';

export interface Sprint {
  sprint_id: string;
  project_id: string;
  sprint_number: number;
  goal: string;
  status: SprintStatus;
  created_at: string;
  completed_at: string | null;
}

export interface SprintCreate {
  goal: string;
}

export interface SprintMetrics {
  sprint_id: string;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  total_cost_usd: number;
  total_tokens: number;
  duration_seconds: number | null;
}

export interface GoalTree {
  sprint_id: string;
  goal: string;
  tasks: TaskNode[];
}

export interface TaskNode {
  task_id: string;
  title: string;
  status: string;
  children: TaskNode[];
}

// === Tasks ===
export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'blocked';

export interface Task {
  task_id: string;
  title: string;
  description: string;
  acceptance_criteria: string[];
  assigned_to: string;
  priority: number;
  status: TaskStatus;
  dependencies: string[];
  result: Record<string, unknown> | null;
  review: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

// === Agents ===
export type AutonomyLevel = 'low' | 'medium' | 'high';

export interface AgentConfig {
  project_id: string;
  agent_role: string;
  autonomy_level: AutonomyLevel;
  model: string;
  enabled: boolean;
}

export interface AgentConfigUpdate {
  autonomy_level?: AutonomyLevel;
  model?: string;
  enabled?: boolean;
}

// === Approvals ===
export type ApprovalStatus = 'pending' | 'approved' | 'rejected';

export interface Approval {
  approval_id: string;
  sprint_id: string;
  agent_id: string;
  action_type: string;
  title: string;
  status: ApprovalStatus;
  created_at: string;
}

export interface ApprovalDecision {
  comment?: string;
}

// === Events & Messages ===
export interface SprintEvent {
  event_id: number;
  event_type: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface AgentMessage {
  message_id: number;
  sprint_id: string;
  agent_id: string;
  content: string;
  message_type: string;
  timestamp: string;
}

// === Artifacts ===
export interface Artifact {
  artifact_id: string;
  sprint_id: string;
  task_id: string;
  agent_id: string;
  artifact_type: string;
  file_path: string;
  size_bytes: number;
  created_at: string;
}

// === Analytics ===
export interface CostBreakdown {
  total_cost_usd: number;
  total_tokens: number;
  by_agent: Record<string, { cost_usd: number; tokens: number }>;
}

export interface BudgetStatus {
  sprint_budget_usd: number;
  spent_usd: number;
  remaining_usd: number;
  percentage_used: number;
}

// === Templates ===
export interface TeamTemplate {
  id: string;
  name: string;
  description: string;
  author: string;
  version: string;
  agents: TemplateAgent[];
  tags: string[];
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface TemplateAgent {
  role: string;
  model: string;
  autonomy: AutonomyLevel;
  system_prompt?: string;
}

export interface CreateTemplateRequest {
  name: string;
  description: string;
  agents: TemplateAgent[];
  tags?: string[];
}

// === Teams ===
export interface Team {
  id: string;
  name: string;
  description: string;
  project_id: string;
  agents: AgentConfig[];
  template_id: string | null;
  created_at: string;
}

export interface CreateTeamRequest {
  name: string;
  description: string;
  template_id?: string;
}

// === Learnings ===
export interface Learning {
  learning_id: string;
  project_id: string;
  sprint_id: string;
  content: string;
  category: string;
  created_at: string;
}

// === WebSocket Events ===
export type WSEventType =
  | 'sprint.started' | 'sprint.paused' | 'sprint.completed' | 'sprint.failed'
  | 'task.created' | 'task.started' | 'task.completed' | 'task.failed'
  | 'agent.thinking' | 'agent.action' | 'agent.message'
  | 'artifact.created' | 'artifact.updated'
  | 'approval.requested' | 'approval.resolved'
  | 'budget.warning' | 'budget.exceeded'
  | 'connection.established';

export interface WSEvent {
  type: WSEventType;
  data: Record<string, unknown>;
  timestamp: string;
  sequence: number;
}

// === Analytics v0.2.3 ===
export interface SprintCostPoint {
  sprint_id: string;
  sprint_number: number;
  date: string;
  cost_usd: number;
  cumulative_cost_usd: number;
}

export interface SprintSummary {
  sprint_id: string;
  sprint_number: number;
  goal: string;
  status: SprintStatus;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  completion_rate: number;
  duration_seconds: number | null;
  created_at: string;
  completed_at: string | null;
}

export interface AgentMetrics {
  agent_role: string;
  tasks_completed: number;
  tasks_failed: number;
  avg_duration_seconds: number;
  total_cost_usd: number;
  cost_per_task_usd: number;
}

export interface GlobalAnalytics {
  total_spend_usd: number;
  total_sprints: number;
  completed_sprints: number;
  failed_sprints: number;
  success_rate: number;
  top_agents: { role: string; tasks_completed: number }[];
}

// === Settings ===
export interface GlobalSettings {
  default_model: string;
  default_autonomy: AutonomyLevel;
  budget_per_sprint_usd: number | null;
  budget_monthly_usd: number | null;
  notifications: NotificationSettings;
  theme: 'dark' | 'light' | 'system';
}

export interface NotificationSettings {
  sound_enabled: boolean;
  browser_push_enabled: boolean;
  notify_on_approval: boolean;
  notify_on_sprint_complete: boolean;
  notify_on_error: boolean;
  notify_on_budget_warning: boolean;
}

export interface ApiKeyInfo {
  provider: string;
  masked_key: string;
  is_valid: boolean | null;
  last_tested: string | null;
}

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

// === API Response Wrappers ===
export interface ListResponse<T> {
  items: T[];
  total: number;
}

// === Store Type Aliases (for compatibility with legacy stores) ===
export interface SprintResponse extends Sprint {
  tasks: Task[];
  metrics?: SprintMetrics;
  error?: string | null;
}

export type TaskResponse = Task;
export type ApprovalRequest = Approval;
export type WSMessage = WSEvent;
