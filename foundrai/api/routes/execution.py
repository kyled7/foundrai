"""Sprint execution endpoints — trigger SprintEngine from the web."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from foundrai.api.deps import get_config, get_db

router = APIRouter()
logger = logging.getLogger(__name__)

# Track running sprint tasks so we can report status / prevent double-execution.
_running_sprints: dict[str, asyncio.Task[Any]] = {}


class ExecuteRequest(BaseModel):
    goal: str | None = None  # optional override; defaults to sprint's stored goal


class ExecuteResponse(BaseModel):
    sprint_id: str
    status: str
    message: str


class SprintStatusResponse(BaseModel):
    sprint_id: str
    status: str
    running: bool


@router.post(
    "/sprints/{sprint_id}/execute",
    response_model=ExecuteResponse,
    status_code=202,
)
async def execute_sprint(sprint_id: str, body: ExecuteRequest | None = None) -> ExecuteResponse:
    """Trigger background execution of an existing sprint.

    The sprint must be in 'created' status. Returns immediately with 202 while
    the SprintEngine runs asynchronously. Progress is streamed via WebSocket.
    """
    if sprint_id in _running_sprints and not _running_sprints[sprint_id].done():
        raise HTTPException(status_code=409, detail="Sprint is already executing")

    db = await get_db()
    cursor = await db.conn.execute(
        "SELECT * FROM sprints WHERE sprint_id = ?", (sprint_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Sprint not found")

    if row["status"] not in ("created", "failed"):
        raise HTTPException(
            status_code=409,
            detail=f"Sprint is in '{row['status']}' state and cannot be executed",
        )

    goal = (body.goal if body and body.goal else row["goal"]) or ""
    project_id = row["project_id"]

    # Launch execution as a background asyncio task
    task = asyncio.create_task(
        _run_sprint_engine(sprint_id, project_id, goal),
        name=f"sprint-{sprint_id}",
    )
    _running_sprints[sprint_id] = task

    return ExecuteResponse(
        sprint_id=sprint_id,
        status="executing",
        message="Sprint execution started. Monitor via WebSocket.",
    )


@router.get("/sprints/{sprint_id}/execution-status", response_model=SprintStatusResponse)
async def get_execution_status(sprint_id: str) -> SprintStatusResponse:
    """Check whether a sprint's background execution is still running."""
    db = await get_db()
    cursor = await db.conn.execute(
        "SELECT status FROM sprints WHERE sprint_id = ?", (sprint_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Sprint not found")

    running = sprint_id in _running_sprints and not _running_sprints[sprint_id].done()
    return SprintStatusResponse(
        sprint_id=sprint_id,
        status=row["status"],
        running=running,
    )


@router.post("/sprints/{sprint_id}/cancel", response_model=ExecuteResponse)
async def cancel_sprint(sprint_id: str) -> ExecuteResponse:
    """Cancel a running sprint execution."""
    if sprint_id not in _running_sprints or _running_sprints[sprint_id].done():
        raise HTTPException(status_code=409, detail="Sprint is not currently executing")

    _running_sprints[sprint_id].cancel()
    del _running_sprints[sprint_id]

    db = await get_db()
    await db.conn.execute(
        "UPDATE sprints SET status = 'cancelled' WHERE sprint_id = ?",
        (sprint_id,),
    )
    await db.conn.commit()

    return ExecuteResponse(
        sprint_id=sprint_id,
        status="cancelled",
        message="Sprint execution cancelled.",
    )


# ---------------------------------------------------------------------------
# Async execution helper
# ---------------------------------------------------------------------------


async def _run_sprint_engine(sprint_id: str, project_id: str, goal: str) -> None:
    """Run the SprintEngine in the background.

    All events are emitted to EventLog → WebSocket automatically.
    """
    from foundrai.agents.context import SprintContext
    from foundrai.orchestration.agent_factory import create_agents
    from foundrai.orchestration.engine import SprintEngine
    from foundrai.orchestration.message_bus import MessageBus
    from foundrai.orchestration.task_graph import TaskGraph
    from foundrai.persistence.artifact_store import ArtifactStore
    from foundrai.persistence.event_log import EventLog
    from foundrai.persistence.sprint_store import SprintStore

    try:
        db = await get_db()
        config = get_config()

        event_log = EventLog(db)
        sprint_store = SprintStore(db)
        artifact_store = ArtifactStore(db)
        message_bus = MessageBus(event_log)
        task_graph = TaskGraph()

        # Import the WebSocket broadcaster so engine events go to clients
        from foundrai.api.app import ws_manager

        async def _broadcast(event_type: str, data: dict) -> None:
            await ws_manager.broadcast_all(event_type, data)

        event_log.register_listener(_broadcast)

        sprint_context = SprintContext(
            project_name=config.project.name,
            project_path=".",
            sprint_goal=goal,
            sprint_number=await sprint_store.next_sprint_number(project_id),
        )

        # Optional stores (may not be available)
        token_store = None
        trace_store = None
        error_store = None
        try:
            from foundrai.persistence.token_store import TokenStore
            token_store = TokenStore(db)
        except Exception:
            pass
        try:
            from foundrai.persistence.trace_store import TraceStore
            trace_store = TraceStore(db)
        except Exception:
            pass
        try:
            from foundrai.persistence.error_store import ErrorStore
            error_store = ErrorStore(db)
        except Exception:
            pass

        agents = create_agents(
            config=config,
            sprint_context=sprint_context,
            message_bus=message_bus,
            event_log=event_log,
            token_store=token_store,
            trace_store=trace_store,
            sprint_id=sprint_id,
            project_id=project_id,
        )

        engine = SprintEngine(
            config=config,
            agents=agents,
            task_graph=task_graph,
            message_bus=message_bus,
            sprint_store=sprint_store,
            event_log=event_log,
            artifact_store=artifact_store,
            error_store=error_store,
            db=db,
        )

        # The engine creates its own sprint record, but we already have one
        # from the create_sprint endpoint. Delete the duplicate before running,
        # or patch the engine to use the existing sprint_id.
        # Approach: update existing sprint status to "planning" and let the
        # engine work with it. We override run_sprint to reuse the sprint_id.
        await db.conn.execute(
            "UPDATE sprints SET status = 'planning' WHERE sprint_id = ?",
            (sprint_id,),
        )
        await db.conn.commit()

        await event_log.append("sprint.started", {
            "sprint_id": sprint_id,
            "goal": goal,
        })

        # Build initial state matching what the engine expects
        from foundrai.models.enums import SprintStatus
        from foundrai.models.sprint import SprintMetrics, SprintState

        state: SprintState = {
            "project_id": project_id,
            "sprint_id": sprint_id,
            "sprint_number": sprint_context.sprint_number,
            "goal": goal,
            "status": SprintStatus.PLANNING,
            "tasks": [],
            "messages": [],
            "artifacts": [],
            "metrics": SprintMetrics(),
            "error": None,
        }

        # Run the engine phases manually (reusing existing sprint_id)
        state = await engine._plan_node(state)
        route = engine._route_after_plan(state)
        if route == "failed":
            state = await engine._failed_node(state)
        else:
            state = await engine._execute_node(state)
            state = await engine._review_node(state)
            state = await engine._retrospective_node(state)
            state = await engine._complete_node(state)

        logger.info("Sprint %s completed with status: %s", sprint_id, state["status"])

    except asyncio.CancelledError:
        logger.info("Sprint %s execution was cancelled", sprint_id)
    except Exception:
        logger.exception("Sprint %s execution failed", sprint_id)
        try:
            db = await get_db()
            await db.conn.execute(
                "UPDATE sprints SET status = 'failed' WHERE sprint_id = ?",
                (sprint_id,),
            )
            await db.conn.commit()
        except Exception:
            pass
    finally:
        _running_sprints.pop(sprint_id, None)
