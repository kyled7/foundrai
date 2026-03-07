"""Token usage tracking models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class TokenUsage:
    """Single LLM call token usage record."""

    usage_id: int | None = None
    task_id: str | None = None
    sprint_id: str | None = None
    project_id: str | None = None
    agent_role: str = ""
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
