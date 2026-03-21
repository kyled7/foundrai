"""Model recommendation engine for optimal LLM assignments."""

from __future__ import annotations

import logging

from foundrai.models.enums import AgentRoleName
from foundrai.models.recommendation import (
    CostSavingsEstimate,
    ModelPerformanceComparison,
    ModelRecommendation,
    PerformanceMetrics,
    RecommendationConfidence,
    TaskComplexity,
)
from foundrai.persistence.database import Database
from foundrai.persistence.event_log import EventLog
from foundrai.persistence.recommendation_store import RecommendationStore

logger = logging.getLogger(__name__)


# Default model recommendations by role when no historical data exists
DEFAULT_ROLE_RECOMMENDATIONS = {
    AgentRoleName.PRODUCT_MANAGER: "claude-sonnet-4",  # Best at planning/writing
    AgentRoleName.ARCHITECT: "claude-sonnet-4",  # Complex technical decisions
    AgentRoleName.DEVELOPER: "gpt-4o",  # Best at code generation
    AgentRoleName.QA_ENGINEER: "gpt-4o-mini",  # Good for formatting, cheaper
    AgentRoleName.DESIGNER: "claude-sonnet-4",  # Creative tasks
    AgentRoleName.DEVOPS: "gpt-4o-mini",  # Script generation, config
}


class RecommendationEngine:
    """Generates intelligent model recommendations for agent roles."""

    def __init__(
        self,
        recommendation_store: RecommendationStore,
        db: Database,
        event_log: EventLog,
    ) -> None:
        self.store = recommendation_store
        self.db = db
        self.event_log = event_log

    async def get_recommendation(
        self,
        project_id: str,
        agent_role: AgentRoleName,
        current_model: str | None = None,
        task_complexity: TaskComplexity | None = None,
        quality_requirements: str | None = None,
        cost_constraints: float | None = None,
    ) -> ModelRecommendation:
        """Generate a model recommendation for an agent role.

        Args:
            project_id: The project ID
            agent_role: The agent role to recommend for
            current_model: Currently configured model (optional)
            task_complexity: Task complexity level (optional)
            quality_requirements: Quality requirements (optional)
            cost_constraints: Max budget per task in USD (optional)

        Returns:
            ModelRecommendation with suggested model and reasoning
        """
        # Get historical performance data
        performance_data = await self.store.get_agent_performance(project_id, agent_role)

        # Determine confidence based on available data
        confidence = self._calculate_confidence(performance_data)

        if confidence == RecommendationConfidence.INSUFFICIENT_DATA:
            # Use default recommendations when no historical data
            return await self._default_recommendation(
                project_id,
                agent_role,
                current_model,
                task_complexity,
                quality_requirements,
                cost_constraints,
            )

        # Analyze performance data to make recommendation
        recommended_model, reasoning, metrics = await self._analyze_performance(
            project_id,
            agent_role,
            performance_data,
            cost_constraints,
            quality_requirements,
        )

        # Get alternative models
        alternative_models = [m.model for m in performance_data if m.model != recommended_model][:3]

        recommendation = ModelRecommendation(
            project_id=project_id,
            agent_role=agent_role,
            recommended_model=recommended_model,
            current_model=current_model,
            confidence=confidence,
            reasoning=reasoning,
            expected_quality_score=metrics.quality_score if metrics else 0.0,
            expected_cost_per_task=metrics.avg_cost_per_task if metrics else 0.0,
            expected_success_rate=metrics.success_rate if metrics else 0.0,
            performance_metrics=metrics,
            alternative_models=alternative_models,
            task_complexity=task_complexity,
            quality_requirements=quality_requirements,
            cost_constraints=cost_constraints,
        )

        # Log recommendation event
        await self.event_log.append(
            "model_recommendation_generated",
            {
                "project_id": project_id,
                "agent_role": agent_role,
                "recommended_model": recommended_model,
                "current_model": current_model,
                "confidence": confidence,
            },
        )

        return recommendation

    async def get_all_recommendations(
        self, project_id: str, current_config: dict[str, str] | None = None
    ) -> list[ModelRecommendation]:
        """Get recommendations for all agent roles in a project.

        Args:
            project_id: The project ID
            current_config: Dict mapping agent_role to current model (optional)

        Returns:
            List of ModelRecommendation for each role
        """
        recommendations = []
        current_config = current_config or {}

        for role in AgentRoleName:
            current_model = current_config.get(role.value)
            recommendation = await self.get_recommendation(project_id, role, current_model)
            recommendations.append(recommendation)

        return recommendations

    async def calculate_cost_savings(
        self,
        project_id: str,
        current_config: dict[str, str],
        recommended_config: dict[str, str] | None = None,
    ) -> CostSavingsEstimate:
        """Calculate potential cost savings from recommended model configuration.

        Args:
            project_id: The project ID
            current_config: Dict mapping agent_role to current model
            recommended_config: Dict mapping agent_role to recommended model (optional, will be generated)

        Returns:
            CostSavingsEstimate with savings analysis
        """
        # Generate recommended config if not provided
        if recommended_config is None:
            recommendations = await self.get_all_recommendations(project_id, current_config)
            recommended_config = {rec.agent_role: rec.recommended_model for rec in recommendations}

        # Calculate costs for each configuration
        current_total = 0.0
        recommended_total = 0.0
        role_breakdown: dict[str, dict[str, float]] = {}
        total_tasks = 0

        for role_str, current_model in current_config.items():
            try:
                role = AgentRoleName(role_str)
            except ValueError:
                logger.warning("Invalid agent role: %s", role_str)
                continue

            # Get performance metrics for current and recommended models
            performance_data = await self.store.get_agent_performance(project_id, role)

            current_metrics = next((m for m in performance_data if m.model == current_model), None)
            recommended_model = recommended_config.get(role_str, current_model)
            recommended_metrics = next(
                (m for m in performance_data if m.model == recommended_model), None
            )

            # Calculate costs based on historical data
            current_cost = current_metrics.avg_cost_per_task if current_metrics else 0.0
            recommended_cost = recommended_metrics.avg_cost_per_task if recommended_metrics else 0.0

            current_total += current_cost
            recommended_total += recommended_cost

            if current_metrics:
                total_tasks += current_metrics.total_tasks

            role_breakdown[role_str] = {
                "current_cost": current_cost,
                "recommended_cost": recommended_cost,
                "savings": current_cost - recommended_cost,
            }

        # Calculate overall savings
        total_savings = current_total - recommended_total
        savings_pct = (total_savings / current_total * 100.0) if current_total > 0 else 0.0

        # Determine quality impact (simplified - could be enhanced)
        quality_impact = "neutral"
        quality_score_change = 0.0
        if savings_pct > 10:
            quality_impact = "improved"  # Assuming better models = better quality
            quality_score_change = 5.0
        elif savings_pct < -10:
            quality_impact = "degraded"
            quality_score_change = -5.0

        # Calculate confidence
        confidence = (
            RecommendationConfidence.HIGH
            if total_tasks >= 30
            else (
                RecommendationConfidence.MEDIUM
                if total_tasks >= 10
                else RecommendationConfidence.LOW
            )
        )

        estimate = CostSavingsEstimate(
            project_id=project_id,
            current_total_cost=current_total,
            current_config=current_config,
            recommended_total_cost=recommended_total,
            recommended_config=recommended_config,
            total_savings_usd=total_savings,
            savings_percentage=savings_pct,
            role_breakdown=role_breakdown,
            quality_impact=quality_impact,
            quality_score_change=quality_score_change,
            based_on_tasks=total_tasks,
            confidence=confidence,
        )

        # Log savings estimate event
        await self.event_log.append(
            "cost_savings_estimated",
            {
                "project_id": project_id,
                "total_savings_usd": total_savings,
                "savings_percentage": savings_pct,
                "confidence": confidence,
            },
        )

        return estimate

    async def compare_models(
        self, project_id: str, agent_role: AgentRoleName
    ) -> ModelPerformanceComparison:
        """Compare all models used by an agent role.

        Args:
            project_id: The project ID
            agent_role: The agent role to compare models for

        Returns:
            ModelPerformanceComparison with best models identified
        """
        performance_data = await self.store.get_agent_performance(project_id, agent_role)

        if not performance_data:
            return ModelPerformanceComparison(
                agent_role=agent_role, project_id=project_id, models=[]
            )

        # Identify best models
        best_for_quality = await self.store.get_best_performing_model(project_id, agent_role)
        best_for_cost = await self.store.get_most_cost_efficient_model(project_id, agent_role)

        # Determine best overall (balance quality and cost)
        best_overall = self._determine_best_overall(performance_data)

        comparison = ModelPerformanceComparison(
            agent_role=agent_role,
            project_id=project_id,
            models=performance_data,
            best_for_quality=best_for_quality,
            best_for_cost=best_for_cost,
            best_overall=best_overall,
        )

        return comparison

    def _calculate_confidence(
        self, performance_data: list[PerformanceMetrics]
    ) -> RecommendationConfidence:
        """Calculate confidence level based on available data."""
        if not performance_data:
            return RecommendationConfidence.INSUFFICIENT_DATA

        total_tasks = sum(m.total_tasks for m in performance_data)

        if total_tasks >= 50:
            return RecommendationConfidence.HIGH
        elif total_tasks >= 20:
            return RecommendationConfidence.MEDIUM
        elif total_tasks >= 5:
            return RecommendationConfidence.LOW
        else:
            return RecommendationConfidence.INSUFFICIENT_DATA

    async def _default_recommendation(
        self,
        project_id: str,
        agent_role: AgentRoleName,
        current_model: str | None,
        task_complexity: TaskComplexity | None,
        quality_requirements: str | None,
        cost_constraints: float | None,
    ) -> ModelRecommendation:
        """Provide default recommendation when insufficient historical data."""
        recommended_model = DEFAULT_ROLE_RECOMMENDATIONS.get(agent_role, "gpt-4o-mini")

        # Adjust based on task complexity if provided
        if task_complexity == TaskComplexity.CRITICAL:
            recommended_model = "claude-opus-4"  # Most capable
        elif task_complexity == TaskComplexity.SIMPLE:
            recommended_model = "gpt-4o-mini"  # Most cost-effective

        # Adjust based on cost constraints
        if cost_constraints is not None and cost_constraints < 0.01:
            recommended_model = "gpt-4o-mini"  # Cheapest option

        reasoning = f"Default recommendation for {agent_role} (insufficient historical data). "
        if task_complexity:
            reasoning += f"Adjusted for {task_complexity} task complexity. "
        if cost_constraints:
            reasoning += f"Considering cost constraint of ${cost_constraints:.4f} per task."

        return ModelRecommendation(
            project_id=project_id,
            agent_role=agent_role,
            recommended_model=recommended_model,
            current_model=current_model,
            confidence=RecommendationConfidence.INSUFFICIENT_DATA,
            reasoning=reasoning,
            task_complexity=task_complexity,
            quality_requirements=quality_requirements,
            cost_constraints=cost_constraints,
        )

    async def _analyze_performance(
        self,
        project_id: str,
        agent_role: AgentRoleName,
        performance_data: list[PerformanceMetrics],
        cost_constraints: float | None,
        quality_requirements: str | None,
    ) -> tuple[str, str, PerformanceMetrics | None]:
        """Analyze performance data to determine best model.

        Returns:
            Tuple of (recommended_model, reasoning, metrics)
        """
        if not performance_data:
            default_model = DEFAULT_ROLE_RECOMMENDATIONS.get(agent_role, "gpt-4o-mini")
            return default_model, "No performance data available", None

        # Filter viable models (success rate >= 60%, at least 3 tasks)
        viable_models = [
            m for m in performance_data if m.success_rate >= 60.0 and m.total_tasks >= 3
        ]

        if not viable_models:
            # Fall back to best available
            best = max(performance_data, key=lambda m: m.success_rate)
            return (
                best.model,
                f"Limited data available. {best.model} has highest success rate ({best.success_rate:.1f}%).",
                best,
            )

        # Apply cost constraints if specified
        if cost_constraints is not None:
            constrained = [m for m in viable_models if m.avg_cost_per_task <= cost_constraints]
            if constrained:
                viable_models = constrained

        # Apply quality requirements
        if quality_requirements == "high":
            # Prefer high success rate
            best = max(viable_models, key=lambda m: (m.success_rate, -m.avg_cost_per_task))
            reasoning = f"{best.model} recommended for high quality requirements (success rate: {best.success_rate:.1f}%, avg cost: ${best.avg_cost_per_task:.4f})."
        elif quality_requirements == "low":
            # Prefer low cost
            best = min(viable_models, key=lambda m: (m.avg_cost_per_task, -m.success_rate))
            reasoning = f"{best.model} recommended for cost optimization (avg cost: ${best.avg_cost_per_task:.4f}, success rate: {best.success_rate:.1f}%)."
        else:
            # Balance quality and cost
            best = self._determine_best_overall(viable_models)
            metrics = next((m for m in viable_models if m.model == best), None)
            if metrics:
                reasoning = f"{best} recommended based on balanced performance (success rate: {metrics.success_rate:.1f}%, avg cost: ${metrics.avg_cost_per_task:.4f})."
            else:
                reasoning = f"{best} recommended based on historical performance."

        best_metrics = next((m for m in viable_models if m.model == best), None)
        return best, reasoning, best_metrics

    def _determine_best_overall(self, performance_data: list[PerformanceMetrics]) -> str | None:
        """Determine best overall model balancing quality and cost.

        Uses a simple scoring formula: score = success_rate / (avg_cost * 1000)
        This rewards high success rate and low cost.
        """
        if not performance_data:
            return None

        # Calculate composite score
        scored = []
        for m in performance_data:
            if m.avg_cost_per_task > 0:
                # Normalize: success_rate (0-100) / (cost in USD * 1000)
                # Higher success rate and lower cost = better score
                score = m.success_rate / (m.avg_cost_per_task * 1000.0)
                scored.append((m.model, score))

        if not scored:
            # Fall back to best success rate
            best = max(performance_data, key=lambda m: m.success_rate)
            return best.model

        # Return model with highest composite score
        best_model = max(scored, key=lambda x: x[1])
        return best_model[0]
