"""SprintEngine — orchestrates the sprint lifecycle with approval gates."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from foundrai.config import FoundrAIConfig
from foundrai.models.enums import AgentRoleName, AutonomyLevel, SprintStatus, TaskStatus
from foundrai.models.sprint import SprintMetrics, SprintState
from foundrai.models.task import Task
from foundrai.orchestration.ceremonies import SprintRetrospective, SprintReview
from foundrai.orchestration.message_bus import MessageBus
from foundrai.orchestration.task_graph import TaskGraph
from foundrai.persistence.artifact_store import ArtifactStore
from foundrai.persistence.event_log import EventLog
from foundrai.persistence.sprint_store import SprintStore
from foundrai.utils.retry import retry_async

logger = logging.getLogger(__name__)

# How long to wait for a human approval decision (seconds)
APPROVAL_TIMEOUT = 300  # 5 minutes
APPROVAL_POLL_INTERVAL = 2  # Check every 2 seconds


class SprintEngine:
    """Orchestrates the sprint lifecycle with approval gates and multi-sprint support."""

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
        db: Any | None = None,
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
        self.db = db
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

    async def run_multi_sprint(
        self, goal: str, project_id: str, max_sprints: int | None = None
    ) -> list[SprintState]:
        """Run multiple sprints iteratively until the goal is achieved or max reached.

        Each sprint after the first refines remaining work based on the previous
        sprint's results and retrospective learnings.
        """
        max_sprints = max_sprints or self.config.sprint.max_sprints
        sprint_results: list[SprintState] = []

        remaining_goal = goal

        for sprint_num in range(max_sprints):
            logger.info(
                "Starting sprint %d/%d for goal: %s",
                sprint_num + 1, max_sprints, remaining_goal[:100],
            )

            state = await self.run_sprint(remaining_goal, project_id)
            sprint_results.append(state)

            # Check if all tasks completed successfully
            tasks = state.get("tasks", [])
            done = sum(1 for t in tasks if t.status in (TaskStatus.DONE, "done"))
            failed = sum(1 for t in tasks if t.status in (TaskStatus.FAILED, "failed"))
            total = len(tasks)

            if failed == 0 and done == total and total > 0:
                logger.info("All tasks completed in sprint %d. Goal achieved.", sprint_num + 1)
                await self.event_log.append("multi_sprint.goal_achieved", {
                    "project_id": project_id,
                    "sprints_used": sprint_num + 1,
                    "goal": goal,
                })
                break

            # Check if auto_start_next is disabled
            if not self.config.sprint.auto_start_next:
                logger.info("auto_start_next disabled. Stopping after sprint %d.", sprint_num + 1)
                break

            # Build refined goal for next sprint from failed/incomplete tasks
            failed_tasks = [t for t in tasks if t.status in (TaskStatus.FAILED, "failed")]
            if not failed_tasks:
                logger.info("No failed tasks to retry. Stopping.")
                break

            failed_descriptions = "\n".join(
                f"- {t.title}: {t.description}" for t in failed_tasks
            )
            remaining_goal = (
                f"Continue working on the original goal: {goal}\n\n"
                f"The following tasks from the previous sprint need to be completed:\n"
                f"{failed_descriptions}"
            )

            await self.event_log.append("multi_sprint.continuing", {
                "project_id": project_id,
                "sprint_number": sprint_num + 1,
                "failed_tasks": len(failed_tasks),
                "remaining_goal": remaining_goal[:500],
            })

            # Reset task graph for next sprint
            self.task_graph.reset()

        return sprint_results

    async def resume_sprint(self, checkpoint_id: str) -> SprintState:
        """Resume a sprint from a specific checkpoint.

        Loads the specified checkpoint and continues execution from the phase
        immediately following that checkpoint.

        Args:
            checkpoint_id: The ID of the checkpoint to resume from

        Returns:
            The final sprint state after completion

        Raises:
            ValueError: If checkpoint cannot be found or loaded
        """
        # Get the checkpoint name and sprint_id for routing
        cursor = await self.sprint_store.db.conn.execute(
            "SELECT checkpoint_name, sprint_id FROM checkpoints WHERE checkpoint_id = ?",
            (checkpoint_id,),
        )
        row = await cursor.fetchone()
        if not row:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")

        checkpoint_name = row["checkpoint_name"]
        sprint_id = row["sprint_id"]

        logger.info(
            "Resuming sprint %s from checkpoint %s (%s)",
            sprint_id, checkpoint_id, checkpoint_name,
        )

        # Load the state
        state = await self.sprint_store.load_checkpoint(checkpoint_id)
        if not state:
            raise ValueError(f"Failed to load checkpoint {checkpoint_id}")

        await self.event_log.append("sprint.resumed", {
            "sprint_id": sprint_id,
            "checkpoint_name": checkpoint_name,
            "checkpoint_id": checkpoint_id,
        })

        # Resume from the appropriate phase based on checkpoint name
        if checkpoint_name == "after_planning":
            # Resume from execution
            state = await self._execute_node(state)
            state = await self._review_node(state)
            state = await self._retrospective_node(state)
            state = await self._complete_node(state)
        elif checkpoint_name == "after_execution":
            # Resume from review
            state = await self._review_node(state)
            state = await self._retrospective_node(state)
            state = await self._complete_node(state)
        elif checkpoint_name == "after_review":
            # Resume from retrospective
            state = await self._retrospective_node(state)
            state = await self._complete_node(state)
        elif checkpoint_name == "after_retrospective":
            # Just complete
            state = await self._complete_node(state)
        else:
            raise ValueError(f"Unknown checkpoint name: {checkpoint_name}")

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

        # Create checkpoint after planning
        await self.sprint_store.save_checkpoint(
            state["sprint_id"], "after_planning", state
        )

        return state

    async def _execute_node(self, state: SprintState) -> SprintState:
        """EXECUTING node: Execute tasks (parallel where deps allow) with approval gates."""
        state["status"] = SprintStatus.EXECUTING
        await self._emit_status_change(state)

        max_parallel = self.config.sprint.max_tasks_parallel

        # Execute in waves based on dependency graph
        while True:
            ready = self.task_graph.get_ready_tasks()
            if not ready:
                break

            # Categorize tasks by assigned agent
            executable_tasks = []
            for t in ready:
                assigned = t.assigned_to
                if isinstance(assigned, AgentRoleName):
                    assigned = assigned.value
                agent = self.agents.get(assigned or "developer")
                if agent:
                    executable_tasks.append((t, agent, assigned or "developer"))
                else:
                    # No agent available for this role — mark as failed
                    t.status = TaskStatus.FAILED
                    self.task_graph.mark_completed(t.id)
                    await self._emit_task_status(t)

            if not executable_tasks:
                if not ready:
                    break
                continue

            # Execute batch with concurrency limit
            sem = asyncio.Semaphore(max_parallel)

            async def execute_one(task: Task, agent: Any, role_name: str) -> None:
                async with sem:
                    # --- Approval gate ---
                    approved = await self._check_approval_gate(
                        task, role_name, state["sprint_id"]
                    )
                    if not approved:
                        task.status = TaskStatus.BLOCKED
                        self.task_graph.mark_completed(task.id)
                        await self._emit_task_status(task)
                        return

                    task.status = TaskStatus.IN_PROGRESS
                    await self._emit_task_status(task)

                    try:
                        # Determine timeout: use task-specific or fall back to config default
                        timeout = task.timeout_seconds or self.config.sprint.task_timeout_seconds

                        # Wrap task execution with retry logic and timeout enforcement
                        max_retries = self.config.sprint.max_task_retries

                        async def execute_with_timeout() -> Any:
                            """Execute task with timeout enforcement."""
                            return await asyncio.wait_for(
                                retry_async(
                                    fn=lambda: agent.execute_task(task),
                                    max_retries=max_retries,
                                    backoff_base=1.0,
                                    retryable_exceptions=(Exception,),
                                    auto_classify_retryable=True,
                                ),
                                timeout=timeout,
                            )

                        result = await execute_with_timeout()
                        task.result = result
                        task.status = TaskStatus.IN_REVIEW if result.success else TaskStatus.FAILED

                        for artifact in result.artifacts:
                            await self.artifact_store.save(artifact)
                            state["artifacts"].append(artifact)
                    except asyncio.TimeoutError:
                        # Task execution timed out
                        task.status = TaskStatus.FAILED
                        logger.warning(
                            "Task %s timed out after %s seconds in sprint %s",
                            task.id, timeout, state["sprint_id"],
                        )
                        await self.event_log.append("task.timeout", {
                            "task_id": task.id,
                            "sprint_id": state["sprint_id"],
                            "timeout_seconds": timeout,
                            "task_title": task.title,
                        })
                    except Exception as exc:
                        task.status = TaskStatus.FAILED
                        await self._record_error(
                            exc, task_id=task.id,
                            sprint_id=state["sprint_id"],
                            agent_role=role_name,
                        )

                    self.task_graph.mark_completed(task.id)
                    await self._emit_task_status(task)

            await asyncio.gather(
                *[execute_one(t, agent, role) for t, agent, role in executable_tasks],
                return_exceptions=True,
            )

        # Create checkpoint after execution
        await self.sprint_store.save_checkpoint(
            state["sprint_id"], "after_execution", state
        )

        return state

    async def _check_approval_gate(
        self, task: Task, agent_role: str, sprint_id: str
    ) -> bool:
        """Check if this task/agent requires human approval before execution.

        Returns True if approved (or no approval needed), False if rejected/timed out.
        """
        # Look up autonomy level from config
        autonomy = self._get_agent_autonomy(agent_role)

        if autonomy in (AutonomyLevel.AUTO_APPROVE, AutonomyLevel.NOTIFY):
            # Auto-approve or just notify (no blocking)
            if autonomy == AutonomyLevel.NOTIFY:
                await self.event_log.append("approval.notify", {
                    "sprint_id": sprint_id,
                    "task_id": task.id,
                    "agent_role": agent_role,
                    "task_title": task.title,
                    "message": f"Agent '{agent_role}' is starting task: {task.title}",
                })
            return True

        if autonomy == AutonomyLevel.BLOCK:
            await self.event_log.append("approval.blocked", {
                "sprint_id": sprint_id,
                "task_id": task.id,
                "agent_role": agent_role,
                "task_title": task.title,
            })
            return False

        # REQUIRE_APPROVAL — create approval request and wait
        if not self.db:
            # No DB means we can't persist approvals — auto-approve as fallback
            return True

        approval_id = str(uuid.uuid4())
        await self.db.conn.execute(
            """INSERT INTO approvals
               (approval_id, sprint_id, task_id, agent_id, action_type, title, description, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')""",
            (
                approval_id, sprint_id, task.id, agent_role,
                "task_execution", task.title, task.description,
            ),
        )
        await self.db.conn.commit()

        await self.event_log.append("approval.requested", {
            "approval_id": approval_id,
            "sprint_id": sprint_id,
            "task_id": task.id,
            "agent_role": agent_role,
            "action_type": "task_execution",
            "task_title": task.title,
        })

        # Poll for approval decision
        elapsed = 0.0
        while elapsed < APPROVAL_TIMEOUT:
            await asyncio.sleep(APPROVAL_POLL_INTERVAL)
            elapsed += APPROVAL_POLL_INTERVAL

            cursor = await self.db.conn.execute(
                "SELECT status FROM approvals WHERE approval_id = ?",
                (approval_id,),
            )
            row = await cursor.fetchone()
            if row and row["status"] == "approved":
                await self.event_log.append("approval.approved", {
                    "approval_id": approval_id,
                    "sprint_id": sprint_id,
                    "task_id": task.id,
                })
                return True
            if row and row["status"] == "rejected":
                await self.event_log.append("approval.rejected", {
                    "approval_id": approval_id,
                    "sprint_id": sprint_id,
                    "task_id": task.id,
                })
                return False

        # Timed out
        await self.db.conn.execute(
            "UPDATE approvals SET status = 'expired' WHERE approval_id = ?",
            (approval_id,),
        )
        await self.db.conn.commit()
        await self.event_log.append("approval.expired", {
            "approval_id": approval_id,
            "sprint_id": sprint_id,
            "task_id": task.id,
        })
        return False

    def _get_agent_autonomy(self, agent_role: str) -> AutonomyLevel:
        """Get the autonomy level for an agent role from config."""
        agent_config = getattr(self.config.team, agent_role, None)
        if agent_config and hasattr(agent_config, "autonomy"):
            return agent_config.autonomy
        return AutonomyLevel.NOTIFY

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
                await self._record_error(
                    exc, task_id=task.id,
                    sprint_id=state["sprint_id"], agent_role="qa_engineer",
                )

            await self._emit_task_status(task)

        # Create checkpoint after review
        await self.sprint_store.save_checkpoint(
            state["sprint_id"], "after_review", state
        )

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

        # Create checkpoint after retrospective
        await self.sprint_store.save_checkpoint(
            state["sprint_id"], "after_retrospective", state
        )

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
