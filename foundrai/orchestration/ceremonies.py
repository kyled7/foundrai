"""Sprint ceremonies: Planning, Review, Retrospective."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from foundrai.models.enums import TaskStatus
from foundrai.models.learning import Learning
from foundrai.models.sprint import SprintState
from foundrai.models.task import Task


class ReviewSummary(BaseModel):
    """Summary of sprint review."""

    completed_count: int = 0
    failed_count: int = 0
    quality_score: float = 0.0
    incomplete_tasks: list[Any] = Field(default_factory=list)


class RetroSummary(BaseModel):
    """Summary of sprint retrospective."""

    went_well: list[str] = Field(default_factory=list)
    went_wrong: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    learnings: list[Learning] = Field(default_factory=list)


class SprintPlanning:
    """Sprint Planning ceremony orchestrator."""

    async def run(
        self,
        goal: str,
        agents: dict,
        context: Any,
        vector_memory: Any | None = None,
    ) -> list[Task]:
        """Run full planning ceremony."""
        pm = agents.get("product_manager")
        if not pm:
            return []

        tasks = await pm.decompose_goal(goal)

        # Architect reviews if available
        architect = agents.get("architect")
        if architect and hasattr(architect, "review_plan"):
            tasks = await architect.review_plan(tasks, context)

        # Retrieve past learnings
        if vector_memory:
            learnings = await vector_memory.query_relevant(
                goal, k=5,
                project_id=context.project_id if hasattr(context, "project_id") else None,
            )
            if learnings and hasattr(pm, "refine_with_learnings"):
                tasks = await pm.refine_with_learnings(tasks, learnings)

        # Estimate effort
        for task in tasks:
            task.estimated_tokens = self._estimate_effort(task)

        return tasks

    def _estimate_effort(self, task: Task) -> int:
        """Heuristic effort estimation."""
        base = 1000
        base += len(task.acceptance_criteria) * 500
        base += len(task.description) * 2
        return min(base, 8000)


class SprintReview:
    """Sprint Review ceremony."""

    async def run(self, state: SprintState, agents: dict) -> ReviewSummary:
        """Run sprint review."""
        tasks = state.get("tasks", [])
        completed = [t for t in tasks if t.status in (TaskStatus.DONE, "done")]
        failed = [t for t in tasks if t.status in (TaskStatus.FAILED, "failed")]

        quality_score = self._auto_score(completed, failed)

        return ReviewSummary(
            completed_count=len(completed),
            failed_count=len(failed),
            quality_score=quality_score,
            incomplete_tasks=[
                t for t in tasks
                if t.status not in (TaskStatus.DONE, TaskStatus.FAILED, "done", "failed")
            ],
        )

    def _auto_score(self, completed: list, failed: list) -> float:
        """Calculate quality score."""
        total = len(completed) + len(failed)
        if total == 0:
            return 0.0
        return len(completed) / total


class SprintRetrospective:
    """Sprint Retrospective — analyze and learn."""

    async def run(
        self,
        state: SprintState,
        agents: dict,
        vector_memory: Any | None = None,
        db: Any | None = None,
    ) -> RetroSummary:
        """Run retrospective, store learnings."""
        tasks = state.get("tasks", [])
        completed = [t for t in tasks if t.status in (TaskStatus.DONE, "done")]
        failed = [t for t in tasks if t.status in (TaskStatus.FAILED, "failed")]
        total = len(completed) + len(failed)
        rate = len(completed) / total if total > 0 else 0

        # Try PM-driven retrospective
        pm = agents.get("product_manager")
        if pm and hasattr(pm, "run_retrospective"):
            try:
                result = await pm.run_retrospective(state)
                parsed = result.parsed if hasattr(result, "parsed") else None
                if parsed and isinstance(parsed, dict):
                    learnings = []
                    for text in parsed.get("learnings", []):
                        learnings.append(Learning(
                            content=text,
                            category="process",
                            sprint_id=state.get("sprint_id", ""),
                            project_id=state.get("project_id", ""),
                        ))
                    # Add auto-generated completion rate learning
                    learnings.append(Learning(
                        content=f"Sprint completion rate: {rate:.0%}",
                        category="process",
                        sprint_id=state.get("sprint_id", ""),
                        project_id=state.get("project_id", ""),
                    ))

                    if vector_memory:
                        for lr in learnings:
                            await vector_memory.store_learning(lr)

                    return RetroSummary(
                        went_well=parsed.get("went_well", []),
                        went_wrong=parsed.get("went_wrong", []),
                        action_items=parsed.get("action_items", []),
                        learnings=learnings,
                    )
            except Exception:
                pass

        # Auto-generated retrospective
        learnings = [
            Learning(
                content=f"Sprint completion rate: {rate:.0%}",
                category="process",
                sprint_id=state.get("sprint_id", ""),
                project_id=state.get("project_id", ""),
            )
        ]
        if failed:
            learnings.append(Learning(
                content=f"{len(failed)} task(s) failed. Review task complexity.",
                category="quality",
                sprint_id=state.get("sprint_id", ""),
                project_id=state.get("project_id", ""),
            ))

        if vector_memory:
            for lr in learnings:
                await vector_memory.store_learning(lr)

        return RetroSummary(learnings=learnings)
