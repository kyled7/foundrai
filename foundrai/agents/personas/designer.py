"""Designer agent."""

from __future__ import annotations

from typing import TYPE_CHECKING

from foundrai.agents.base import BaseAgent
from foundrai.models.task import Task, TaskResult

if TYPE_CHECKING:
    from foundrai.models.task import ReviewResult


class DesignerAgent(BaseAgent):
    """Designer — UI/UX specs, design decisions."""

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute design tasks."""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"## Task: {task.title}\n\n{task.description}"},
        ]
        result = await self.runtime.run(messages)
        return TaskResult(
            task_id=task.id,
            agent_id=self.agent_id,
            success=result.success,
            output=result.output,
            tokens_used=result.tokens_used,
        )

    async def decompose_goal(self, goal: str) -> list[Task]:
        """Designer does not decompose goals."""
        raise NotImplementedError

    async def review_task(self, task: Task, result: TaskResult) -> ReviewResult:
        """Designer does not review tasks."""
        raise NotImplementedError
