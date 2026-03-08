"""Agent factory — creates agent instances from config.

Extracted from CLI so the API layer can also spawn agents for sprint execution.
"""

from __future__ import annotations

from typing import Any

from foundrai.agents.context import SprintContext
from foundrai.agents.llm import LLMClient, LLMConfig
from foundrai.agents.personas.developer import DeveloperAgent
from foundrai.agents.personas.product_manager import ProductManagerAgent
from foundrai.agents.personas.qa_engineer import QAEngineerAgent
from foundrai.agents.roles import get_role
from foundrai.agents.runtime import AgentRuntime
from foundrai.config import FoundrAIConfig
from foundrai.models.enums import AgentRoleName
from foundrai.orchestration.message_bus import MessageBus
from foundrai.persistence.event_log import EventLog


def create_agents(
    config: FoundrAIConfig,
    sprint_context: SprintContext,
    message_bus: MessageBus,
    event_log: EventLog,
    token_store: Any | None = None,
    budget_manager: Any | None = None,
    trace_store: Any | None = None,
    sprint_id: str = "",
    project_id: str = "",
) -> dict[str, Any]:
    """Create agent instances from team configuration.

    Returns a dict mapping agent role name (str) to agent instance.
    """
    agents: dict[str, Any] = {}

    role_map: list[tuple[str, Any, type]] = [
        (AgentRoleName.PRODUCT_MANAGER.value, config.team.product_manager, ProductManagerAgent),
        (AgentRoleName.DEVELOPER.value, config.team.developer, DeveloperAgent),
        (AgentRoleName.QA_ENGINEER.value, config.team.qa_engineer, QAEngineerAgent),
    ]

    for role_name, agent_config, agent_class in role_map:
        if not agent_config.enabled:
            continue

        llm = LLMClient(LLMConfig(model=agent_config.model))
        runtime = AgentRuntime(
            llm_client=llm,
            event_log=event_log,
            token_store=token_store,
            budget_manager=budget_manager,
            trace_store=trace_store,
            agent_role=role_name,
            sprint_id=sprint_id,
            project_id=project_id,
        )
        agent = agent_class(
            role=get_role(AgentRoleName(role_name)),
            model=agent_config.model,
            tools=[],
            message_bus=message_bus,
            sprint_context=sprint_context,
            runtime=runtime,
        )
        agents[role_name] = agent
        message_bus.register_agent(role_name)

    return agents
