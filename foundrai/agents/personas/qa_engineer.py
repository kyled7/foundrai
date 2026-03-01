"""QA Engineer agent."""

from __future__ import annotations

import json

from foundrai.agents.base import BaseAgent
from foundrai.models.task import ReviewResult, Task, TaskResult


class QAEngineerAgent(BaseAgent):
    """QA agent — reviews code and runs tests."""

    async def review_task(self, task: Task, result: TaskResult) -> ReviewResult:
        """Review a completed task."""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": self._build_review_prompt(task, result)},
        ]
        review_output = await self.runtime.run(messages, response_format="json")

        parsed = review_output.parsed or {}
        if isinstance(parsed, str):
            try:
                parsed = json.loads(parsed)
            except json.JSONDecodeError:
                parsed = {}

        return ReviewResult(
            task_id=task.id,
            reviewer_id=self.agent_id,
            passed=parsed.get("passed", False) if isinstance(parsed, dict) else False,
            issues=parsed.get("issues", []) if isinstance(parsed, dict) else [],
            suggestions=parsed.get("suggestions", []) if isinstance(parsed, dict) else [],
        )

    def _build_review_prompt(self, task: Task, result: TaskResult) -> str:
        """Build review prompt."""
        criteria = "\n".join(f"- {ac}" for ac in task.acceptance_criteria)
        return (
            f"## Review Task: {task.title}\n\n"
            f"**Acceptance Criteria:**\n{criteria}\n\n"
            f"**Developer Output:**\n{result.output}\n\n"
            "Review this task. If sandbox is unavailable, do a code-review-only analysis.\n"
            "Return JSON: {\"passed\": bool, \"issues\": [...], \"suggestions\": [...]}"
        )

    async def execute_task(self, task: Task) -> TaskResult:
        """QA does not execute implementation tasks."""
        raise NotImplementedError

    async def decompose_goal(self, goal: str) -> list[Task]:
        """QA does not decompose goals."""
        raise NotImplementedError
