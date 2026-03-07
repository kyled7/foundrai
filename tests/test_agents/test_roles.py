"""Tests for agent roles."""

import pytest

from foundrai.agents.roles import ROLE_REGISTRY, get_role
from foundrai.models.enums import AgentRoleName


def test_default_roles_registered():
    assert AgentRoleName.PRODUCT_MANAGER in ROLE_REGISTRY
    assert AgentRoleName.DEVELOPER in ROLE_REGISTRY
    assert AgentRoleName.QA_ENGINEER in ROLE_REGISTRY
    assert AgentRoleName.ARCHITECT in ROLE_REGISTRY
    assert AgentRoleName.DESIGNER in ROLE_REGISTRY
    assert AgentRoleName.DEVOPS in ROLE_REGISTRY


def test_get_role_not_found():
    with pytest.raises(KeyError):
        get_role("nonexistent_role")  # type: ignore[arg-type]
