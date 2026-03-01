"""Developer agent."""

from __future__ import annotations

from typing import TYPE_CHECKING

from foundrai.agents.base import BaseAgent
from foundrai.models.task import Task, TaskResult

if TYPE_CHECKING:
    from foundrai.models.task import ReviewResult


class DeveloperAgent(BaseAgent):
    """Developer agent — writes code from task specs."""

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute a development task using tools."""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": self._build_task_prompt(task)},
        ]
        result = await self.runtime.run(messages, tools=self.tools)

        return TaskResult(
            task_id=task.id,
            agent_id=self.agent_id,
            success=result.success,
            output=result.output,
            artifacts=result.artifacts,
            tokens_used=result.tokens_used,
        )

    def _build_task_prompt(self, task: Task) -> str:
        """Build task execution prompt."""
        criteria = "\n".join(f"- {ac}" for ac in task.acceptance_criteria)
        return (
            f"## Task: {task.title}\n\n"
            f"**Description:** {task.description}\n\n"
            f"**Acceptance Criteria:**\n{criteria}\n\n"
            f"**Project directory:** {self.sprint_context.project_path}\n\n"
            "Implement this task. Write all files to the project directory."
        )

    async def decompose_goal(self, goal: str) -> list[Task]:
        """Developer does not decompose goals."""
        raise NotImplementedError

    async def review_task(self, task: Task, result: TaskResult) -> ReviewResult:
        """Developer does not review tasks."""
        raise NotImplementedError
