"""Tests for task models."""

from foundrai.models.enums import AgentRoleName, TaskStatus
from foundrai.models.task import ReviewResult, Task, TaskResult


def test_task_default_status():
    task = Task(title="test", description="test desc")
    assert task.status == TaskStatus.BACKLOG


def test_task_default_priority():
    task = Task(title="test", description="test desc")
    assert task.priority == 3


def test_task_default_assigned_to():
    task = Task(title="test", description="test desc")
    assert task.assigned_to == AgentRoleName.DEVELOPER


def test_task_with_acceptance_criteria():
    task = Task(
        title="test",
        description="desc",
        acceptance_criteria=["criterion 1", "criterion 2"],
    )
    assert len(task.acceptance_criteria) == 2


def test_task_result():
    result = TaskResult(
        task_id="t1",
        agent_id="developer",
        success=True,
        output="Done",
        tokens_used=100,
    )
    assert result.success
    assert result.tokens_used == 100


def test_review_result_passed():
    review = ReviewResult(
        task_id="t1",
        reviewer_id="qa_engineer",
        passed=True,
    )
    assert review.passed
    assert review.issues == []


def test_review_result_failed():
    review = ReviewResult(
        task_id="t1",
        reviewer_id="qa_engineer",
        passed=False,
        issues=["Bug found"],
        suggestions=["Fix the bug"],
    )
    assert not review.passed
    assert len(review.issues) == 1
