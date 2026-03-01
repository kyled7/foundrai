"""Tests for project endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    resp = await client.post("/api/projects", json={"name": "my-project", "description": "A test"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "my-project"
    assert data["description"] == "A test"
    assert data["project_id"]
    assert data["sprint_count"] == 0


@pytest.mark.asyncio
async def test_create_project_validation(client: AsyncClient):
    resp = await client.post("/api/projects", json={"name": ""})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient):
    await client.post("/api/projects", json={"name": "p1"})
    await client.post("/api/projects", json={"name": "p2"})
    resp = await client.get("/api/projects")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["projects"]) == 2


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient, project_id: str):
    resp = await client.get(f"/api/projects/{project_id}")
    assert resp.status_code == 200
    assert resp.json()["project_id"] == project_id


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient):
    resp = await client.get("/api/projects/nonexistent")
    assert resp.status_code == 404
