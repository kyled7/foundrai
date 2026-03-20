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
  expires_at: string | null;
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
  cost_summary?: {
    total_cost: number;
    total_tokens: number;
    by_agent: Record<string, { cost_usd: number; tokens: number }>;
    by_task: Record<string, { cost_usd: number; tokens: number }>;
  };
}

// === Model Recommendations ===

export type RecommendationConfidence = 'high' | 'medium' | 'low' | 'insufficient_data';
export type TaskComplexity = 'simple' | 'moderate' | 'complex' | 'critical';

export interface PerformanceMetrics {
  model: string;
  agent_role: AgentRole;
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
  agent_role: AgentRole;
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
  agent_role: AgentRole;
  project_id: string;
  models: PerformanceMetrics[];
  best_for_quality: string | null;
  best_for_cost: string | null;
  best_overall: string | null;
  created_at: string;
}
