"""Tests for MessageBus."""

import pytest

from foundrai.models.enums import MessageType
from foundrai.models.message import AgentMessage
from foundrai.orchestration.message_bus import MessageBus
from foundrai.persistence.event_log import EventLog


@pytest.fixture
def event_log(db):
    return EventLog(db)


@pytest.mark.asyncio
async def test_direct_message(db):
    event_log = EventLog(db)
    bus = MessageBus(event_log)
    bus.register_agent("agent_a")
    bus.register_agent("agent_b")

    msg = AgentMessage(
        type=MessageType.QUESTION,
        from_agent="agent_a",
        to_agent="agent_b",
        content="hello",
    )
    await bus.publish(msg)

    msgs = await bus.consume("agent_b")
    assert len(msgs) == 1
    assert msgs[0].content == "hello"

    # Sender should NOT receive their own message
    msgs_a = await bus.consume("agent_a")
    assert len(msgs_a) == 0


@pytest.mark.asyncio
async def test_broadcast(db):
    event_log = EventLog(db)
    bus = MessageBus(event_log)
    bus.register_agent("a")
    bus.register_agent("b")
    bus.register_agent("c")

    msg = AgentMessage(
        type=MessageType.STATUS_UPDATE,
        from_agent="a",
        to_agent=None,
        content="done",
    )
    await bus.publish(msg)

    assert len(await bus.consume("b")) == 1
    assert len(await bus.consume("c")) == 1
    assert len(await bus.consume("a")) == 0  # Sender excluded


@pytest.mark.asyncio
async def test_get_history(db):
    event_log = EventLog(db)
    bus = MessageBus(event_log)
    bus.register_agent("a")

    msg1 = AgentMessage(type=MessageType.QUESTION, from_agent="a", content="first")
    msg2 = AgentMessage(type=MessageType.DECISION, from_agent="a", content="second")
    await bus.publish(msg1)
    await bus.publish(msg2)

    history = bus.get_history()
    assert len(history) == 2


@pytest.mark.asyncio
async def test_listener_callback(db):
    event_log = EventLog(db)
    bus = MessageBus(event_log)
    bus.register_agent("a")

    received = []

    async def listener(msg: AgentMessage) -> None:
        received.append(msg)

    bus.register_listener(listener)

    msg = AgentMessage(type=MessageType.QUESTION, from_agent="a", content="test")
    await bus.publish(msg)

    assert len(received) == 1
    assert received[0].content == "test"
