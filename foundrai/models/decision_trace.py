"""Decision trace model for tracking LLM reasoning chains."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class DecisionTrace:
    """Single LLM decision trace record."""

    trace_id: int | None = None
    event_id: int | None = None
    task_id: str | None = None
    sprint_id: str | None = None
    agent_role: str = ""
    model: str = ""
    prompt: str = ""
    response: str = ""
    thinking: str | None = None
    tool_calls: list = field(default_factory=list)
    tokens_used: int = 0
    cost_usd: float = 0.0
    duration_ms: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
