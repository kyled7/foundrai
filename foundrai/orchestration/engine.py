"""SprintEngine — orchestrates the sprint lifecycle."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from foundrai.config import FoundrAIConfig
from foundrai.models.enums import AgentRoleName, SprintStatus, TaskStatus
from foundrai.models.sprint import SprintMetrics, SprintState
from foundrai.models.task import Task
from foundrai.orchestration.ceremonies import SprintRetrospective, SprintReview
from foundrai.orchestration.message_bus import MessageBus
from foundrai.orchestration.task_graph import TaskGraph
from foundrai.persistence.artifact_store import ArtifactStore
from foundrai.persistence.event_log import EventLog
from foundrai.persistence.sprint_store import SprintStore


class SprintEngine:
    """Orchestrates the sprint lifecycle."""

    def __init__(
        self,
        config: FoundrAIConfig,
        agents: dict[str, Any],
        task_graph: TaskGraph,
        message_bus: MessageBus,
        sprint_store: SprintStore,
        event_log: EventLog,
        artifact_store: ArtifactStore,
        vector_memory: Any | None = None,
        error_store: Any | None = None,
    ) -> None:
        self.config = config
        self.agents = agents
        self.task_graph = task_graph
        self.message_bus = message_bus
        self.sprint_store = sprint_store
        self.event_log = event_log
        self.artifact_store = artifact_store
        self.vector_memory = vector_memory
        self.error_store = error_store
        self.graph = self._build_graph()

    def _build_graph(self) -> object:
        """Build a simple state machine (no LangGraph dependency for tests)."""
        return True  # Placeholder; actual execution in run_sprint

    async def run_sprint(self, goal: str, project_id: str) -> SprintState:
        """Execute a complete sprint from goal to completion."""
        sprint_id = str(uuid.uuid4())
        sprint_number = await self.sprint_store.next_sprint_number(project_id)

        state: SprintState = {
            "project_id": project_id,
            "sprint_id": sprint_id,
            "sprint_number": sprint_number,
            "goal": goal,
            "status": SprintStatus.CREATED,
            "tasks": [],
            "messages": [],
            "artifacts": [],
            "metrics": SprintMetrics(),
            "error": None,
        }

        await self.sprint_store.create_sprint(state)
        await self.event_log.append("sprint.started", {
            "sprint_id": sprint_id, "goal": goal,
        })

        # Plan
        state = await self._plan_node(state)
        route = self._route_after_plan(state)
        if route == "failed":
            state = await self._failed_node(state)
            return state

        # Execute
        state = await self._execute_node(state)

        # Review
        state = await self._review_node(state)

        # Retrospective
        state = await self._retrospective_node(state)

        # Complete
        state = await self._complete_node(state)
        return state

    async def _plan_node(self, state: SprintState) -> SprintState:
        """PLANNING node: PM decomposes goal into tasks."""
        state["status"] = SprintStatus.PLANNING
        await self._emit_status_change(state)

        pm_key = AgentRoleName.PRODUCT_MANAGER.value
        if pm_key not in self.agents:
            state["error"] = "Product Manager agent not available"
            return state

        pm = self.agents[pm_key]
        try:
            tasks = await pm.decompose_goal(state["goal"])
        except Exception as e:
            state["error"] = f"Planning failed: {e}"
            return state

        if not tasks:
            state["error"] = "Planning produced no tasks"
            return state

        # Resolve dependencies by title -> id
        title_to_id = {t.title: t.id for t in tasks}
        for task in tasks:
            resolved_deps = []
            for dep in task.dependencies:
                if dep in title_to_id:
                    resolved_deps.append(title_to_id[dep])
                else:
                    resolved_deps.append(dep)
            task.dependencies = resolved_deps

        # Build task graph
        self.task_graph.reset()
        for task in tasks:
            self.task_graph.add_task(task, depends_on=task.dependencies)

        state["tasks"] = tasks
        await self.sprint_store.update_tasks(state["sprint_id"], tasks)

        await self.event_log.append("sprint.planning_completed", {
            "sprint_id": state["sprint_id"],
            "task_count": len(tasks),
        })

        return state

    async def _execute_node(self, state: SprintState) -> SprintState:
        """EXECUTING node: Execute tasks (parallel where deps allow)."""
        state["status"] = SprintStatus.EXECUTING
        await self._emit_status_change(state)

        dev_key = AgentRoleName.DEVELOPER.value
        dev = self.agents.get(dev_key)

        max_parallel = self.config.sprint.max_tasks_parallel

        # Execute in waves based on dependency graph
        while True:
            ready = self.task_graph.get_ready_tasks()
            if not ready:
                break

            # Filter to dev-assigned tasks (QA excluded from execute)
            dev_tasks = [
                t for t in ready
                if t.assigned_to in (
                    AgentRoleName.DEVELOPER, AgentRoleName.DEVELOPER.value,
                    "developer",
                )
            ]

            # Mark non-dev tasks as done (skip them in execute)
            for t in ready:
                if t not in dev_tasks:
                    t.status = TaskStatus.DONE
                    self.task_graph.mark_completed(t.id)
                    await self._emit_task_status(t)

            if not dev_tasks:
                if not ready:
                    break
                continue

            if not dev:
                for t in dev_tasks:
                    t.status = TaskStatus.FAILED
                    self.task_graph.mark_completed(t.id)
                    await self._emit_task_status(t)
                break

            # Execute batch with concurrency limit
            sem = asyncio.Semaphore(max_parallel)

            async def execute_one(task: Task) -> None:
                async with sem:
                    task.status = TaskStatus.IN_PROGRESS
                    await self._emit_task_status(task)

                    try:
                        result = await dev.execute_task(task)
                        task.result = result
                        task.status = TaskStatus.IN_REVIEW if result.success else TaskStatus.FAILED

                        for artifact in result.artifacts:
                            await self.artifact_store.save(artifact)
                            state["artifacts"].append(artifact)
                    except Exception as exc:
                        task.status = TaskStatus.FAILED
                        await self._record_error(exc, task_id=task.id, sprint_id=state["sprint_id"], agent_role="developer")

                    self.task_graph.mark_completed(task.id)
                    await self._emit_task_status(task)

            await asyncio.gather(
                *[execute_one(t) for t in dev_tasks],
                return_exceptions=True,
            )

        return state

    async def _review_node(self, state: SprintState) -> SprintState:
        """REVIEWING node: QA reviews completed tasks."""
        state["status"] = SprintStatus.REVIEWING
        await self._emit_status_change(state)

        qa_key = AgentRoleName.QA_ENGINEER.value
        qa = self.agents.get(qa_key)

        # Run review ceremony
        review = SprintReview()
        await review.run(state, self.agents)
        await self.event_log.append("sprint.review_completed", {
            "sprint_id": state["sprint_id"],
        })

        if not qa:
            # Auto-pass tasks without QA
            for task in state["tasks"]:
                if task.status in (TaskStatus.IN_REVIEW, "in_review"):
                    task.status = TaskStatus.DONE
                    await self._emit_task_status(task)
            return state

        for task in state["tasks"]:
            if task.status not in (TaskStatus.IN_REVIEW, "in_review"):
                continue

            try:
                review_result = await qa.review_task(task, task.result)
                task.review = review_result
                task.status = TaskStatus.DONE if review_result.passed else TaskStatus.FAILED
            except Exception as exc:
                task.status = TaskStatus.FAILED
                await self._record_error(exc, task_id=task.id, sprint_id=state["sprint_id"], agent_role="qa_engineer")

            await self._emit_task_status(task)

        return state

    async def _retrospective_node(self, state: SprintState) -> SprintState:
        """RETROSPECTIVE node: Analyze sprint and generate learnings."""
        await self.event_log.append("sprint.retrospective_started", {
            "sprint_id": state["sprint_id"],
        })

        retro = SprintRetrospective()
        await retro.run(state, self.agents, self.vector_memory)

        await self.event_log.append("sprint.retrospective_completed", {
            "sprint_id": state["sprint_id"],
        })
        return state

    async def _complete_node(self, state: SprintState) -> SprintState:
        """COMPLETED node: Finalize sprint metrics."""
        state["status"] = SprintStatus.COMPLETED

        total = len(state["tasks"])
        done = sum(
            1 for t in state["tasks"]
            if t.status in (TaskStatus.DONE, "done")
        )
        failed = sum(
            1 for t in state["tasks"]
            if t.status in (TaskStatus.FAILED, "failed")
        )
        total_tokens = sum(
            t.result.tokens_used
            for t in state["tasks"]
            if t.result
        )

        state["metrics"] = SprintMetrics(
            total_tasks=total,
            completed_tasks=done,
            failed_tasks=failed,
            total_tokens=total_tokens,
        )

        await self.sprint_store.complete_sprint(state)
        await self._emit_status_change(state)
        return state

    async def _failed_node(self, state: SprintState) -> SprintState:
        """Handle sprint failure."""
        state["status"] = SprintStatus.FAILED
        await self.sprint_store.complete_sprint(state)
        await self._emit_status_change(state)
        return state

    def _route_after_plan(self, state: SprintState) -> str:
        """Route after planning."""
        if state.get("error"):
            return "failed"
        if not state.get("tasks"):
            state["error"] = "Planning produced no tasks"
            return "failed"
        return "execute"

    async def _emit_status_change(self, state: SprintState) -> None:
        """Emit a sprint status change event."""
        status = state["status"]
        status_val = status.value if hasattr(status, "value") else status
        await self.event_log.append(
            "sprint.status_changed",
            {"sprint_id": state["sprint_id"], "status": status_val},
        )

    async def _record_error(
        self, exc: Exception, task_id: str = "", sprint_id: str = "", agent_role: str = ""
    ) -> None:
        """Record an error via the error_store if available."""
        if not self.error_store:
            return
        try:
            import traceback as tb
            from foundrai.models.error_log import ErrorLog
            from foundrai.persistence.error_store import ErrorStore

            error = ErrorLog(
                task_id=task_id or None,
                sprint_id=sprint_id or None,
                agent_role=agent_role,
                error_type=ErrorStore.classify_error(exc),
                error_message=str(exc),
                traceback=tb.format_exc(),
            )
            await self.error_store.record_error(error)
        except Exception:
            pass

    async def _emit_task_status(self, task: Task) -> None:
        """Emit a task status change event and persist to DB."""
        status_val = task.status if isinstance(task.status, str) else task.status.value
        await self.event_log.append(
            "task.status_changed",
            {"task_id": task.id, "status": status_val, "task_title": task.title},
        )
        await self.sprint_store.update_task(task)
