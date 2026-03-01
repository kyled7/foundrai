"""Tests for FoundrAI enums."""

from foundrai.models.enums import (
    AgentRoleName,
    AutonomyLevel,
    MessageType,
    SprintStatus,
    TaskStatus,
)


def test_sprint_status_values():
    assert SprintStatus.CREATED == "created"
    assert SprintStatus.COMPLETED == "completed"
    assert SprintStatus.FAILED == "failed"


def test_task_status_values():
    assert TaskStatus.BACKLOG == "backlog"
    assert TaskStatus.IN_PROGRESS == "in_progress"
    assert TaskStatus.DONE == "done"


def test_agent_role_names():
    assert AgentRoleName.PRODUCT_MANAGER == "product_manager"
    assert AgentRoleName.DEVELOPER == "developer"
    assert AgentRoleName.QA_ENGINEER == "qa_engineer"


def test_autonomy_level_values():
    assert AutonomyLevel.AUTO_APPROVE == "auto_approve"
    assert AutonomyLevel.BLOCK == "block"


def test_message_type_values():
    assert MessageType.TASK_ASSIGNMENT == "task_assignment"
    assert MessageType.GOAL_DECOMPOSITION == "goal_decomposition"
