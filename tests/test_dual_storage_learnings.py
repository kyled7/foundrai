"""Integration test: Verify learnings are stored in both ChromaDB and SQLite."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from foundrai.agents.context import SprintContext
from foundrai.agents.runtime import AgentRuntime, RuntimeResult
from foundrai.config import MemoryConfig
from foundrai.orchestration.message_bus import MessageBus
from foundrai.orchestration.task_graph import TaskGraph
from foundrai.persistence.artifact_store import ArtifactStore
from foundrai.persistence.event_log import EventLog
from foundrai.persistence.sprint_store import SprintStore
from foundrai.persistence.vector_memory import VectorMemory

# Mock responses
PM_RESPONSE = json.dumps(
    [
        {
            "title": "Build feature",
            "description": "Create a feature with intentional bug",
            "acceptance_criteria": ["Feature works"],
            "dependencies": [],
            "assigned_to": "developer",
            "priority": 1,
        }
    ]
)

DEV_RESPONSE = "Feature implemented with a known bug for testing"

QA_FAIL_RESPONSE = json.dumps(
    {
        "passed": False,
        "issues": ["Found critical bug in implementation"],
        "suggestions": ["Fix the bug and add tests"],
    }
)

RETRO_RESPONSE = json.dumps(
    {
        "went_well": ["Task was completed on time"],
        "went_wrong": ["Quality issues found by QA"],
        "action_items": ["Improve code review process"],
        "learnings": [
            "Need more thorough testing before QA review",
            "Should add unit tests before implementation",
        ],
    }
)


def _make_runtime_mock(response_content: str, response_format: str | None = None) -> AsyncMock:
    """Create a mock runtime that returns a canned response."""
    runtime = AsyncMock(spec=AgentRuntime)
    parsed = None
    starts_json = response_content.startswith(("[", "{"))
    if response_format == "json" or starts_json:
        try:
            parsed = json.loads(response_content)
        except json.JSONDecodeError:
            pass
    runtime.run = AsyncMock(
        return_value=RuntimeResult(
            output=response_content,
            parsed=parsed,
            artifacts=[],
            tokens_used=100,
            success=True,
        )
    )
    return runtime


@pytest.fixture
def sprint_context(tmp_path):
    return SprintContext(
        project_name="test-dual-storage",
        project_path=str(tmp_path),
        sprint_goal="Test dual storage of learnings",
        sprint_number=1,
    )


@pytest.fixture
async def components(db, tmp_path):
    """Set up all orchestration components with VectorMemory."""
    event_log = EventLog(db)
    sprint_store = SprintStore(db)
    artifact_store = ArtifactStore(db)
    message_bus = MessageBus(event_log)
    task_graph = TaskGraph()

    # Create VectorMemory with database connection
    memory_config = MemoryConfig(chromadb_path=str(tmp_path / "chroma"))
    vector_memory = VectorMemory(config=memory_config, db=db)

    return event_log, sprint_store, artifact_store, message_bus, task_graph, vector_memory


@pytest.mark.asyncio
async def test_learnings_stored_in_both_chromadb_and_sqlite(db, tmp_path):
    """Verify learnings are stored in both ChromaDB and SQLite.

    This is a direct test that:
    1. Creates a VectorMemory with database connection
    2. Stores learnings via VectorMemory.store_learning()
    3. Queries SQLite learnings table
    4. Queries VectorMemory (ChromaDB)
    5. Verifies both stores contain the same learnings
    """
    from foundrai.models.learning import Learning

    # Create VectorMemory with database connection
    memory_config = MemoryConfig(chromadb_path=str(tmp_path / "chroma"))
    vector_memory = VectorMemory(config=memory_config, db=db)

    # Create test learnings
    learnings = [
        Learning(
            content="Need more thorough testing before QA review",
            category="quality",
            sprint_id="sprint-test-001",
            project_id="test-dual-storage",
        ),
        Learning(
            content="Should add unit tests before implementation",
            category="process",
            sprint_id="sprint-test-001",
            project_id="test-dual-storage",
        ),
        Learning(
            content="Sprint completion rate: 75%",
            category="metrics",
            sprint_id="sprint-test-001",
            project_id="test-dual-storage",
        ),
    ]

    # Store learnings via VectorMemory
    for learning in learnings:
        await vector_memory.store_learning(learning)

    # STEP 1: Query SQLite learnings table
    cursor = await db.conn.execute(
        "SELECT learning_id, project_id, sprint_id, content, category FROM learnings WHERE sprint_id = ?",
        ("sprint-test-001",),
    )
    sqlite_rows = await cursor.fetchall()

    # Convert to dict for easier comparison
    sqlite_learnings = [
        {
            "id": row[0],
            "project_id": row[1],
            "sprint_id": row[2],
            "content": row[3],
            "category": row[4],
        }
        for row in sqlite_rows
    ]

    print(f"\n=== SQLite Learnings ({len(sqlite_learnings)}) ===")
    for learning in sqlite_learnings:
        print(f"  - [{learning['category']}] {learning['content']}")

    # STEP 2: Query VectorMemory (ChromaDB)
    vector_learnings_list = await vector_memory.get_all_learnings(project_id="test-dual-storage")

    # Filter to only this sprint
    vector_learnings = [lr for lr in vector_learnings_list if lr.sprint_id == "sprint-test-001"]

    print(f"\n=== ChromaDB Learnings ({len(vector_learnings)}) ===")
    for learning in vector_learnings:
        print(f"  - [{learning.category}] {learning.content}")

    # STEP 3: Verify both stores have learnings
    assert len(sqlite_learnings) > 0, "SQLite should contain learnings"
    assert len(vector_learnings) > 0, "ChromaDB should contain learnings"

    # STEP 4: Verify both stores have the same number of learnings
    assert len(sqlite_learnings) == len(vector_learnings), (
        f"Both stores should have same count. SQLite: {len(sqlite_learnings)}, ChromaDB: {len(vector_learnings)}"
    )

    # STEP 5: Verify content matches (order-independent)
    sqlite_contents = {lr["content"] for lr in sqlite_learnings}
    vector_contents = {lr.content for lr in vector_learnings}

    assert sqlite_contents == vector_contents, (
        f"Learning content should match.\nSQLite: {sqlite_contents}\nChromaDB: {vector_contents}"
    )

    # STEP 6: Verify metadata matches for each learning
    vector_by_id = {lr.id: lr for lr in vector_learnings}

    for sqlite_lr in sqlite_learnings:
        learning_id = sqlite_lr["id"]
        assert learning_id in vector_by_id, f"Learning {learning_id} should exist in ChromaDB"

        vector_lr = vector_by_id[learning_id]

        # Verify metadata matches
        assert vector_lr.project_id == sqlite_lr["project_id"], (
            f"Project ID mismatch for {learning_id}"
        )
        assert vector_lr.sprint_id == sqlite_lr["sprint_id"], (
            f"Sprint ID mismatch for {learning_id}"
        )
        assert vector_lr.content == sqlite_lr["content"], f"Content mismatch for {learning_id}"
        assert vector_lr.category == sqlite_lr["category"], f"Category mismatch for {learning_id}"

    print(f"\n✅ VERIFICATION PASSED: All {len(sqlite_learnings)} learnings match in both stores!")
    print("   Sprint ID: sprint-test-001")
    print("   Project ID: test-dual-storage")


@pytest.mark.asyncio
async def test_learnings_persist_across_vector_memory_instances(db, tmp_path):
    """Verify learnings persisted in ChromaDB survive VectorMemory recreation."""
    memory_config = MemoryConfig(chromadb_path=str(tmp_path / "chroma"))

    # Create first VectorMemory instance and store a learning
    vm1 = VectorMemory(config=memory_config, db=db)

    from foundrai.models.learning import Learning

    test_learning = Learning(
        content="Test learning for persistence",
        category="test",
        sprint_id="sprint-persist-test",
        project_id="project-persist-test",
    )

    await vm1.store_learning(test_learning)

    # Query from first instance
    learnings1 = await vm1.get_all_learnings(project_id="project-persist-test")
    assert len(learnings1) == 1
    assert learnings1[0].content == "Test learning for persistence"

    # Create second VectorMemory instance (simulating app restart)
    vm2 = VectorMemory(config=memory_config, db=db)

    # Query from second instance - should still find the learning
    learnings2 = await vm2.get_all_learnings(project_id="project-persist-test")
    assert len(learnings2) == 1
    assert learnings2[0].content == "Test learning for persistence"
    assert learnings2[0].id == test_learning.id

    # Verify it's also in SQLite
    cursor = await db.conn.execute(
        "SELECT content FROM learnings WHERE learning_id = ?", (test_learning.id,)
    )
    row = await cursor.fetchone()
    assert row is not None
    assert row[0] == "Test learning for persistence"

    print("\n✅ PERSISTENCE VERIFIED: Learnings survive VectorMemory recreation")
