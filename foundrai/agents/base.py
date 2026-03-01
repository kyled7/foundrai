"""BaseAgent abstract class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from foundrai.agents.context import SprintContext
    from foundrai.agents.roles import AgentRole
    from foundrai.agents.runtime import AgentRuntime
    from foundrai.models.message import AgentMessage
    from foundrai.models.task import ReviewResult, Task, TaskResult
    from foundrai.orchestration.message_bus import MessageBus
    from foundrai.tools.base import BaseTool


class BaseAgent(ABC):
    """Abstract base class for all FoundrAI agents."""

    def __init__(
        self,
        role: AgentRole,
        model: str,
        tools: list[BaseTool],
        message_bus: MessageBus,
        sprint_context: SprintContext,
        runtime: AgentRuntime | None = None,
    ) -> None:
        self.role = role
        self.model = model
        self.tools = tools
        self.message_bus = message_bus
        self.sprint_context = sprint_context
        self.runtime = runtime
        self.working_memory: list[AgentMessage] = []

    @property
    def agent_id(self) -> str:
        """Unique identifier."""
        return self.role.name.value if hasattr(self.role.name, "value") else str(self.role.name)

    @abstractmethod
    async def execute_task(self, task: Task) -> TaskResult:
        """Execute a single task and return the result."""
        ...

    @abstractmethod
    async def decompose_goal(self, goal: str) -> list[Task]:
        """Decompose a high-level goal into tasks."""
        ...

    @abstractmethod
    async def review_task(self, task: Task, result: TaskResult) -> ReviewResult:
        """Review a completed task result."""
        ...

    async def send_message(self, message: AgentMessage) -> None:
        """Send a message through the MessageBus."""
        await self.message_bus.publish(message)

    async def receive_messages(self) -> list[AgentMessage]:
        """Receive pending messages from the MessageBus."""
        return await self.message_bus.consume(self.agent_id)

    def get_system_prompt(self) -> str:
        """Build the system prompt from role persona + sprint context."""
        persona = self.role.persona_override or self.role.persona
        context = self.sprint_context.to_prompt_string()
        return f"{persona}\n\n## Current Sprint Context\n{context}"
