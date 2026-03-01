"""Tests for BaseAgent."""

from foundrai.agents.roles import get_role
from foundrai.models.enums import AgentRoleName


def test_role_registry_has_defaults():
    pm = get_role(AgentRoleName.PRODUCT_MANAGER)
    assert pm.display_name == "Product Manager"

    dev = get_role(AgentRoleName.DEVELOPER)
    assert dev.display_name == "Developer"

    qa = get_role(AgentRoleName.QA_ENGINEER)
    assert qa.display_name == "QA Engineer"


def test_role_has_tools():
    dev = get_role(AgentRoleName.DEVELOPER)
    assert "file_manager" in dev.tools
    assert "code_executor" in dev.tools


def test_role_has_persona():
    pm = get_role(AgentRoleName.PRODUCT_MANAGER)
    assert len(pm.persona) > 50  # Should have substantial persona text
