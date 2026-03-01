"""Agent message model."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from foundrai.models.enums import MessageType


class AgentMessage(BaseModel):
    """A message sent between agents via the MessageBus."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType
    from_agent: str
    to_agent: str | None = None
    content: str
    metadata: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
