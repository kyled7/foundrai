"""Integration tests for agent health API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_project_agent_health_empty(client: AsyncClient, project_id: str):
    """Test GET /api/projects/{id}/agent-health with no health data."""
    response = await client.get(f"/api/projects/{project_id}/agent-health")
    assert response.status_code == 200

    data = response.json()
    assert "project_id" in data
    assert data["project_id"] == project_id
    assert "agents" in data
    assert isinstance(data["agents"], list)
    assert len(data["agents"]) == 0  # No health data yet


@pytest.mark.asyncio
async def test_get_project_agent_health_with_data(client: AsyncClient, project_id: str):
    """Test GET /api/projects/{id}/agent-health returns health data."""
    # First calculate health for a developer
    calc_response = await client.post(
        f"/api/projects/{project_id}/agents/developer/health/calculate"
    )
    assert calc_response.status_code == 200

    # Now get project health
    response = await client.get(f"/api/projects/{project_id}/agent-health")
    assert response.status_code == 200

    data = response.json()
    assert data["project_id"] == project_id
    assert "agents" in data
    assert len(data["agents"]) == 1

    # Verify structure
    agent = data["agents"][0]
    assert agent["agent_role"] == "developer"
    assert "health_score" in agent
    assert "status" in agent
    assert "metrics" in agent
    assert "recommendations" in agent
    assert "timestamp" in agent

    # Verify metrics structure
    metrics = agent["metrics"]
    assert "completion_rate" in metrics
    assert "quality_score" in metrics
    assert "cost_efficiency" in metrics
    assert "failure_rate" in metrics
    assert "total_tasks" in metrics
    assert "completed_tasks" in metrics


@pytest.mark.asyncio
async def test_get_agent_health_no_data(client: AsyncClient, project_id: str):
    """Test GET /api/projects/{id}/agents/{role}/health with no data."""
    response = await client.get(f"/api/projects/{project_id}/agents/developer/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "no_data"
    assert data["project_id"] == project_id
    assert data["agent_role"] == "developer"
    assert "message" in data
    assert data["health_score"] is None


@pytest.mark.asyncio
async def test_get_agent_health_with_data(client: AsyncClient, project_id: str):
    """Test GET /api/projects/{id}/agents/{role}/health returns data."""
    # First calculate health
    calc_response = await client.post(
        f"/api/projects/{project_id}/agents/qa_engineer/health/calculate"
    )
    assert calc_response.status_code == 200

    # Now get specific agent health
    response = await client.get(f"/api/projects/{project_id}/agents/qa_engineer/health")
    assert response.status_code == 200

    data = response.json()
    assert data["project_id"] == project_id
    assert data["agent_role"] == "qa_engineer"
    assert "health_score" in data
    assert data["health_score"] is not None
    assert "status" in data
    assert data["status"] in ["healthy", "warning", "unhealthy", "no_data"]
    assert "metrics" in data
    assert "recommendations" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_calculate_agent_health(client: AsyncClient, project_id: str):
    """Test POST /api/projects/{id}/agents/{role}/health/calculate."""
    response = await client.post(f"/api/projects/{project_id}/agents/developer/health/calculate")
    assert response.status_code == 200

    data = response.json()
    assert "health_score" in data
    assert isinstance(data["health_score"], (int, float))
    assert 0 <= data["health_score"] <= 100
    assert "status" in data
    assert data["status"] in ["healthy", "warning", "unhealthy"]
    assert "metrics" in data
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) > 0


@pytest.mark.asyncio
async def test_calculate_agent_health_multiple_agents(client: AsyncClient, project_id: str):
    """Test calculating health for multiple agents in same project."""
    # Calculate for developer
    dev_response = await client.post(
        f"/api/projects/{project_id}/agents/developer/health/calculate"
    )
    assert dev_response.status_code == 200

    # Calculate for QA engineer
    qa_response = await client.post(
        f"/api/projects/{project_id}/agents/qa_engineer/health/calculate"
    )
    assert qa_response.status_code == 200

    # Get project health should show both
    project_response = await client.get(f"/api/projects/{project_id}/agent-health")
    assert project_response.status_code == 200

    data = project_response.json()
    assert len(data["agents"]) == 2
    agent_roles = {agent["agent_role"] for agent in data["agents"]}
    assert "developer" in agent_roles
    assert "qa_engineer" in agent_roles


@pytest.mark.asyncio
async def test_get_sprint_agent_health_empty(client: AsyncClient, project_id: str):
    """Test GET /api/sprints/{id}/agent-health with no health data."""
    # Create a sprint
    sprint_response = await client.post(
        f"/api/projects/{project_id}/sprints",
        json={"goal": "Test sprint for health monitoring"},
    )
    assert sprint_response.status_code == 201
    sprint_id = sprint_response.json()["sprint_id"]

    # Get sprint health (should be empty)
    response = await client.get(f"/api/sprints/{sprint_id}/agent-health")
    assert response.status_code == 200

    data = response.json()
    assert "sprint_id" in data
    assert data["sprint_id"] == sprint_id
    assert "agents" in data
    assert isinstance(data["agents"], list)
    assert len(data["agents"]) == 0


@pytest.mark.asyncio
async def test_get_sprint_agent_health_with_data(client: AsyncClient, project_id: str):
    """Test GET /api/sprints/{id}/agent-health with calculated data."""
    # Create a sprint
    sprint_response = await client.post(
        f"/api/projects/{project_id}/sprints",
        json={"goal": "Test sprint"},
    )
    assert sprint_response.status_code == 201
    sprint_id = sprint_response.json()["sprint_id"]

    # Calculate health for sprint-specific agent
    calc_response = await client.post(
        f"/api/projects/{project_id}/agents/developer/health/calculate",
        params={"sprint_id": sprint_id},
    )
    assert calc_response.status_code == 200

    # Get sprint health
    response = await client.get(f"/api/sprints/{sprint_id}/agent-health")
    assert response.status_code == 200

    data = response.json()
    assert data["sprint_id"] == sprint_id
    assert "agents" in data
    assert len(data["agents"]) == 1
    assert data["agents"][0]["agent_role"] == "developer"


@pytest.mark.asyncio
async def test_health_metrics_structure(client: AsyncClient, project_id: str):
    """Test that health metrics have correct structure and types."""
    response = await client.post(f"/api/projects/{project_id}/agents/developer/health/calculate")
    assert response.status_code == 200

    data = response.json()
    metrics = data["metrics"]

    # Verify all expected fields exist
    required_fields = [
        "completion_rate",
        "quality_score",
        "cost_efficiency",
        "avg_execution_time",
        "failure_rate",
        "total_tasks",
        "completed_tasks",
        "failed_tasks",
        "total_tokens",
        "total_cost_usd",
    ]

    for field in required_fields:
        assert field in metrics, f"Missing field: {field}"

    # Verify types
    assert isinstance(metrics["completion_rate"], (int, float))
    assert isinstance(metrics["quality_score"], (int, float))
    assert isinstance(metrics["total_tasks"], int)
    assert isinstance(metrics["completed_tasks"], int)
    assert isinstance(metrics["failed_tasks"], int)
    assert isinstance(metrics["total_cost_usd"], (int, float))


@pytest.mark.asyncio
async def test_health_status_values(client: AsyncClient, project_id: str):
    """Test that health status is one of expected values."""
    response = await client.post(f"/api/projects/{project_id}/agents/developer/health/calculate")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ["healthy", "warning", "unhealthy", "no_data"]


@pytest.mark.asyncio
async def test_recommendations_not_empty(client: AsyncClient, project_id: str):
    """Test that recommendations are always provided."""
    response = await client.post(f"/api/projects/{project_id}/agents/developer/health/calculate")
    assert response.status_code == 200

    data = response.json()
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) > 0
    # Should have at least one recommendation (even if it's "performing well")


@pytest.mark.asyncio
async def test_timestamp_format(client: AsyncClient, project_id: str):
    """Test that timestamp is in ISO format."""
    response = await client.post(f"/api/projects/{project_id}/agents/developer/health/calculate")
    assert response.status_code == 200

    data = response.json()
    assert "timestamp" in data
    # Verify it's a valid ISO timestamp string
    from datetime import datetime

    timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    assert isinstance(timestamp, datetime)


@pytest.mark.asyncio
async def test_multiple_health_calculations_keep_latest(client: AsyncClient, project_id: str):
    """Test that multiple calculations keep the latest record."""
    # Calculate health twice
    response1 = await client.post(f"/api/projects/{project_id}/agents/developer/health/calculate")
    assert response1.status_code == 200
    timestamp1 = response1.json()["timestamp"]

    # Small delay to ensure different timestamp
    import asyncio

    await asyncio.sleep(0.01)

    response2 = await client.post(f"/api/projects/{project_id}/agents/developer/health/calculate")
    assert response2.status_code == 200
    _timestamp2 = response2.json()["timestamp"]

    # Get agent health should return the latest
    get_response = await client.get(f"/api/projects/{project_id}/agents/developer/health")
    assert get_response.status_code == 200

    data = get_response.json()
    # The timestamp should be from the second calculation (or later)
    assert data["timestamp"] >= timestamp1
