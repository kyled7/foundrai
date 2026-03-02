"""Tests for ErrorStore."""

from __future__ import annotations

import pytest
import pytest_asyncio

from foundrai.models.error_log import ErrorLog
from foundrai.persistence.database import Database
from foundrai.persistence.error_store import ErrorStore


@pytest_asyncio.fixture
async def error_store(db: Database) -> ErrorStore:
    return ErrorStore(db)


@pytest.mark.asyncio
async def test_record_and_get_errors(error_store: ErrorStore) -> None:
    error = ErrorLog(
        task_id="task-1",
        sprint_id="sprint-1",
        agent_role="developer",
        error_type="timeout",
        error_message="Request timed out after 30s",
        traceback="Traceback ...",
        suggested_fix="Increase timeout or reduce prompt size",
    )
    error_id = await error_store.record_error(error)
    assert error_id > 0

    errors = await error_store.get_task_errors("task-1")
    assert len(errors) == 1
    assert errors[0].error_type == "timeout"
    assert errors[0].error_message == "Request timed out after 30s"


@pytest.mark.asyncio
async def test_get_sprint_errors(error_store: ErrorStore) -> None:
    for i in range(3):
        await error_store.record_error(ErrorLog(
            task_id=f"task-{i}", sprint_id="sprint-1", agent_role="developer",
            error_type="unknown", error_message=f"error {i}",
        ))
    await error_store.record_error(ErrorLog(
        task_id="task-x", sprint_id="sprint-2", agent_role="developer",
        error_type="unknown", error_message="other",
    ))

    errors = await error_store.get_sprint_errors("sprint-1")
    assert len(errors) == 3


@pytest.mark.asyncio
async def test_classify_error() -> None:
    assert ErrorStore.classify_error(Exception("rate limit exceeded")) == "rate_limit"
    assert ErrorStore.classify_error(Exception("429 too many requests")) == "rate_limit"
    assert ErrorStore.classify_error(Exception("context token limit exceeded")) == "context_overflow"
    assert ErrorStore.classify_error(TimeoutError("timed out")) == "timeout"
    assert ErrorStore.classify_error(Exception("json decode error")) == "parse_error"
    assert ErrorStore.classify_error(Exception("something random")) == "unknown"
