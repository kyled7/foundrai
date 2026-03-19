"""Agent health and quality monitoring models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from foundrai.models.enums import AgentRoleName


class AgentHealthMetrics(BaseModel):
    """Detailed metrics for agent health calculation."""

    completion_rate: float = 0.0  # Percentage of completed tasks (0-100)
    quality_score: float = 0.0  # Score based on QA feedback (0-100)
    cost_efficiency: float = 0.0  # Average tokens per completed task
    avg_execution_time: float = 0.0  # Average task execution time in seconds
    failure_rate: float = 0.0  # Percentage of failed tasks (0-100)

    # Raw counts for calculation
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0

    model_config = {"use_enum_values": True}


class AgentHealth(BaseModel):
    """Agent health status and performance tracking."""

    agent_role: AgentRoleName
    project_id: str
    sprint_id: str | None = None

    # Health status
    health_score: float = 0.0  # Overall health score (0-100)
    status: str = "healthy"  # healthy|warning|unhealthy

    # Detailed metrics
    metrics: AgentHealthMetrics = Field(default_factory=AgentHealthMetrics)

    # Actionable recommendations for improvement
    recommendations: list[str] = Field(default_factory=list)

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"use_enum_values": True}
