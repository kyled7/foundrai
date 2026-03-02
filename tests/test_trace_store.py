"""Tests for TraceStore."""

from __future__ import annotations

import pytest
import pytest_asyncio

from foundrai.models.decision_trace import DecisionTrace
from foundrai.persistence.database import Database
from foundrai.persistence.trace_store import TraceStore


@pytest_asyncio.fixture
async def trace_store(db: Database) -> TraceStore:
    return TraceStore(db)


@pytest.mark.asyncio
async def test_record_and_get_trace(trace_store: TraceStore) -> None:
    trace = DecisionTrace(
        task_id="task-1",
        sprint_id="sprint-1",
        agent_role="developer",
        model="gpt-4",
        prompt="What is 2+2?",
        response="4",
        thinking="Let me calculate...",
        tool_calls=[{"name": "calculator", "args": {"expr": "2+2"}}],
        tokens_used=100,
        cost_usd=0.01,
        duration_ms=500,
    )
    trace_id = await trace_store.record_trace(trace)
    assert trace_id > 0

    fetched = await trace_store.get_trace(trace_id)
    assert fetched is not None
    assert fetched.prompt == "What is 2+2?"
    assert fetched.response == "4"
    assert fetched.thinking == "Let me calculate..."
    assert fetched.tool_calls == [{"name": "calculator", "args": {"expr": "2+2"}}]
    assert fetched.tokens_used == 100
    assert fetched.cost_usd == 0.01
    assert fetched.duration_ms == 500


@pytest.mark.asyncio
async def test_get_task_traces(trace_store: TraceStore) -> None:
    for i in range(3):
        await trace_store.record_trace(DecisionTrace(
            task_id="task-1", sprint_id="sprint-1", agent_role="developer",
            prompt=f"prompt {i}", response=f"response {i}",
        ))
    await trace_store.record_trace(DecisionTrace(
        task_id="task-2", sprint_id="sprint-1", agent_role="developer",
        prompt="other", response="other",
    ))

    traces = await trace_store.get_task_traces("task-1")
    assert len(traces) == 3


@pytest.mark.asyncio
async def test_get_sprint_traces(trace_store: TraceStore) -> None:
    for i in range(5):
        await trace_store.record_trace(DecisionTrace(
            task_id=f"task-{i}", sprint_id="sprint-1", agent_role="developer",
            prompt=f"p{i}", response=f"r{i}",
        ))

    traces = await trace_store.get_sprint_traces("sprint-1", limit=3)
    assert len(traces) == 3


@pytest.mark.asyncio
async def test_get_nonexistent_trace(trace_store: TraceStore) -> None:
    result = await trace_store.get_trace(99999)
    assert result is None


@pytest.mark.asyncio
async def test_compression_roundtrip(trace_store: TraceStore) -> None:
    long_prompt = "x" * 10000
    long_response = "y" * 10000
    trace_id = await trace_store.record_trace(DecisionTrace(
        agent_role="developer", prompt=long_prompt, response=long_response,
    ))
    fetched = await trace_store.get_trace(trace_id)
    assert fetched is not None
    assert fetched.prompt == long_prompt
    assert fetched.response == long_response
