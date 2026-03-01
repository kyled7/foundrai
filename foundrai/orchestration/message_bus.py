"""In-process async message bus for inter-agent communication."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Callable

from foundrai.models.message import AgentMessage
from foundrai.persistence.event_log import EventLog


class MessageBus:
    """In-process async message bus."""

    def __init__(self, event_log: EventLog) -> None:
        self._queues: dict[str, asyncio.Queue[AgentMessage]] = defaultdict(asyncio.Queue)
        self._listeners: list[Callable] = []
        self._event_log = event_log
        self._all_messages: list[AgentMessage] = []

    async def publish(self, message: AgentMessage) -> None:
        """Publish a message."""
        self._all_messages.append(message)

        # Log to event store
        await self._event_log.append(
            event_type="agent.message",
            data=message.model_dump(mode="json"),
        )

        # Notify listeners
        for listener in self._listeners:
            await listener(message)

        if message.to_agent:
            await self._queues[message.to_agent].put(message)
        else:
            for agent_id, queue in self._queues.items():
                if agent_id != message.from_agent:
                    await queue.put(message)

    async def consume(self, agent_id: str) -> list[AgentMessage]:
        """Consume all pending messages for an agent (non-blocking)."""
        queue = self._queues[agent_id]
        messages = []
        while not queue.empty():
            messages.append(queue.get_nowait())
        return messages

    def register_listener(self, callback: Callable) -> None:
        """Register a callback for all messages."""
        self._listeners.append(callback)

    def unregister_listener(self, callback: Callable) -> None:
        """Remove a listener."""
        self._listeners.remove(callback)

    def get_history(self) -> list[AgentMessage]:
        """Return all messages in order."""
        return list(self._all_messages)

    def register_agent(self, agent_id: str) -> None:
        """Ensure a queue exists for this agent."""
        _ = self._queues[agent_id]
