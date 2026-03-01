"""Sprint context for agents."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from foundrai.models.task import Task


class SprintContext:
    """Provides sprint-level context to agents for prompt building."""

    def __init__(
        self,
        project_name: str,
        project_path: str,
        sprint_goal: str,
        sprint_number: int,
        tasks: list[Task] | None = None,
    ) -> None:
        self.project_name = project_name
        self.project_path = project_path
        self.sprint_goal = sprint_goal
        self.sprint_number = sprint_number
        self.tasks: list[Task] = tasks or []

    def to_prompt_string(self) -> str:
        """Build a prompt string from the sprint context."""
        task_summary = "\n".join(
            f"- [{t.status}] {t.title} (assigned: {t.assigned_to})"
            for t in self.tasks
        )
        return (
            f"Project: {self.project_name}\n"
            f"Sprint #{self.sprint_number}\n"
            f"Goal: {self.sprint_goal}\n"
            f"Project path: {self.project_path}\n\n"
            f"Tasks:\n{task_summary or 'No tasks yet.'}"
        )
