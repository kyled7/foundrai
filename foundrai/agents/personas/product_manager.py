"""Product Manager agent."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from foundrai.agents.base import BaseAgent
from foundrai.models.enums import AgentRoleName, MessageType
from foundrai.models.message import AgentMessage
from foundrai.models.task import Task, TaskResult

if TYPE_CHECKING:
    from foundrai.models.task import ReviewResult


class ProductManagerAgent(BaseAgent):
    """PM agent — decomposes goals into tasks with acceptance criteria."""

    async def decompose_goal(self, goal: str) -> list[Task]:
        """Call LLM to decompose goal into a structured task list."""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Decompose this goal into tasks:\n\n{goal}"},
        ]
        result = await self.runtime.run(messages, response_format="json")

        tasks = self._parse_tasks(result.parsed or result.output)

        await self.send_message(AgentMessage(
            type=MessageType.GOAL_DECOMPOSITION,
            from_agent=self.agent_id,
            to_agent=None,
            content=f"Decomposed goal into {len(tasks)} tasks",
            metadata={"task_count": len(tasks), "tasks": [t.title for t in tasks]},
        ))
        return tasks

    def _parse_tasks(self, data: Any) -> list[Task]:
        """Parse task data from LLM response."""
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return []

        if not isinstance(data, list):
            return []

        tasks: list[Task] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            assigned = item.get("assigned_to", "developer")
            if isinstance(assigned, str):
                try:
                    assigned = AgentRoleName(assigned)
                except ValueError:
                    assigned = AgentRoleName.DEVELOPER
            tasks.append(Task(
                title=item.get("title", "Untitled"),
                description=item.get("description", ""),
                acceptance_criteria=item.get("acceptance_criteria", []),
                dependencies=item.get("dependencies", []),
                assigned_to=assigned,
                priority=item.get("priority", 3),
            ))
        return tasks

    async def run_retrospective(self, state: dict) -> Any:
        """Run retrospective analysis."""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": (
                "Analyze this sprint and provide a retrospective.\n"
                f"Goal: {state.get('goal', '')}\n"
                f"Tasks: {len(state.get('tasks', []))}\n"
                "Return JSON with: went_well, went_wrong, action_items, learnings"
            )},
        ]
        result = await self.runtime.run(messages, response_format="json")
        return result

    async def refine_with_learnings(
        self, tasks: list[Task], learnings: list[Any]
    ) -> list[Task]:
        """Refine tasks based on past learnings from vector memory."""
        if not learnings:
            return tasks

        learnings_text = "\n".join(
            f"- {lr.content}" if hasattr(lr, "content") else f"- {lr}"
            for lr in learnings
        )
        task_summaries = "\n".join(
            f"- {t.title}: {t.description}" for t in tasks
        )

        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": (
                "Review these tasks based on lessons learned from previous sprints.\n\n"
                f"## Past Learnings:\n{learnings_text}\n\n"
                f"## Current Tasks:\n{task_summaries}\n\n"
                "Return a JSON array of refined tasks. Each task should have: "
                "title, description, acceptance_criteria, dependencies, assigned_to, priority. "
                "Apply the learnings to improve task quality, add missing criteria, "
                "adjust priorities, or split/merge tasks as needed."
            )},
        ]
        result = await self.runtime.run(messages, response_format="json")
        refined = self._parse_tasks(result.parsed or result.output)
        return refined if refined else tasks

    async def execute_task(self, task: Task) -> TaskResult:
        """PM does not execute implementation tasks."""
        raise NotImplementedError("PM does not execute implementation tasks")

    async def review_task(self, task: Task, result: TaskResult) -> ReviewResult:
        """PM does not review tasks."""
        raise NotImplementedError("PM does not review tasks")
