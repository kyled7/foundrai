"""DevOps agent."""

from __future__ import annotations

from typing import TYPE_CHECKING

from foundrai.agents.base import BaseAgent
from foundrai.models.task import Task, TaskResult

if TYPE_CHECKING:
    from foundrai.models.task import ReviewResult


class DevOpsAgent(BaseAgent):
    """DevOps agent — handles CI/CD, deployment, and infrastructure tasks."""

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute a DevOps task (CI/CD config, Dockerfile, deployment scripts)."""
        prompt = (
            f"Task: {task.title}\n"
            f"Description: {task.description}\n"
            f"Acceptance Criteria:\n"
            + "\n".join(f"- {c}" for c in task.acceptance_criteria)
            + "\n\nCreate the necessary infrastructure files, CI/CD configs, "
            "Dockerfiles, or deployment scripts. Return a summary of files created."
        )
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": prompt},
        ]
        result = await self.runtime.run(messages, tools=self.tools)
        return TaskResult(
            success=result.success,
            output=result.output,
            artifacts=result.artifacts,
            tokens_used=result.tokens_used,
        )

    async def decompose_goal(self, goal: str) -> list[Task]:
        """DevOps does not decompose goals."""
        raise NotImplementedError("DevOps does not decompose goals")

    async def review_task(self, task: Task, result: TaskResult) -> ReviewResult:
        """DevOps does not review tasks."""
        raise NotImplementedError("DevOps does not review tasks")
