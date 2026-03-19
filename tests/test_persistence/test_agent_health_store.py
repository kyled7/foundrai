"""Tests for AgentHealthStore persistence layer."""

from __future__ import annotations

import pytest
import pytest_asyncio

from foundrai.models.agent_health import AgentHealth, AgentHealthMetrics
from foundrai.models.enums import AgentRoleName
from foundrai.persistence.agent_health_store import AgentHealthStore
from foundrai.persistence.database import Database


@pytest_asyncio.fixture
async def health_store(db: Database) -> AgentHealthStore:
    """Provide an AgentHealthStore instance."""
    return AgentHealthStore(db)


@pytest_asyncio.fixture
async def test_project(db: Database) -> str:
    """Create a test project and return its ID."""
    cursor = await db.conn.execute(
        "INSERT INTO projects (project_id, name, created_at) VALUES (?, ?, datetime('now'))",
        ("test-project", "Test Project"),
    )
    await db.conn.commit()
    return "test-project"


@pytest_asyncio.fixture
async def test_sprint(db: Database, test_project: str) -> str:
    """Create a test sprint and return its ID."""
    cursor = await db.conn.execute(
        """INSERT INTO sprints (sprint_id, project_id, sprint_number, goal, status, created_at)
           VALUES (?, ?, ?, ?, ?, datetime('now'))""",
        ("test-sprint", test_project, 1, "Test Sprint", "in_progress"),
    )
    await db.conn.commit()
    return "test-sprint"


@pytest.mark.asyncio
async def test_calculate_health_score_no_tasks(
    health_store: AgentHealthStore,
    test_project: str,
) -> None:
    """Test health score calculation when agent has no tasks."""
    health = await health_store.calculate_health_score(
        AgentRoleName.DEVELOPER,
        test_project,
        None,
    )

    assert health.health_score == 0.0
    assert health.status == "unhealthy"
    assert health.metrics.total_tasks == 0
    assert health.metrics.completed_tasks == 0
    assert health.metrics.completion_rate == 0.0
    assert health.metrics.quality_score == 0.0
    assert health.agent_role == "developer"
    assert health.project_id == test_project
    assert len(health.recommendations) > 0


@pytest.mark.asyncio
async def test_calculate_health_score_with_tasks(
    health_store: AgentHealthStore,
    db: Database,
    test_project: str,
    test_sprint: str,
) -> None:
    """Test health score calculation with sample tasks."""
    # Create tasks for the developer
    for i in range(10):
        status = "done" if i < 8 else "in_progress"
        await db.conn.execute(
            """INSERT INTO tasks (task_id, sprint_id, title, assigned_to, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))""",
            (f"task-{i}", test_sprint, f"Task {i}", "developer", status),
        )

    # Add some token usage
    for i in range(5):
        await db.conn.execute(
            """INSERT INTO token_usage (task_id, sprint_id, project_id, agent_role, model,
                                       prompt_tokens, completion_tokens, total_tokens, cost_usd)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (f"task-{i}", test_sprint, test_project, "developer", "gpt-4", 100, 50, 150, 0.01),
        )

    await db.conn.commit()

    # Calculate health score
    health = await health_store.calculate_health_score(
        AgentRoleName.DEVELOPER,
        test_project,
        None,
    )

    assert health.metrics.total_tasks == 10
    assert health.metrics.completed_tasks == 8
    assert health.metrics.completion_rate == 80.0
    assert health.metrics.total_tokens == 750  # 5 * 150
    assert health.metrics.total_cost_usd == 0.05  # 5 * 0.01
    assert health.metrics.cost_efficiency > 0  # 750 / 8 = 93.75
    assert health.health_score > 0


@pytest.mark.asyncio
async def test_normalize_cost_efficiency(health_store: AgentHealthStore) -> None:
    """Test cost efficiency normalization logic."""
    # Zero tokens = perfect score
    assert health_store._normalize_cost_efficiency(0) == 100.0

    # 5000 tokens = target (50 score)
    assert health_store._normalize_cost_efficiency(5000) == 50.0

    # Higher tokens = lower score
    assert health_store._normalize_cost_efficiency(10000) < 50.0
    assert health_store._normalize_cost_efficiency(20000) < health_store._normalize_cost_efficiency(10000)

    # Lower tokens = higher score
    assert health_store._normalize_cost_efficiency(1000) > 50.0
    assert health_store._normalize_cost_efficiency(100) > health_store._normalize_cost_efficiency(1000)

    # Score is capped at 100
    assert health_store._normalize_cost_efficiency(10) <= 100.0


@pytest.mark.asyncio
async def test_generate_recommendations_low_completion(health_store: AgentHealthStore) -> None:
    """Test recommendations generated for low completion rate."""
    metrics = AgentHealthMetrics(
        completion_rate=40.0,  # Below 50%
        quality_score=80.0,
        cost_efficiency=3000,
        avg_execution_time=100.0,
        failure_rate=5.0,
        total_tasks=10,
        completed_tasks=4,
        failed_tasks=1,
        total_tokens=12000,
        total_cost_usd=0.50,
    )

    recommendations = health_store._generate_recommendations(metrics)
    assert any("Low completion rate" in r for r in recommendations)


@pytest.mark.asyncio
async def test_generate_recommendations_low_quality(health_store: AgentHealthStore) -> None:
    """Test recommendations generated for low quality score."""
    metrics = AgentHealthMetrics(
        completion_rate=80.0,
        quality_score=40.0,  # Below 50%
        cost_efficiency=3000,
        avg_execution_time=100.0,
        failure_rate=5.0,
        total_tasks=10,
        completed_tasks=8,
        failed_tasks=1,
        total_tokens=24000,
        total_cost_usd=1.00,
    )

    recommendations = health_store._generate_recommendations(metrics)
    assert any("Low quality score" in r for r in recommendations)


@pytest.mark.asyncio
async def test_generate_recommendations_high_cost(health_store: AgentHealthStore) -> None:
    """Test recommendations generated for high token usage."""
    metrics = AgentHealthMetrics(
        completion_rate=80.0,
        quality_score=80.0,
        cost_efficiency=15000,  # High tokens per task
        avg_execution_time=100.0,
        failure_rate=5.0,
        total_tasks=10,
        completed_tasks=8,
        failed_tasks=1,
        total_tokens=120000,
        total_cost_usd=5.00,
    )

    recommendations = health_store._generate_recommendations(metrics)
    assert any("token usage" in r.lower() for r in recommendations)


@pytest.mark.asyncio
async def test_generate_recommendations_high_failure(health_store: AgentHealthStore) -> None:
    """Test recommendations generated for high failure rate."""
    metrics = AgentHealthMetrics(
        completion_rate=60.0,
        quality_score=80.0,
        cost_efficiency=3000,
        avg_execution_time=100.0,
        failure_rate=30.0,  # High failure rate
        total_tasks=10,
        completed_tasks=6,
        failed_tasks=3,
        total_tokens=18000,
        total_cost_usd=0.75,
    )

    recommendations = health_store._generate_recommendations(metrics)
    assert any("failure rate" in r.lower() for r in recommendations)


@pytest.mark.asyncio
async def test_generate_recommendations_all_good(health_store: AgentHealthStore) -> None:
    """Test recommendations when agent is performing well."""
    metrics = AgentHealthMetrics(
        completion_rate=90.0,
        quality_score=90.0,
        cost_efficiency=3000,
        avg_execution_time=100.0,
        failure_rate=2.0,
        total_tasks=10,
        completed_tasks=9,
        failed_tasks=0,
        total_tokens=27000,
        total_cost_usd=1.00,
    )

    recommendations = health_store._generate_recommendations(metrics)
    assert any("performing well" in r.lower() for r in recommendations)


@pytest.mark.asyncio
async def test_get_agent_health_none(
    health_store: AgentHealthStore,
    test_project: str,
) -> None:
    """Test getting health for agent with no records."""
    health = await health_store.get_agent_health(
        AgentRoleName.DEVELOPER,
        test_project,
        None,
    )

    assert health is None


@pytest.mark.asyncio
async def test_get_agent_health_exists(
    health_store: AgentHealthStore,
    test_project: str,
) -> None:
    """Test getting health for agent with existing record."""
    # Calculate and save health
    saved_health = await health_store.calculate_health_score(
        AgentRoleName.DEVELOPER,
        test_project,
        None,
    )

    # Retrieve it
    retrieved_health = await health_store.get_agent_health(
        AgentRoleName.DEVELOPER,
        test_project,
        None,
    )

    assert retrieved_health is not None
    assert retrieved_health.agent_role == "developer"
    assert retrieved_health.project_id == test_project
    assert retrieved_health.health_score == saved_health.health_score


@pytest.mark.asyncio
async def test_get_project_health(
    health_store: AgentHealthStore,
    test_project: str,
) -> None:
    """Test getting health for all agents in a project."""
    # Calculate health for multiple agents
    await health_store.calculate_health_score(AgentRoleName.DEVELOPER, test_project, None)
    await health_store.calculate_health_score(AgentRoleName.QA_ENGINEER, test_project, None)

    # Get project health
    health_records = await health_store.get_project_health(test_project)

    assert len(health_records) == 2
    agent_roles = {h.agent_role for h in health_records}
    assert "developer" in agent_roles
    assert "qa_engineer" in agent_roles


@pytest.mark.asyncio
async def test_get_sprint_health(
    health_store: AgentHealthStore,
    test_project: str,
    test_sprint: str,
) -> None:
    """Test getting health for all agents in a sprint."""
    # Calculate health for sprint-specific agents
    await health_store.calculate_health_score(AgentRoleName.DEVELOPER, test_project, test_sprint)
    await health_store.calculate_health_score(AgentRoleName.QA_ENGINEER, test_project, test_sprint)

    # Get sprint health
    health_records = await health_store.get_sprint_health(test_sprint)

    assert len(health_records) == 2
    agent_roles = {h.agent_role for h in health_records}
    assert "developer" in agent_roles
    assert "qa_engineer" in agent_roles


@pytest.mark.asyncio
async def test_health_status_thresholds(
    health_store: AgentHealthStore,
    db: Database,
    test_project: str,
    test_sprint: str,
) -> None:
    """Test that health status is correctly determined by score."""
    # Create scenario for healthy status (>= 80)
    for i in range(10):
        await db.conn.execute(
            """INSERT INTO tasks (task_id, sprint_id, title, assigned_to, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))""",
            (f"task-healthy-{i}", test_sprint, f"Task {i}", "developer", "done"),
        )

    await db.conn.commit()

    health = await health_store.calculate_health_score(
        AgentRoleName.DEVELOPER,
        test_project,
        None,
    )

    # With 100% completion and low cost, should be healthy
    if health.health_score >= 80:
        assert health.status == "healthy"
    elif health.health_score >= 50:
        assert health.status == "warning"
    else:
        assert health.status == "unhealthy"
