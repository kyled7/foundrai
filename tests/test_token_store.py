"""Tests for TokenStore."""

from __future__ import annotations

import pytest
import pytest_asyncio

from foundrai.models.token_usage import TokenUsage
from foundrai.persistence.database import Database
from foundrai.persistence.token_store import TokenStore


@pytest_asyncio.fixture
async def token_store(db: Database) -> TokenStore:
    return TokenStore(db)


def _make_usage(**kwargs) -> TokenUsage:
    defaults = {
        "task_id": "task-1",
        "sprint_id": "sprint-1",
        "project_id": "proj-1",
        "agent_role": "developer",
        "model": "gpt-4",
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150,
        "cost_usd": 0.01,
    }
    defaults.update(kwargs)
    return TokenUsage(**defaults)


@pytest.mark.asyncio
async def test_record_and_get_task_usage(token_store: TokenStore) -> None:
    usage = _make_usage()
    usage_id = await token_store.record_usage(usage)
    assert usage_id > 0

    records = await token_store.get_task_usage("task-1")
    assert len(records) == 1
    assert records[0].agent_role == "developer"
    assert records[0].total_tokens == 150


@pytest.mark.asyncio
async def test_get_sprint_usage(token_store: TokenStore) -> None:
    await token_store.record_usage(_make_usage(agent_role="developer", cost_usd=0.05))
    await token_store.record_usage(_make_usage(agent_role="qa_engineer", cost_usd=0.03))

    result = await token_store.get_sprint_usage("sprint-1")
    assert result["total_cost"] == pytest.approx(0.08)
    assert result["call_count"] == 2
    assert "developer" in result["by_agent"]
    assert "qa_engineer" in result["by_agent"]


@pytest.mark.asyncio
async def test_get_project_usage(token_store: TokenStore) -> None:
    await token_store.record_usage(_make_usage(sprint_id="s1", cost_usd=0.02))
    await token_store.record_usage(_make_usage(sprint_id="s2", cost_usd=0.03))

    result = await token_store.get_project_usage("proj-1")
    assert result["total_cost"] == pytest.approx(0.05)
    assert "s1" in result["by_sprint"]
    assert "s2" in result["by_sprint"]


@pytest.mark.asyncio
async def test_get_agent_usage(token_store: TokenStore) -> None:
    await token_store.record_usage(_make_usage())
    result = await token_store.get_agent_usage("proj-1", "developer")
    assert result["total_tokens"] == 150
    assert result["call_count"] == 1


@pytest.mark.asyncio
async def test_get_sprint_spent(token_store: TokenStore) -> None:
    await token_store.record_usage(_make_usage(cost_usd=0.1))
    await token_store.record_usage(_make_usage(cost_usd=0.2))
    spent = await token_store.get_sprint_spent("sprint-1")
    assert spent == pytest.approx(0.3)
