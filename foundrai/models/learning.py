"""Learning model for vector memory."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field


class Learning(BaseModel):
    """A learning stored in vector memory."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    category: str = "general"
    sprint_id: str = ""
    project_id: str = ""
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
