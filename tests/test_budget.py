"""Tests for BudgetManager."""

from __future__ import annotations

import pytest
import pytest_asyncio

from foundrai.models.budget import BudgetConfig
from foundrai.models.token_usage import TokenUsage
from foundrai.orchestration.budget_manager import BudgetManager
from foundrai.persistence.database import Database
from foundrai.persistence.event_log import EventLog
from foundrai.persistence.token_store import TokenStore


@pytest_asyncio.fixture
async def budget_setup(db: Database):
    token_store = TokenStore(db)
    event_log = EventLog(db)
    config = BudgetConfig(
        sprint_budget_usd=1.0,
        agent_budgets={"developer": 0.5, "qa_engineer": 0.3},
    )
    manager = BudgetManager(config, token_store, db, event_log)
    return manager, token_store


@pytest.mark.asyncio
async def test_check_budget_no_spending(budget_setup) -> None:
    mgr, _ = budget_setup
    status = await mgr.check_budget("sprint-1")
    assert status.budget_usd == 1.0
    assert status.spent_usd == 0.0
    assert not status.is_warning
    assert not status.is_exceeded


@pytest.mark.asyncio
async def test_check_budget_warning(budget_setup) -> None:
    mgr, store = budget_setup
    await store.record_usage(TokenUsage(
        sprint_id="sprint-1", project_id="p1", agent_role="developer",
        model="gpt-4", cost_usd=0.85, total_tokens=1000,
    ))
    status = await mgr.check_budget("sprint-1")
    assert status.is_warning
    assert not status.is_exceeded


@pytest.mark.asyncio
async def test_check_budget_exceeded(budget_setup) -> None:
    mgr, store = budget_setup
    await store.record_usage(TokenUsage(
        sprint_id="sprint-1", project_id="p1", agent_role="developer",
        model="gpt-4", cost_usd=1.10, total_tokens=1000,
    ))
    status = await mgr.check_budget("sprint-1")
    assert status.is_exceeded


@pytest.mark.asyncio
async def test_enforce_budget_allows(budget_setup) -> None:
    mgr, _ = budget_setup
    assert await mgr.enforce_budget("sprint-1") is True


@pytest.mark.asyncio
async def test_enforce_budget_blocks(budget_setup) -> None:
    mgr, store = budget_setup
    await store.record_usage(TokenUsage(
        sprint_id="sprint-1", project_id="p1", agent_role="developer",
        model="gpt-4", cost_usd=1.50, total_tokens=1000,
    ))
    assert await mgr.enforce_budget("sprint-1") is False


@pytest.mark.asyncio
async def test_agent_budget(budget_setup) -> None:
    mgr, store = budget_setup
    await store.record_usage(TokenUsage(
        sprint_id="sprint-1", project_id="p1", agent_role="developer",
        model="gpt-4", cost_usd=0.45, total_tokens=1000,
    ))
    status = await mgr.check_budget("sprint-1", "developer")
    assert status.is_warning  # 90% of 0.5


@pytest.mark.asyncio
async def test_budget_override(budget_setup) -> None:
    mgr, store = budget_setup
    await mgr.set_override("sprint-1", 10.0)
    await store.record_usage(TokenUsage(
        sprint_id="sprint-1", project_id="p1", agent_role="developer",
        model="gpt-4", cost_usd=1.50, total_tokens=1000,
    ))
    status = await mgr.check_budget("sprint-1")
    assert not status.is_exceeded  # 1.50 < 10.0


@pytest.mark.asyncio
async def test_unlimited_budget() -> None:
    """Zero budget means unlimited."""
    from foundrai.persistence.database import Database
    import tempfile, os
    db = Database(os.path.join(tempfile.mkdtemp(), "test.db"))
    await db.connect()
    try:
        store = TokenStore(db)
        event_log = EventLog(db)
        config = BudgetConfig(sprint_budget_usd=0.0)
        mgr = BudgetManager(config, store, db, event_log)
        status = await mgr.check_budget("sprint-1")
        assert not status.is_exceeded
        assert not status.is_warning
        assert await mgr.enforce_budget("sprint-1") is True
    finally:
        await db.close()
