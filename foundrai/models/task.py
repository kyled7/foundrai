"""Task models."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from foundrai.models.enums import AgentRoleName, TaskStatus


def _generate_id() -> str:
    return str(uuid.uuid4())


class TaskResult(BaseModel):
    """Result of a task execution by an agent."""

    task_id: str
    agent_id: str
    success: bool
    output: str
    artifacts: list[dict] = Field(default_factory=list)
    tokens_used: int = 0
    completed_at: datetime = Field(default_factory=datetime.utcnow)


class ReviewResult(BaseModel):
    """Result of QA review."""

    task_id: str
    reviewer_id: str
    passed: bool
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    reviewed_at: datetime = Field(default_factory=datetime.utcnow)


class Task(BaseModel):
    """A single unit of work within a sprint."""

    id: str = Field(default_factory=_generate_id)
    title: str
    description: str
    acceptance_criteria: list[str] = Field(default_factory=list)
    assigned_to: AgentRoleName = AgentRoleName.DEVELOPER
    priority: int = 3
    status: TaskStatus = TaskStatus.BACKLOG
    dependencies: list[str] = Field(default_factory=list)
    result: TaskResult | None = None
    review: ReviewResult | None = None
    estimated_tokens: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"use_enum_values": True}
