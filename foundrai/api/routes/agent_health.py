"""Agent health and quality monitoring API routes."""

from __future__ import annotations

from fastapi import APIRouter

from foundrai.api.deps import get_db
from foundrai.persistence.agent_health_store import AgentHealthStore

router = APIRouter()


async def _get_health_store() -> AgentHealthStore:
    db = await get_db()
    return AgentHealthStore(db)


# --- Agent Health Routes ---


@router.get("/projects/{project_id}/agent-health")
async def get_project_agent_health(project_id: str) -> dict:
    """Get health metrics for all agents in a project."""
    store = await _get_health_store()
    health_records = await store.get_project_health(project_id)

    return {
        "project_id": project_id,
        "agents": [
            {
                "agent_role": h.agent_role,
                "health_score": h.health_score,
                "status": h.status,
                "metrics": {
                    "completion_rate": h.metrics.completion_rate,
                    "quality_score": h.metrics.quality_score,
                    "cost_efficiency": h.metrics.cost_efficiency,
                    "avg_execution_time": h.metrics.avg_execution_time,
                    "failure_rate": h.metrics.failure_rate,
                    "total_tasks": h.metrics.total_tasks,
                    "completed_tasks": h.metrics.completed_tasks,
                    "failed_tasks": h.metrics.failed_tasks,
                    "total_tokens": h.metrics.total_tokens,
                    "total_cost_usd": h.metrics.total_cost_usd,
                },
                "recommendations": h.recommendations,
                "timestamp": h.timestamp.isoformat(),
            }
            for h in health_records
        ],
    }


@router.get("/projects/{project_id}/agents/{agent_role}/health")
async def get_agent_health(project_id: str, agent_role: str) -> dict:
    """Get health metrics for a specific agent in a project."""
    store = await _get_health_store()
    health = await store.get_agent_health(agent_role, project_id)

    if not health:
        return {
            "project_id": project_id,
            "agent_role": agent_role,
            "health_score": None,
            "status": "no_data",
            "message": "No health data available for this agent.",
        }

    return {
        "project_id": project_id,
        "agent_role": health.agent_role,
        "health_score": health.health_score,
        "status": health.status,
        "metrics": {
            "completion_rate": health.metrics.completion_rate,
            "quality_score": health.metrics.quality_score,
            "cost_efficiency": health.metrics.cost_efficiency,
            "avg_execution_time": health.metrics.avg_execution_time,
            "failure_rate": health.metrics.failure_rate,
            "total_tasks": health.metrics.total_tasks,
            "completed_tasks": health.metrics.completed_tasks,
            "failed_tasks": health.metrics.failed_tasks,
            "total_tokens": health.metrics.total_tokens,
            "total_cost_usd": health.metrics.total_cost_usd,
        },
        "recommendations": health.recommendations,
        "timestamp": health.timestamp.isoformat(),
    }


@router.get("/sprints/{sprint_id}/agent-health")
async def get_sprint_agent_health(sprint_id: str) -> dict:
    """Get health metrics for all agents in a sprint."""
    store = await _get_health_store()
    health_records = await store.get_sprint_health(sprint_id)

    return {
        "sprint_id": sprint_id,
        "agents": [
            {
                "agent_role": h.agent_role,
                "health_score": h.health_score,
                "status": h.status,
                "metrics": {
                    "completion_rate": h.metrics.completion_rate,
                    "quality_score": h.metrics.quality_score,
                    "cost_efficiency": h.metrics.cost_efficiency,
                    "avg_execution_time": h.metrics.avg_execution_time,
                    "failure_rate": h.metrics.failure_rate,
                    "total_tasks": h.metrics.total_tasks,
                    "completed_tasks": h.metrics.completed_tasks,
                    "failed_tasks": h.metrics.failed_tasks,
                    "total_tokens": h.metrics.total_tokens,
                    "total_cost_usd": h.metrics.total_cost_usd,
                },
                "recommendations": h.recommendations,
                "timestamp": h.timestamp.isoformat(),
            }
            for h in health_records
        ],
    }


@router.post("/projects/{project_id}/agents/{agent_role}/health/calculate")
async def calculate_agent_health(
    project_id: str, agent_role: str, sprint_id: str | None = None
) -> dict:
    """Calculate and save health metrics for a specific agent."""
    store = await _get_health_store()
    health = await store.calculate_health_score(agent_role, project_id, sprint_id)

    return {
        "project_id": project_id,
        "agent_role": health.agent_role,
        "sprint_id": health.sprint_id,
        "health_score": health.health_score,
        "status": health.status,
        "metrics": {
            "completion_rate": health.metrics.completion_rate,
            "quality_score": health.metrics.quality_score,
            "cost_efficiency": health.metrics.cost_efficiency,
            "avg_execution_time": health.metrics.avg_execution_time,
            "failure_rate": health.metrics.failure_rate,
            "total_tasks": health.metrics.total_tasks,
            "completed_tasks": health.metrics.completed_tasks,
            "failed_tasks": health.metrics.failed_tasks,
            "total_tokens": health.metrics.total_tokens,
            "total_cost_usd": health.metrics.total_cost_usd,
        },
        "recommendations": health.recommendations,
        "timestamp": health.timestamp.isoformat(),
    }
