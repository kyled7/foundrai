"""Sprint models."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from pydantic import BaseModel

if TYPE_CHECKING:
    from foundrai.models.enums import SprintStatus
    from foundrai.models.message import AgentMessage
    from foundrai.models.task import Task


class SprintMetrics(BaseModel):
    """Metrics collected during and after a sprint."""

    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_tokens: int = 0
    total_llm_calls: int = 0
    duration_seconds: float = 0.0

    @property
    def completion_rate(self) -> float:
        """Return the completion rate, safe from division by zero."""
        return self.completed_tasks / max(self.total_tasks, 1)


class SprintState(TypedDict, total=False):
    """Sprint state managed by the engine."""

    project_id: str
    sprint_id: str
    sprint_number: int
    goal: str
    status: SprintStatus
    tasks: list[Task]
    messages: list[AgentMessage]
    artifacts: list[dict]
    metrics: SprintMetrics
    created_at: str
    completed_at: str | None
    error: str | None
