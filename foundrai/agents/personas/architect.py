"""Architect agent."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from foundrai.agents.base import BaseAgent
from foundrai.models.task import Task, TaskResult

if TYPE_CHECKING:
    from foundrai.models.task import ReviewResult


class ArchitectAgent(BaseAgent):
    """Architect — system design, tech decisions, plan review."""

    async def review_plan(self, tasks: list[Task], context: Any) -> list[Task]:
        """Review and enhance the task plan with technical considerations."""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {
                "role": "user",
                "content": (
                    "Review these tasks and add technical considerations:\n"
                    + json.dumps(
                        [
                            {
                                "title": t.title,
                                "description": t.description,
                                "acceptance_criteria": t.acceptance_criteria,
                            }
                            for t in tasks
                        ]
                    )
                ),
            },
        ]
        result = await self.runtime.run(messages, response_format="json")

        if result.parsed and isinstance(result.parsed, list):
            for i, item in enumerate(result.parsed):
                if i < len(tasks) and isinstance(item, dict):
                    extra_criteria = item.get("additional_criteria", [])
                    if extra_criteria:
                        tasks[i].acceptance_criteria.extend(extra_criteria)
        return tasks

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute architecture/design tasks."""
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
        """Architect does not decompose goals."""
        raise NotImplementedError

    async def review_task(self, task: Task, result: TaskResult) -> ReviewResult:
        """Architect does not review tasks in Phase 0."""
        raise NotImplementedError
