"""Integration models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IntegrationStatus(str, Enum):
    """Integration status enumeration."""
    DISABLED = "disabled"
    ENABLED = "enabled"
    ERROR = "error"
    CONFIGURING = "configuring"


class IntegrationType(str, Enum):
    """Integration type enumeration."""
    SOURCE_CONTROL = "source_control"
    PROJECT_MANAGEMENT = "project_management"
    COMMUNICATION = "communication"
    CI_CD = "ci_cd"
    MONITORING = "monitoring"


class IntegrationConfig(BaseModel):
    """Integration configuration model."""
    id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    name: str  # 'github', 'jira', 'slack'
    project_id: str
    integration_type: IntegrationType

    # Configuration
    config: dict[str, Any] = Field(default_factory=dict)
    encrypted_config: dict[str, str] = Field(default_factory=dict)  # Sensitive data

    # Status
    status: IntegrationStatus = IntegrationStatus.DISABLED
    enabled: bool = True
    last_sync: datetime | None = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: str | None = None


class ExternalTaskMapping(BaseModel):
    """Mapping between FoundrAI tasks and external system tasks."""
    id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    task_id: str
    external_system: str  # 'jira', 'linear', 'github'
    external_task_id: str
    external_url: str | None = None

    # Sync tracking
    last_sync: datetime | None = None
    # "foundrai_to_external", "external_to_foundrai", "bidirectional"
    sync_direction: str = "bidirectional"

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GitHubWebhookRequest(BaseModel):
    """GitHub webhook request model."""
    event: str
    action: str
    repository: dict[str, Any]
    pull_request: dict[str, Any] | None = None
    issue: dict[str, Any] | None = None


class SlackEventRequest(BaseModel):
    """Slack event request model."""
    type: str
    event: dict[str, Any] | None = None
    challenge: str | None = None  # For URL verification
