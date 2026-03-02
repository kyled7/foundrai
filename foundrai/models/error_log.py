"""Error log model for structured error tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass
class ErrorLog:
    """Structured error log entry."""

    error_id: int | None = None
    task_id: str | None = None
    sprint_id: str | None = None
    agent_role: str = ""
    error_type: str = "unknown"  # rate_limit|context_overflow|timeout|tool_error|parse_error|unknown
    error_message: str = ""
    traceback: str = ""
    context_json: str = "{}"
    suggested_fix: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
