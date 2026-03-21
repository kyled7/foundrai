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
  cost_usd?: number;
  tokens_used?: number;
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

// === Autonomy Configuration (Granular) ===
export type ActionType =
  | 'code_write'
  | 'code_execute'
  | 'file_create'
  | 'file_modify'
  | 'file_delete'
  | 'git_commit'
  | 'git_push'
  | 'api_call'
  | 'tool_use'
  | 'task_create'
  | 'task_assign'
  | 'message_send'
  | 'code_review'
  | 'deployment';

export type AutonomyMode = 'auto_approve' | 'notify' | 'require_approval' | 'block';

export interface TrustScore {
  agent_role: string;
  action_type: ActionType;
  success_count: number;
  total_count: number;
  last_updated: string;
  success_rate: number;
  recommendation: string | null;
}

export interface AutonomyMatrix {
  project_id: string;
  matrix: Record<string, Record<ActionType, AutonomyMode>>;
  created_at: string;
  updated_at: string;
}

export interface AutonomyProfile {
  profile_id: string;
  name: string;
  description: string;
  matrix: Record<string, Record<ActionType, AutonomyMode>>;
  is_builtin: boolean;
  created_at: string;
}

// === Agent Health ===
export type AgentHealthStatus = 'healthy' | 'warning' | 'unhealthy' | 'no_data';

export interface AgentHealthMetrics {
  completion_rate: number;
  quality_score: number;
  cost_efficiency: number;
  avg_execution_time: number;
  failure_rate: number;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  total_tokens: number;
  total_cost_usd: number;
}

export interface AgentHealth {
  agent_role: string;
  project_id: string;
  sprint_id: string | null;
  health_score: number;
  status: AgentHealthStatus;
  metrics: AgentHealthMetrics;
  recommendations: string[];
  timestamp: string;
}

export interface ProjectAgentHealthResponse {
  project_id: string;
  agents: AgentHealth[];
}

export interface SprintAgentHealthResponse {
  sprint_id: string;
  agents: AgentHealth[];
}

// === Approvals ===
export type ApprovalStatus = 'pending' | 'approved' | 'rejected';

export interface Approval {
  approval_id: string;
  sprint_id: string;
  task_id: string | null;
  agent_id: string;
  action_type: string;
  title: string;
  description: string;
  context: Record<string, unknown>;
  status: ApprovalStatus;
  created_at: string;
  resolved_at: string | null;
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
  budget_usd: number;
  spent_usd: number;
  remaining_usd: number;
  percentage_used: number;
  is_warning: boolean;
  is_exceeded: boolean;
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
  pinned: boolean;
  status: string;
  created_at: string;
  updated_at: string;
}

// === WebSocket Events ===
export type WSEventType =
  | 'sprint.started' | 'sprint.paused' | 'sprint.completed' | 'sprint.failed'
  | 'sprint.status_changed' | 'sprint.planning_started' | 'sprint.planning_completed'
  | 'sprint.review_completed' | 'sprint.retrospective_started' | 'sprint.retrospective_completed'
  | 'task.created' | 'task.started' | 'task.completed' | 'task.failed' | 'task.status_changed'
  | 'agent.thinking' | 'agent.action' | 'agent.message' | 'agent.tool_call' | 'agent.tool_result'
  | 'artifact.created' | 'artifact.updated'
  | 'approval.requested' | 'approval.resolved'
  | 'cost_updated' | 'budget.warning' | 'budget.exceeded'
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

export interface SprintComparison {
  sprint_id: string;
  sprint_number: number;
  goal: string;
  task_count: number;
  completed_count: number;
  failed_count: number;
  pass_rate: number;
  total_tokens: number;
  total_cost: number;
  duration_seconds: number;
}

export interface BudgetHistoryPoint {
  sprint_id: string;
  sprint_number: number;
  goal: string;
  created_at: string;
  completed_at: string | null;
  budget_usd: number;
  spent_usd: number;
  remaining_usd: number;
  percentage_used: number;
  is_warning: boolean;
  is_exceeded: boolean;
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

// === Budget Configuration ===
export interface BudgetConfig {
  sprint_budget_usd: number | null;
  per_agent_budgets: Record<string, number | null>;
  warning_threshold_percent: number;
  model_tier_down_mapping?: Record<string, string>;
}

// === Model Recommendations ===
export type RecommendationConfidence = 'high' | 'medium' | 'low' | 'insufficient_data';
export type TaskComplexity = 'simple' | 'moderate' | 'complex' | 'critical';

export interface PerformanceMetrics {
  model: string;
  agent_role: string;
  task_complexity: TaskComplexity | null;
  success_rate: number;
  quality_score: number;
  avg_tokens_per_task: number;
  avg_cost_per_task: number;
  avg_execution_time: number;
  total_tasks: number;
  successful_tasks: number;
  failed_tasks: number;
  total_tokens: number;
  total_cost_usd: number;
  project_id: string | null;
  sprint_id: string | null;
  last_updated: string;
}

export interface ModelRecommendation {
  id: string;
  project_id: string;
  agent_role: string;
  recommended_model: string;
  current_model: string | null;
  confidence: RecommendationConfidence;
  reasoning: string;
  expected_quality_score: number;
  expected_cost_per_task: number;
  expected_success_rate: number;
  performance_metrics: PerformanceMetrics | null;
  alternative_models: string[];
  task_complexity: TaskComplexity | null;
  quality_requirements: string | null;
  cost_constraints: number | null;
  created_at: string;
  expires_at: string | null;
}

export interface CostSavingsEstimate {
  id: string;
  project_id: string;
  current_total_cost: number;
  current_config: Record<string, string>;
  recommended_total_cost: number;
  recommended_config: Record<string, string>;
  total_savings_usd: number;
  savings_percentage: number;
  role_breakdown: Record<string, { current_cost: number; recommended_cost: number; savings: number }>;
  quality_impact: string;
  quality_score_change: number;
  based_on_tasks: number;
  confidence: RecommendationConfidence;
  created_at: string;
  sprint_id: string | null;
}

export interface ModelPerformanceComparison {
  agent_role: string;
  project_id: string;
  models: PerformanceMetrics[];
  best_for_quality: string | null;
  best_for_cost: string | null;
  best_overall: string | null;
  created_at: string;
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
