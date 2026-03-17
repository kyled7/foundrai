// === Enums ===

export type SprintStatus = 'created' | 'planning' | 'executing' | 'reviewing' | 'completed' | 'failed' | 'cancelled';
export type TaskStatus = 'backlog' | 'in_progress' | 'in_review' | 'done' | 'failed' | 'blocked';
export type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'expired';
export type AgentRole = 'product_manager' | 'developer' | 'qa_engineer' | 'architect' | 'designer' | 'devops';

// === API Responses ===

export interface ProjectResponse {
  project_id: string;
  name: string;
  description: string;
  created_at: string;
  sprint_count: number;
  current_sprint_id: string | null;
}

export interface SprintResponse {
  sprint_id: string;
  project_id: string;
  sprint_number: number;
  goal: string;
  status: SprintStatus;
  tasks: TaskResponse[];
  metrics: SprintMetricsResponse;
  created_at: string;
  completed_at: string | null;
  error: string | null;
}

export interface TaskResponse {
  task_id: string;
  title: string;
  description: string;
  acceptance_criteria: string[];
  assigned_to: AgentRole;
  priority: number;
  status: TaskStatus;
  dependencies: string[];
  result: TaskResultResponse | null;
  review: ReviewResultResponse | null;
  created_at: string;
  updated_at: string;
}

export interface TaskResultResponse {
  agent_id: string;
  success: boolean;
  output: string;
  artifacts: ArtifactResponse[];
  tokens_used: number;
  completed_at: string;
}

export interface ReviewResultResponse {
  reviewer_id: string;
  passed: boolean;
  issues: string[];
  suggestions: string[];
  reviewed_at: string;
}

export interface ArtifactResponse {
  artifact_id: string;
  sprint_id: string;
  task_id: string;
  agent_id: string;
  artifact_type: string;
  file_path: string;
  size_bytes: number;
  created_at: string;
}

export interface SprintMetricsResponse {
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  total_tokens: number;
  total_llm_calls: number;
  duration_seconds: number;
  completion_rate: number;
  tasks_by_status: Record<string, number>;
  tokens_by_agent: Record<string, number>;
}

export interface ApprovalRequest {
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

// === WebSocket ===

export interface WSMessage {
  type: string;
  data: Record<string, unknown>;
  timestamp: string;
  sequence: number;
}

// === Goal Tree ===

export interface GoalTreeNode {
  id: string;
  type: 'goal' | 'task';
  label: string;
  status: TaskStatus | null;
  assigned_to: AgentRole | null;
  metadata: Record<string, unknown>;
}

export interface GoalTreeEdge {
  source: string;
  target: string;
  type: 'dependency' | 'decomposition';
}

export interface GoalTreeResponse {
  nodes: GoalTreeNode[];
  edges: GoalTreeEdge[];
}

// === Phase 2 Types ===

export interface AgentConfig {
  agent_role: AgentRole;
  autonomy_level: string;
  model: string;
  enabled: boolean;
}

export interface LearningResponse {
  learning_id: string;
  content: string;
  category: string;
  sprint_id: string;
  project_id: string;
  created_at: string;
}

export interface RetroResponse {
  went_well: string[];
  went_wrong: string[];
  action_items: string[];
  learnings_count: number;
}
