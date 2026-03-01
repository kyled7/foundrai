"""Tests for EventLog."""

import pytest

from foundrai.persistence.event_log import EventLog


@pytest.mark.asyncio
async def test_append_event(db):
    log = EventLog(db)
    event_id = await log.append("test.event", {"key": "value"})
    assert event_id is not None
    assert event_id > 0


@pytest.mark.asyncio
async def test_query_events(db):
    log = EventLog(db)
    await log.append("type_a", {"data": 1})
    await log.append("type_b", {"data": 2})
    await log.append("type_a", {"data": 3})

    all_events = await log.query()
    assert len(all_events) == 3

    type_a = await log.query(event_type="type_a")
    assert len(type_a) == 2


@pytest.mark.asyncio
async def test_event_listener(db):
    log = EventLog(db)
    received = []

    async def listener(event_type: str, data: dict) -> None:
        received.append((event_type, data))

    log.register_listener(listener)
    await log.append("test.event", {"key": "value"})

    assert len(received) == 1
    assert received[0][0] == "test.event"
