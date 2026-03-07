"""Multi-team coordination models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DependencyStatus(str, Enum):
    """Cross-team dependency status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class Team(BaseModel):
    """Team model for multi-team coordination."""
    id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    name: str
    description: str = ""
    project_id: str

    # Team composition - stored as dicts to avoid circular imports
    agents: list[dict[str, Any]]
    template_id: str | None = None

    # Coordination
    lead_agent: str | None = None  # Agent role acting as team lead
    coordination_channel: str | None = None  # Slack channel

    # Sprint configuration
    sprint_config: dict[str, Any]
    current_sprint_id: str | None = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CrossTeamDependency(BaseModel):
    """Cross-team dependency model."""
    id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    dependent_team_id: str
    provider_team_id: str

    # Dependency details
    dependency_type: str  # "api", "component", "data", "deployment"
    title: str
    description: str = ""

    # Status tracking
    status: DependencyStatus = DependencyStatus.PENDING
    due_date: datetime | None = None
    priority: str = "medium"  # "low", "medium", "high", "critical"

    # Communication
    discussion_thread: str | None = None  # Slack thread
    resolution_notes: str | None = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None


class CreateTeamRequest(BaseModel):
    """Request model for creating a team."""
    name: str
    description: str = ""
    template_id: str | None = None
    lead_agent: str | None = None
    coordination_channel: str | None = None


class CreateDependencyRequest(BaseModel):
    """Request model for creating cross-team dependency."""
    provider_team_id: str
    dependency_type: str
    title: str
    description: str = ""
    due_date: datetime | None = None
    priority: str = "medium"


class MultiTeamSprintPlan(BaseModel):
    """Coordinated sprint plan across multiple teams."""
    id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    project_id: str
    teams: list[str]  # Team IDs

    # Planning details
    coordinated_goals: dict[str, Any]  # Team goals and coordination
    dependencies: list[str]  # Dependency IDs
    conflicts: list[dict[str, Any]] = Field(default_factory=list)

    # Timeline
    planned_start: datetime
    planned_end: datetime

    # Status
    status: str = "planned"
    created_at: datetime = Field(default_factory=datetime.utcnow)
