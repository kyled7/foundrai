"""Decision trace API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from foundrai.api.deps import get_db
from foundrai.persistence.trace_store import TraceStore

router = APIRouter()


async def _get_trace_store() -> TraceStore:
    db = await get_db()
    return TraceStore(db)


@router.get("/tasks/{task_id}/traces")
async def get_task_traces(task_id: str) -> dict:
    """Get all decision traces for a task."""
    store = await _get_trace_store()
    traces = await store.get_task_traces(task_id)
    return {
        "traces": [_trace_summary(t) for t in traces],
        "total": len(traces),
    }


@router.get("/sprints/{sprint_id}/traces")
async def get_sprint_traces(sprint_id: str, limit: int = 50) -> dict:
    """Get decision traces for a sprint."""
    store = await _get_trace_store()
    traces = await store.get_sprint_traces(sprint_id, limit=limit)
    return {
        "traces": [_trace_summary(t) for t in traces],
        "total": len(traces),
    }


@router.get("/traces/{trace_id}")
async def get_trace(trace_id: int) -> dict:
    """Get a single trace with full decompressed prompt/response."""
    store = await _get_trace_store()
    trace = await store.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return {
        "trace_id": trace.trace_id,
        "event_id": trace.event_id,
        "task_id": trace.task_id,
        "sprint_id": trace.sprint_id,
        "agent_role": trace.agent_role,
        "model": trace.model,
        "prompt": trace.prompt,
        "response": trace.response,
        "thinking": trace.thinking,
        "tool_calls": trace.tool_calls,
        "tokens_used": trace.tokens_used,
        "cost_usd": trace.cost_usd,
        "duration_ms": trace.duration_ms,
        "timestamp": trace.timestamp,
    }


def _trace_summary(t: Any) -> dict:
    """Return a trace without full prompt/response (for list views)."""
    return {
        "trace_id": t.trace_id,
        "event_id": t.event_id,
        "task_id": t.task_id,
        "sprint_id": t.sprint_id,
        "agent_role": t.agent_role,
        "model": t.model,
        "tokens_used": t.tokens_used,
        "cost_usd": t.cost_usd,
        "duration_ms": t.duration_ms,
        "thinking": t.thinking[:200] if t.thinking else None,
        "timestamp": t.timestamp,
    }
