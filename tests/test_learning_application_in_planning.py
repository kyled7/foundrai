"""Integration test: Verify learnings are retrieved and applied during sprint planning.

This test focuses on the SprintPlanning ceremony and verifies:
1. Learnings are stored in VectorMemory
2. SprintPlanning.run() queries learnings
3. PM.refine_with_learnings() is called with retrieved learnings
4. Tasks are refined based on learnings
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from foundrai.agents.context import SprintContext
from foundrai.agents.personas.product_manager import ProductManagerAgent
from foundrai.agents.roles import get_role
from foundrai.agents.runtime import RuntimeResult
from foundrai.config import MemoryConfig
from foundrai.models.enums import AgentRoleName
from foundrai.models.learning import Learning
from foundrai.orchestration.ceremonies import SprintPlanning
from foundrai.orchestration.message_bus import MessageBus
from foundrai.persistence.event_log import EventLog
from foundrai.persistence.vector_memory import VectorMemory

# Mock PM responses
INITIAL_TASKS_JSON = json.dumps(
    [
        {
            "title": "Build feature X",
            "description": "Basic implementation",
            "acceptance_criteria": ["Feature works"],
            "dependencies": [],
            "assigned_to": "developer",
            "priority": 1,
        }
    ]
)

REFINED_TASKS_JSON = json.dumps(
    [
        {
            "title": "Build secure feature X",
            "description": "Implementation with security best practices",
            "acceptance_criteria": [
                "Feature works",
                "Input validation added",
                "Security review completed",
            ],
            "dependencies": [],
            "assigned_to": "developer",
            "priority": 1,
        }
    ]
)


@pytest.fixture
def project_id():
    return "test-planning-learnings"


@pytest.fixture
def sprint_context(tmp_path, project_id):
    ctx = SprintContext(
        project_name=project_id,
        project_path=str(tmp_path),
        sprint_goal="Build feature X",
        sprint_number=2,
    )
    # Add project_id attribute for compatibility
    ctx.project_id = project_id
    return ctx


@pytest.fixture
async def vector_memory(db, tmp_path):
    """Create VectorMemory with database connection."""
    memory_config = MemoryConfig(chromadb_path=str(tmp_path / "chroma"))
    return VectorMemory(config=memory_config, db=db)


@pytest.fixture
async def message_bus(db):
    """Create message bus."""
    event_log = EventLog(db)
    mb = MessageBus(event_log)
    mb.register_agent("product_manager")
    return mb


@pytest.mark.asyncio
async def test_sprint_planning_retrieves_and_applies_learnings(
    db, tmp_path, project_id, sprint_context, vector_memory, message_bus
):
    """Test that SprintPlanning retrieves learnings and PM.refine_with_learnings is called.

    Test Flow:
    1. Store learnings in VectorMemory (simulating previous sprint)
    2. Create SprintPlanning ceremony
    3. Mock PM to track decompose and refine calls
    4. Run planning with vector_memory
    5. Verify learnings were queried
    6. Verify PM.refine_with_learnings was called with learnings
    7. Verify refined tasks were returned
    """

    # STEP 1: Store learnings from "previous sprint"
    print("\n" + "=" * 80)
    print("STEP 1: Store learnings in VectorMemory (simulating Sprint 1)")
    print("=" * 80)

    learnings = [
        Learning(
            content="Always use input validation on user data",
            category="security",
            sprint_id="sprint-001",
            project_id=project_id,
        ),
        Learning(
            content="Add security review to acceptance criteria",
            category="process",
            sprint_id="sprint-001",
            project_id=project_id,
        ),
        Learning(
            content="Security vulnerabilities were found in Sprint 1",
            category="lessons_learned",
            sprint_id="sprint-001",
            project_id=project_id,
        ),
    ]

    for learning in learnings:
        await vector_memory.store_learning(learning)

    print(f"\n✓ Stored {len(learnings)} learnings:")
    for lr in learnings:
        print(f"  - [{lr.category}] {lr.content}")

    # Verify learnings are retrievable
    all_learnings = await vector_memory.get_all_learnings(project_id=project_id)
    assert len(all_learnings) == len(learnings), "All learnings should be stored"

    # STEP 2: Create PM agent with mocked runtime
    print("\n" + "=" * 80)
    print("STEP 2: Create PM agent and SprintPlanning")
    print("=" * 80)

    pm = ProductManagerAgent(
        role=get_role(AgentRoleName.PRODUCT_MANAGER),
        model="test",
        tools=[],
        message_bus=message_bus,
        sprint_context=sprint_context,
        runtime=AsyncMock(),
    )

    # Track calls to PM methods
    decompose_calls = []
    refine_calls = []

    # Mock PM runtime to return different responses
    pm.runtime.run = AsyncMock(
        side_effect=[
            # First call: decompose_goal
            RuntimeResult(
                output=INITIAL_TASKS_JSON,
                parsed=json.loads(INITIAL_TASKS_JSON),
                artifacts=[],
                tokens_used=100,
                success=True,
            ),
            # Second call: refine_with_learnings
            RuntimeResult(
                output=REFINED_TASKS_JSON,
                parsed=json.loads(REFINED_TASKS_JSON),
                artifacts=[],
                tokens_used=150,
                success=True,
            ),
        ]
    )

    # Spy on PM methods to track calls
    original_decompose = pm.decompose_goal
    original_refine = pm.refine_with_learnings

    async def spy_decompose(goal):
        decompose_calls.append(goal)
        return await original_decompose(goal)

    async def spy_refine(tasks, learnings):
        refine_calls.append((tasks, learnings))
        return await original_refine(tasks, learnings)

    pm.decompose_goal = spy_decompose
    pm.refine_with_learnings = spy_refine

    agents = {"product_manager": pm}

    # STEP 3: Run SprintPlanning with vector_memory
    print("\n" + "=" * 80)
    print("STEP 3: Run SprintPlanning with vector_memory")
    print("=" * 80)

    planning = SprintPlanning()

    # Spy on vector_memory.query_relevant
    query_relevant_calls = []
    original_query_relevant = vector_memory.query_relevant

    async def spy_query_relevant(*args, **kwargs):
        query_relevant_calls.append((args, kwargs))
        result = await original_query_relevant(*args, **kwargs)
        return result

    vector_memory.query_relevant = spy_query_relevant

    # Run planning
    tasks = await planning.run(
        goal=sprint_context.sprint_goal,
        agents=agents,
        context=sprint_context,
        vector_memory=vector_memory,
    )

    print(f"\n✓ Planning completed, returned {len(tasks)} tasks")

    # STEP 4: Verify vector_memory.query_relevant was called
    print("\n" + "=" * 80)
    print("VERIFICATION 1: vector_memory.query_relevant called")
    print("=" * 80)

    assert len(query_relevant_calls) > 0, "query_relevant should have been called"

    print(f"\n✓ query_relevant called {len(query_relevant_calls)} time(s)")
    for i, (args, kwargs) in enumerate(query_relevant_calls):
        query = args[0] if args else kwargs.get("query", "N/A")
        k = kwargs.get("k", "N/A")
        proj_id = kwargs.get("project_id", "N/A")
        print(f"  Call {i + 1}: query='{query}', k={k}, project_id={proj_id}")

    # Verify it queried for the sprint goal
    call_args, call_kwargs = query_relevant_calls[0]
    query_text = call_args[0] if call_args else call_kwargs.get("query", "")
    assert query_text == sprint_context.sprint_goal, (
        f"Should query for sprint goal. Expected: '{sprint_context.sprint_goal}', Got: '{query_text}'"
    )

    # STEP 5: Verify PM.refine_with_learnings was called
    print("\n" + "=" * 80)
    print("VERIFICATION 2: PM.refine_with_learnings called")
    print("=" * 80)

    assert len(refine_calls) > 0, "refine_with_learnings should have been called"

    print(f"\n✓ refine_with_learnings called {len(refine_calls)} time(s)")

    tasks_passed, learnings_passed = refine_calls[0]
    print(f"  - Tasks passed: {len(tasks_passed)}")
    print(f"  - Learnings passed: {len(learnings_passed)}")

    assert len(learnings_passed) > 0, "Learnings should have been passed to refine"

    print("\n  Learnings passed to refine_with_learnings:")
    for lr in learnings_passed:
        content = lr.content if hasattr(lr, "content") else str(lr)
        print(f"    - {content}")

    # STEP 6: Verify refined tasks were returned
    print("\n" + "=" * 80)
    print("VERIFICATION 3: Tasks were refined")
    print("=" * 80)

    assert len(tasks) > 0, "Planning should return tasks"

    print(f"\n✓ Final tasks count: {len(tasks)}")
    for task in tasks:
        print(f"\n  Task: {task.title}")
        print(f"    Description: {task.description}")
        print(f"    Acceptance Criteria: {task.acceptance_criteria}")

    # Verify refinement happened by checking acceptance criteria count
    # Initial had 1 criterion, refined should have more
    assert len(tasks[0].acceptance_criteria) > 1, (
        "Refined tasks should have more acceptance criteria than initial tasks"
    )

    # FINAL SUMMARY
    print("\n" + "=" * 80)
    print("✅ ALL VERIFICATIONS PASSED")
    print("=" * 80)
    print(f"\n1. ✅ Stored {len(learnings)} learnings in VectorMemory")
    print("2. ✅ vector_memory.query_relevant() called during planning")
    print(f"3. ✅ PM.refine_with_learnings() called with {len(learnings_passed)} learnings")
    print(f"4. ✅ Tasks were refined (criteria count: 1 → {len(tasks[0].acceptance_criteria)})")
    print("\n🎉 Learning retrieval and application in planning VERIFIED!")
