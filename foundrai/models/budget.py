"""Budget configuration and status models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BudgetConfig:
    """Budget configuration for a sprint or agent."""

    sprint_budget_usd: float = 0.0  # 0 = unlimited
    agent_budgets: dict[str, float] = field(default_factory=dict)


@dataclass
class BudgetStatus:
    """Current budget status."""

    budget_usd: float
    spent_usd: float
    remaining_usd: float
    percentage_used: float
    is_warning: bool  # >80%
    is_exceeded: bool  # >100%
