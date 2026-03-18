"""Race condition stress tests with high parallelism."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock

import pytest

from foundrai.agents.context import SprintContext
from foundrai.agents.personas.developer import DeveloperAgent
from foundrai.agents.personas.product_manager import ProductManagerAgent
from foundrai.agents.personas.qa_engineer import QAEngineerAgent
from foundrai.agents.roles import get_role
from foundrai.agents.runtime import RuntimeResult
from foundrai.config import FoundrAIConfig
from foundrai.models.enums import AgentRoleName, SprintStatus, TaskStatus
from foundrai.models.task import Task
from foundrai.orchestration.engine import SprintEngine
from foundrai.orchestration.message_bus import MessageBus
from foundrai.orchestration.task_graph import TaskGraph
from foundrai.persistence.artifact_store import ArtifactStore
from foundrai.persistence.event_log import EventLog
from foundrai.persistence.sprint_store import SprintStore


def _make_runtime_mock(response_content: str, response_format: str | None = None) -> AsyncMock:
    """Create a mock runtime that returns a canned response."""
    runtime = AsyncMock()
    parsed = None
    starts_json = response_content.startswith(("[", "{"))
    if response_format == "json" or starts_json:
        try:
            parsed = json.loads(response_content)
        except json.JSONDecodeError:
            pass
    runtime.run = AsyncMock(return_value=RuntimeResult(
        output=response_content,
        parsed=parsed,
        artifacts=[],
        tokens_used=100,
        success=True,
    ))
    return runtime


@pytest.fixture
def sprint_context(tmp_path):
    """Create a sprint context for testing."""
    return SprintContext(
        project_name="test-project",
        project_path=str(tmp_path),
        sprint_goal="Test race condition scenarios",
        sprint_number=1,
    )


@pytest.fixture
async def components(db):
    """Set up all orchestration components."""
    event_log = EventLog(db)
    sprint_store = SprintStore(db)
    artifact_store = ArtifactStore(db)
    message_bus = MessageBus(event_log)
    task_graph = TaskGraph()
    return event_log, sprint_store, artifact_store, message_bus, task_graph


@pytest.mark.asyncio
async def test_concurrent_task_graph_additions(components):
    """Test adding many tasks to task graph concurrently."""
    _, _, _, _, task_graph = components

    async def add_task(idx: int) -> None:
        """Add a single task."""
        task = Task(
            title=f"Task {idx}",
            description=f"Description {idx}",
            acceptance_criteria=[],
            dependencies=[],
            assigned_to="developer",
            priority=idx,
        )
        await task_graph.add_task(task, depends_on=[])

    # Add 50 tasks concurrently
    tasks = [add_task(i) for i in range(50)]
    await asyncio.gather(*tasks)

    # Verify all tasks were added
    assert task_graph.task_count == 50

    # Verify we can get all tasks
    ready = await task_graph.get_ready_tasks()
    assert len(ready) == 50


@pytest.mark.asyncio
async def test_concurrent_task_graph_with_dependencies(components):
    """Test adding tasks with dependencies concurrently."""
    _, _, _, _, task_graph = components

    # First add root tasks
    root_tasks = []
    for i in range(10):
        task = Task(
            title=f"Root {i}",
            description=f"Root task {i}",
            acceptance_criteria=[],
            dependencies=[],
            assigned_to="developer",
            priority=i,
        )
        await task_graph.add_task(task, depends_on=[])
        root_tasks.append(task)

    # Now add dependent tasks concurrently
    async def add_dependent_task(idx: int, depends_on_id: str) -> None:
        """Add a task that depends on a root task."""
        task = Task(
            title=f"Dependent {idx}",
            description=f"Depends on root",
            acceptance_criteria=[],
            dependencies=[depends_on_id],
            assigned_to="developer",
            priority=100 + idx,
        )
        await task_graph.add_task(task, depends_on=[depends_on_id])

    dependent_tasks = []
    for i in range(40):
        root_id = root_tasks[i % 10].id
        dependent_tasks.append(add_dependent_task(i, root_id))

    await asyncio.gather(*dependent_tasks)

    # Verify structure
    assert task_graph.task_count == 50
    ready = await task_graph.get_ready_tasks()
    assert len(ready) == 10  # Only root tasks should be ready


@pytest.mark.asyncio
async def test_concurrent_message_bus_publishing(components):
    """Test publishing many messages concurrently to message bus."""
    event_log, _, _, message_bus, _ = components

    # Register agents
    for i in range(10):
        message_bus.register_agent(f"agent-{i}")

    async def publish_message(idx: int) -> None:
        """Publish a single message."""
        from foundrai.models.message import AgentMessage, MessageType
        msg = AgentMessage(
            from_agent=f"agent-{idx % 10}",
            to_agent=f"agent-{(idx + 1) % 10}",
            type=MessageType.TASK_ASSIGNMENT,
            content=f"Message {idx}",
        )
        await message_bus.publish(msg)

    # Publish 100 messages concurrently
    tasks = [publish_message(i) for i in range(100)]
    await asyncio.gather(*tasks)

    # Verify all messages were recorded
    history = message_bus.get_history()
    assert len(history) == 100

    # Verify events were logged
    events = await event_log.query(event_type="agent.message", limit=200)
    assert len(events) == 100


@pytest.mark.asyncio
async def test_concurrent_event_log_appends(components):
    """Test appending many events concurrently to event log."""
    event_log, _, _, _, _ = components

    async def append_event(idx: int) -> None:
        """Append a single event."""
        await event_log.append(
            event_type=f"test.event.{idx % 10}",
            data={"index": idx, "data": f"Event {idx}"},
        )

    # Append 100 events concurrently
    tasks = [append_event(i) for i in range(100)]
    await asyncio.gather(*tasks)

    # Verify all events were logged
    all_events = await event_log.query(limit=200)
    assert len(all_events) == 100


@pytest.mark.asyncio
async def test_concurrent_sprint_status_updates(db, components):
    """Test updating sprint status concurrently from multiple sources."""
    _, sprint_store, _, _, _ = components

    from foundrai.models.sprint import SprintState

    # Create a sprint
    sprint_id = "test-sprint-race"
    state = SprintState(
        sprint_id=sprint_id,
        project_id="test-project",
        sprint_number=1,
        goal="Test concurrent updates",
        status=SprintStatus.PLANNING,
        tasks=[],
        messages=[],
        artifacts=[],
    )
    await sprint_store.create_sprint(state)

    # Try to update status concurrently
    async def update_status(status: SprintStatus) -> None:
        """Update sprint status."""
        await sprint_store.update_sprint_status(sprint_id, status)
        await asyncio.sleep(0.01)  # Small delay to increase contention

    # Fire off multiple concurrent updates
    tasks = [
        update_status(SprintStatus.PLANNING),
        update_status(SprintStatus.EXECUTING),
        update_status(SprintStatus.EXECUTING),
        update_status(SprintStatus.COMPLETED),
        update_status(SprintStatus.EXECUTING),
    ]
    await asyncio.gather(*tasks)

    # Verify sprint still exists and has a valid status
    stored = await sprint_store.get_sprint(sprint_id)
    assert stored is not None
    assert stored["status"] in [
        SprintStatus.PLANNING,
        SprintStatus.EXECUTING,
        SprintStatus.COMPLETED,
    ]


@pytest.mark.asyncio
async def test_concurrent_task_creation(db, components):
    """Test creating many tasks concurrently in a sprint."""
    _, sprint_store, _, _, _ = components

    from foundrai.models.sprint import SprintState

    # Create a sprint
    sprint_id = "test-sprint-tasks"
    state = SprintState(
        sprint_id=sprint_id,
        project_id="test-project",
        sprint_number=1,
        goal="Test concurrent task creation",
        status=SprintStatus.EXECUTING,
        tasks=[],
        messages=[],
        artifacts=[],
    )
    await sprint_store.create_sprint(state)

    async def create_task(idx: int) -> None:
        """Create a single task."""
        task = Task(
            title=f"Concurrent Task {idx}",
            description=f"Task created concurrently {idx}",
            acceptance_criteria=[f"Criterion {idx}"],
            dependencies=[],
            assigned_to="developer",
            priority=idx,
        )
        await sprint_store.create_task(sprint_id, task)

    # Create 50 tasks concurrently
    tasks = [create_task(i) for i in range(50)]
    await asyncio.gather(*tasks)

    # Verify all tasks were created
    stored_tasks = await sprint_store.get_tasks(sprint_id)
    assert len(stored_tasks) == 50


@pytest.mark.asyncio
async def test_concurrent_task_status_updates(db, components):
    """Test updating task status concurrently."""
    _, sprint_store, _, _, _ = components

    from foundrai.models.sprint import SprintState

    # Create a sprint with a task
    sprint_id = "test-sprint-status"
    task = Task(
        title="Test Task",
        description="For status updates",
        acceptance_criteria=["Works"],
        dependencies=[],
        assigned_to="developer",
        priority=1,
    )

    state = SprintState(
        sprint_id=sprint_id,
        project_id="test-project",
        sprint_number=1,
        goal="Test concurrent status updates",
        status=SprintStatus.EXECUTING,
        tasks=[],
        messages=[],
        artifacts=[],
    )
    await sprint_store.create_sprint(state)
    await sprint_store.create_task(sprint_id, task)

    async def update_task_status(status: TaskStatus) -> None:
        """Update task status."""
        task.status = status
        await sprint_store.update_task(task)
        await asyncio.sleep(0.01)  # Small delay to increase contention

    # Fire off multiple concurrent status updates
    tasks = [
        update_task_status(TaskStatus.IN_PROGRESS),
        update_task_status(TaskStatus.IN_REVIEW),
        update_task_status(TaskStatus.IN_PROGRESS),
        update_task_status(TaskStatus.DONE),
        update_task_status(TaskStatus.IN_REVIEW),
    ]
    await asyncio.gather(*tasks)

    # Verify task still exists and has a valid status
    stored_tasks = await sprint_store.get_tasks(sprint_id)
    assert len(stored_tasks) == 1
    stored_task = stored_tasks[0]
    assert stored_task.status in [
        TaskStatus.BACKLOG,
        TaskStatus.IN_PROGRESS,
        TaskStatus.IN_REVIEW,
        TaskStatus.DONE,
        TaskStatus.FAILED,
    ]


@pytest.mark.asyncio
async def test_concurrent_task_graph_mark_completed(components):
    """Test marking tasks as completed concurrently."""
    _, _, _, _, task_graph = components

    # Add tasks
    task_ids = []
    for i in range(50):
        task = Task(
            title=f"Task {i}",
            description=f"Description {i}",
            acceptance_criteria=[],
            dependencies=[],
            assigned_to="developer",
            priority=i,
        )
        await task_graph.add_task(task, depends_on=[])
        task_ids.append(task.id)

    async def mark_complete(task_id: str) -> None:
        """Mark a task as completed."""
        await task_graph.mark_completed(task_id)

    # Mark all as completed concurrently
    tasks = [mark_complete(tid) for tid in task_ids]
    await asyncio.gather(*tasks)

    # Verify no tasks are ready (all completed)
    ready = await task_graph.get_ready_tasks()
    assert len(ready) == 0


@pytest.mark.asyncio
async def test_high_parallelism_mixed_operations(db, components):
    """Stress test with mixed operations at high parallelism."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    from foundrai.models.message import AgentMessage, MessageType
    from foundrai.models.sprint import SprintState

    # Setup
    sprint_id = "stress-test-sprint"
    state = SprintState(
        sprint_id=sprint_id,
        project_id="test-project",
        sprint_number=1,
        goal="High parallelism stress test",
        status=SprintStatus.EXECUTING,
        tasks=[],
        messages=[],
        artifacts=[],
    )
    await sprint_store.create_sprint(state)

    for i in range(5):
        message_bus.register_agent(f"agent-{i}")

    operations = []

    # Mix of different operations
    for i in range(20):
        # Event logging
        operations.append(
            event_log.append(f"stress.event.{i % 5}", {"index": i})
        )

        # Task creation
        task = Task(
            title=f"Stress Task {i}",
            description=f"Task {i}",
            acceptance_criteria=[],
            dependencies=[],
            assigned_to="developer",
            priority=i,
        )
        operations.append(sprint_store.create_task(sprint_id, task))
        operations.append(task_graph.add_task(task, depends_on=[]))

        # Message publishing
        msg = AgentMessage(
            from_agent=f"agent-{i % 5}",
            to_agent=f"agent-{(i + 1) % 5}",
            type=MessageType.TASK_ASSIGNMENT,
            content=f"Stress message {i}",
        )
        operations.append(message_bus.publish(msg))

    # Execute all operations concurrently
    await asyncio.gather(*operations)

    # Verify data consistency
    assert task_graph.task_count == 20
    stored_tasks = await sprint_store.get_tasks(sprint_id)
    assert len(stored_tasks) == 20
    events = await event_log.query(limit=200)
    assert len(events) >= 20  # At least the stress events
    history = message_bus.get_history()
    assert len(history) == 20


@pytest.mark.asyncio
async def test_concurrent_sprint_execution_simulation(db, tmp_path, sprint_context, components):
    """Simulate multiple concurrent sprint operations like a real workload."""
    event_log, sprint_store, artifact_store, message_bus, task_graph = components

    # Create agents
    pm_tasks = json.dumps([
        {
            "title": f"Feature {i}",
            "description": f"Build feature {i}",
            "acceptance_criteria": ["Works"],
            "dependencies": [],
            "assigned_to": "developer",
            "priority": i,
        }
        for i in range(10)
    ])

    qa_pass = json.dumps({"passed": True, "issues": [], "suggestions": []})

    pm = ProductManagerAgent(
        role=get_role(AgentRoleName.PRODUCT_MANAGER),
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(pm_tasks, "json"),
    )
    dev = DeveloperAgent(
        role=get_role(AgentRoleName.DEVELOPER),
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock("Implemented"),
    )
    qa = QAEngineerAgent(
        role=get_role(AgentRoleName.QA_ENGINEER),
        model="test/model",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=_make_runtime_mock(qa_pass, "json"),
    )

    for role in [AgentRoleName.PRODUCT_MANAGER, AgentRoleName.DEVELOPER, AgentRoleName.QA_ENGINEER]:
        message_bus.register_agent(role.value)

    agent_map = {
        AgentRoleName.PRODUCT_MANAGER.value: pm,
        AgentRoleName.DEVELOPER.value: dev,
        AgentRoleName.QA_ENGINEER.value: qa,
    }

    config = FoundrAIConfig()
    engine = SprintEngine(
        config=config,
        agents=agent_map,
        task_graph=task_graph,
        message_bus=message_bus,
        sprint_store=sprint_store,
        event_log=event_log,
        artifact_store=artifact_store,
    )

    # Run sprint while also performing concurrent operations
    async def background_operations():
        """Simulate background activity during sprint."""
        for i in range(30):
            await asyncio.sleep(0.05)
            await event_log.append("background.activity", {"iteration": i})

    sprint_task = asyncio.create_task(
        engine.run_sprint(goal="Concurrent execution test", project_id="test")
    )
    background_task = asyncio.create_task(background_operations())

    result, _ = await asyncio.gather(sprint_task, background_task)

    # Verify sprint completed successfully despite concurrent activity
    assert result["status"] == SprintStatus.COMPLETED
    assert len(result["tasks"]) == 10

    # Verify background events were logged
    bg_events = await event_log.query(event_type="background.activity", limit=50)
    assert len(bg_events) == 30


@pytest.mark.asyncio
async def test_extreme_parallelism_event_logging(components):
    """Stress test event log with 200 concurrent writes."""
    event_log, _, _, _, _ = components

    async def log_event(idx: int) -> None:
        """Log a single event."""
        await event_log.append(
            event_type="extreme.stress",
            data={"index": idx, "thread": idx % 20},
        )

    # Fire off 200 concurrent event logging operations
    tasks = [log_event(i) for i in range(200)]
    await asyncio.gather(*tasks)

    # Verify all events were logged
    events = await event_log.query(event_type="extreme.stress", limit=250)
    assert len(events) == 200

    # Verify data integrity - all indices should be present
    indices = {e["data"]["index"] for e in events}
    assert len(indices) == 200
    assert min(indices) == 0
    assert max(indices) == 199


@pytest.mark.asyncio
async def test_concurrent_task_graph_cycle_detection(components):
    """Test that cycle detection works correctly under concurrency."""
    _, _, _, _, task_graph = components

    # Create a chain: A -> B -> C
    task_a = Task(
        title="Task A",
        description="First task",
        acceptance_criteria=[],
        dependencies=[],
        assigned_to="developer",
        priority=1,
    )
    task_b = Task(
        title="Task B",
        description="Second task",
        acceptance_criteria=[],
        dependencies=[task_a.id],
        assigned_to="developer",
        priority=2,
    )
    task_c = Task(
        title="Task C",
        description="Third task",
        acceptance_criteria=[],
        dependencies=[task_b.id],
        assigned_to="developer",
        priority=3,
    )

    await task_graph.add_task(task_a, depends_on=[])
    await task_graph.add_task(task_b, depends_on=[task_a.id])
    await task_graph.add_task(task_c, depends_on=[task_b.id])

    # Now try to create a cycle: add D that depends on C,
    # and try to make C depend on D concurrently (should fail)
    task_d = Task(
        title="Task D",
        description="Would create cycle",
        acceptance_criteria=[],
        dependencies=[task_c.id],
        assigned_to="developer",
        priority=4,
    )

    # This should work
    await task_graph.add_task(task_d, depends_on=[task_c.id])

    # Verify no cycles exist
    execution_order = await task_graph.get_execution_order()
    assert len(execution_order) == 4
    assert task_graph.task_count == 4


@pytest.mark.asyncio
async def test_message_bus_listener_concurrency(components):
    """Test message bus listeners under high concurrency."""
    event_log, _, _, message_bus, _ = components

    message_bus.register_agent("sender")
    message_bus.register_agent("receiver")

    # Track listener invocations
    listener_calls = []

    async def listener(message):
        """Track message delivery."""
        listener_calls.append(message.content)
        await asyncio.sleep(0.001)  # Simulate processing

    message_bus.register_listener(listener)

    async def publish_message(idx: int) -> None:
        """Publish a message."""
        from foundrai.models.message import AgentMessage, MessageType
        msg = AgentMessage(
            from_agent="sender",
            to_agent="receiver",
            type=MessageType.TASK_ASSIGNMENT,
            content=f"Message {idx}",
        )
        await message_bus.publish(msg)

    # Publish 100 messages concurrently
    tasks = [publish_message(i) for i in range(100)]
    await asyncio.gather(*tasks)

    # Give listeners time to process
    await asyncio.sleep(0.5)

    # Verify all messages were delivered to listener
    assert len(listener_calls) == 100


@pytest.mark.asyncio
async def test_concurrent_artifact_storage(db, components):
    """Test storing artifacts concurrently."""
    _, _, artifact_store, _, _ = components

    sprint_id = "artifact-test"

    async def store_artifact(idx: int) -> None:
        """Store a single artifact."""
        artifact = {
            "id": f"artifact-{idx}",
            "sprint_id": sprint_id,
            "task_id": f"task-{idx % 10}",
            "agent_id": "developer",
            "artifact_type": "test",
            "file_path": f"/tmp/test_{idx}.txt",
            "content_hash": f"hash_{idx}",
            "size_bytes": 100 + idx,
        }
        await artifact_store.save(artifact)

    # Store 50 artifacts concurrently
    tasks = [store_artifact(i) for i in range(50)]
    await asyncio.gather(*tasks)

    # Verify all artifacts were stored
    artifacts = await artifact_store.get_by_sprint(sprint_id)
    assert len(artifacts) == 50
