"""Model recommendation API routes."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from foundrai.api.deps import get_db, get_event_log
from foundrai.models.enums import AgentRoleName
from foundrai.models.recommendation import TaskComplexity
from foundrai.orchestration.recommendation_engine import RecommendationEngine
from foundrai.persistence.recommendation_store import RecommendationStore

router = APIRouter()


async def _get_recommendation_engine() -> RecommendationEngine:
    """Get recommendation engine instance."""
    db = await get_db()
    event_log = await get_event_log()
    recommendation_store = RecommendationStore(db)
    return RecommendationEngine(recommendation_store, db, event_log)


# --- Recommendation routes ---


@router.get("/projects/{project_id}/recommendations")
async def get_project_recommendations(project_id: str) -> dict:
    """Get model recommendations for all agent roles in a project."""
    engine = await _get_recommendation_engine()
    recommendations = await engine.get_all_recommendations(project_id)

    return {
        "project_id": project_id,
        "recommendations": [
            {
                "agent_role": rec.agent_role,
                "recommended_model": rec.recommended_model,
                "current_model": rec.current_model,
                "confidence": rec.confidence,
                "reasoning": rec.reasoning,
                "expected_quality_score": rec.expected_quality_score,
                "expected_cost_per_task": rec.expected_cost_per_task,
                "expected_success_rate": rec.expected_success_rate,
                "alternative_models": rec.alternative_models,
                "task_complexity": rec.task_complexity,
                "quality_requirements": rec.quality_requirements,
                "cost_constraints": rec.cost_constraints,
            }
            for rec in recommendations
        ],
    }


class RecommendationRequest(BaseModel):
    current_model: str | None = None
    task_complexity: TaskComplexity | None = None
    quality_requirements: str | None = None
    cost_constraints: float | None = None


@router.post("/projects/{project_id}/recommendations/{agent_role}")
async def get_agent_recommendation(
    project_id: str, agent_role: str, body: RecommendationRequest | None = None
) -> dict:
    """Get model recommendation for a specific agent role with optional constraints."""
    engine = await _get_recommendation_engine()

    # Parse agent role
    try:
        role = AgentRoleName(agent_role)
    except ValueError:
        return {"error": f"Invalid agent role: {agent_role}"}

    # Get recommendation with optional constraints
    if body:
        recommendation = await engine.get_recommendation(
            project_id,
            role,
            current_model=body.current_model,
            task_complexity=body.task_complexity,
            quality_requirements=body.quality_requirements,
            cost_constraints=body.cost_constraints,
        )
    else:
        recommendation = await engine.get_recommendation(project_id, role)

    return {
        "project_id": project_id,
        "agent_role": recommendation.agent_role,
        "recommended_model": recommendation.recommended_model,
        "current_model": recommendation.current_model,
        "confidence": recommendation.confidence,
        "reasoning": recommendation.reasoning,
        "expected_quality_score": recommendation.expected_quality_score,
        "expected_cost_per_task": recommendation.expected_cost_per_task,
        "expected_success_rate": recommendation.expected_success_rate,
        "alternative_models": recommendation.alternative_models,
        "performance_metrics": recommendation.performance_metrics.dict() if recommendation.performance_metrics else None,
    }


# --- Cost savings routes ---


class CostSavingsRequest(BaseModel):
    current_config: dict[str, str] = Field(
        description="Dict mapping agent_role to current model"
    )
    recommended_config: dict[str, str] | None = Field(
        default=None, description="Dict mapping agent_role to recommended model (optional)"
    )


@router.post("/projects/{project_id}/cost-savings")
async def calculate_cost_savings(
    project_id: str, body: CostSavingsRequest
) -> dict:
    """Calculate potential cost savings from recommended model configuration."""
    engine = await _get_recommendation_engine()

    estimate = await engine.calculate_cost_savings(
        project_id,
        body.current_config,
        body.recommended_config,
    )

    return {
        "project_id": estimate.project_id,
        "current_total_cost": estimate.current_total_cost,
        "current_config": estimate.current_config,
        "recommended_total_cost": estimate.recommended_total_cost,
        "recommended_config": estimate.recommended_config,
        "total_savings_usd": estimate.total_savings_usd,
        "savings_percentage": estimate.savings_percentage,
        "role_breakdown": estimate.role_breakdown,
        "quality_impact": estimate.quality_impact,
        "quality_score_change": estimate.quality_score_change,
        "based_on_tasks": estimate.based_on_tasks,
        "confidence": estimate.confidence,
    }


# --- Model comparison routes ---


@router.get("/projects/{project_id}/model-comparison/{agent_role}")
async def compare_models_for_role(project_id: str, agent_role: str) -> dict:
    """Compare all models used by an agent role."""
    engine = await _get_recommendation_engine()

    # Parse agent role
    try:
        role = AgentRoleName(agent_role)
    except ValueError:
        return {"error": f"Invalid agent role: {agent_role}"}

    comparison = await engine.compare_models(project_id, role)

    return {
        "project_id": comparison.project_id,
        "agent_role": comparison.agent_role,
        "models": [
            {
                "model": m.model,
                "total_tasks": m.total_tasks,
                "success_rate": m.success_rate,
                "avg_cost_per_task": m.avg_cost_per_task,
                "total_cost": m.total_cost,
                "quality_score": m.quality_score,
            }
            for m in comparison.models
        ],
        "best_for_quality": comparison.best_for_quality,
        "best_for_cost": comparison.best_for_cost,
        "best_overall": comparison.best_overall,
    }
