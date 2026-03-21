"""Model recommendation and performance tracking models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from foundrai.models.enums import AgentRoleName


class RecommendationConfidence(str, Enum):
    """Confidence level for model recommendations."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT_DATA = "insufficient_data"


class TaskComplexity(str, Enum):
    """Task complexity categories for model selection."""

    SIMPLE = "simple"  # Simple formatting, basic QA
    MODERATE = "moderate"  # Standard development tasks
    COMPLEX = "complex"  # Architecture, complex planning
    CRITICAL = "critical"  # High-stakes decisions


class PerformanceMetrics(BaseModel):
    """Historical performance metrics for a model on specific tasks."""

    model: str
    agent_role: AgentRoleName
    task_complexity: TaskComplexity | None = None

    # Performance metrics
    success_rate: float = 0.0  # Percentage of successful completions (0-100)
    quality_score: float = 0.0  # Average quality score from reviews (0-100)
    avg_tokens_per_task: float = 0.0
    avg_cost_per_task: float = 0.0
    avg_execution_time: float = 0.0  # Average time in seconds

    # Raw counts for calculation
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0

    # Context
    project_id: str | None = None
    sprint_id: str | None = None

    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"use_enum_values": True}


class ModelRecommendation(BaseModel):
    """Recommendation for which model to use for a specific agent role."""

    id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    project_id: str
    agent_role: AgentRoleName

    # Recommendation details
    recommended_model: str
    current_model: str | None = None
    confidence: RecommendationConfidence = RecommendationConfidence.MEDIUM

    # Supporting data
    reasoning: str = ""  # Human-readable explanation
    expected_quality_score: float = 0.0  # Predicted quality (0-100)
    expected_cost_per_task: float = 0.0  # Predicted cost in USD
    expected_success_rate: float = 0.0  # Predicted success rate (0-100)

    # Performance comparison
    performance_metrics: PerformanceMetrics | None = None
    alternative_models: list[str] = Field(default_factory=list)

    # Context
    task_complexity: TaskComplexity | None = None
    quality_requirements: str | None = None  # "high", "medium", "low"
    cost_constraints: float | None = None  # Max budget per task in USD

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None  # Recommendation validity period

    model_config = {"use_enum_values": True}


class CostSavingsEstimate(BaseModel):
    """Cost savings analysis comparing different model configurations."""

    id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    project_id: str

    # Current configuration
    current_total_cost: float = 0.0  # Current config total cost in USD
    current_config: dict[str, str] = Field(default_factory=dict)  # role -> model

    # Recommended configuration
    recommended_total_cost: float = 0.0  # Recommended config total cost in USD
    recommended_config: dict[str, str] = Field(default_factory=dict)  # role -> model

    # Savings analysis
    total_savings_usd: float = 0.0
    savings_percentage: float = 0.0  # Percentage savings (0-100)

    # Per-role breakdown
    role_breakdown: dict[str, dict[str, float]] = Field(default_factory=dict)
    # Example: {"developer": {"current_cost": 0.50, "recommended_cost": 0.30, "savings": 0.20}}

    # Quality impact
    quality_impact: str = "neutral"  # "improved", "neutral", "degraded"
    quality_score_change: float = 0.0  # Expected quality change (-100 to +100)

    # Analysis context
    based_on_tasks: int = 0  # Number of historical tasks analyzed
    confidence: RecommendationConfidence = RecommendationConfidence.MEDIUM

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sprint_id: str | None = None

    model_config = {"use_enum_values": True}


class ModelPerformanceComparison(BaseModel):
    """Compare performance of multiple models for a specific role."""

    agent_role: AgentRoleName
    project_id: str

    # Models being compared
    models: list[PerformanceMetrics] = Field(default_factory=list)

    # Winner
    best_for_quality: str | None = None
    best_for_cost: str | None = None
    best_overall: str | None = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"use_enum_values": True}
