"""Tests for sprint endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_sprint(client: AsyncClient, project_id: str):
    resp = await client.post(
        f"/api/projects/{project_id}/sprints",
        json={"goal": "Build a hello world API"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["goal"] == "Build a hello world API"
    assert data["status"] == "created"
    assert data["project_id"] == project_id
    assert data["sprint_number"] == 1


@pytest.mark.asyncio
async def test_create_sprint_project_not_found(client: AsyncClient):
    resp = await client.post(
        "/api/projects/nonexistent/sprints",
        json={"goal": "test"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_sprint_conflict(client: AsyncClient, project_id: str):
    await client.post(
        f"/api/projects/{project_id}/sprints",
        json={"goal": "first sprint"},
    )
    resp = await client.post(
        f"/api/projects/{project_id}/sprints",
        json={"goal": "second sprint"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_sprints(client: AsyncClient, project_id: str):
    await client.post(
        f"/api/projects/{project_id}/sprints",
        json={"goal": "test sprint"},
    )
    resp = await client.get(f"/api/projects/{project_id}/sprints")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["sprints"]) == 1


@pytest.mark.asyncio
async def test_get_sprint(client: AsyncClient, project_id: str):
    create_resp = await client.post(
        f"/api/projects/{project_id}/sprints",
        json={"goal": "test"},
    )
    sprint_id = create_resp.json()["sprint_id"]
    resp = await client.get(f"/api/sprints/{sprint_id}")
    assert resp.status_code == 200
    assert resp.json()["sprint_id"] == sprint_id


@pytest.mark.asyncio
async def test_get_sprint_not_found(client: AsyncClient):
    resp = await client.get("/api/sprints/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_sprint_metrics(client: AsyncClient, project_id: str):
    create_resp = await client.post(
        f"/api/projects/{project_id}/sprints",
        json={"goal": "test"},
    )
    sprint_id = create_resp.json()["sprint_id"]
    resp = await client.get(f"/api/sprints/{sprint_id}/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_tasks"] == 0


@pytest.mark.asyncio
async def test_goal_tree(client: AsyncClient, project_id: str):
    create_resp = await client.post(
        f"/api/projects/{project_id}/sprints",
        json={"goal": "Build a REST API"},
    )
    sprint_id = create_resp.json()["sprint_id"]
    resp = await client.get(f"/api/sprints/{sprint_id}/goal-tree")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["nodes"]) == 1  # Just the goal node (no tasks yet)
    assert data["nodes"][0]["type"] == "goal"
