"""Tests for sprint models."""

from foundrai.models.sprint import SprintMetrics


def test_sprint_metrics_defaults():
    m = SprintMetrics()
    assert m.total_tasks == 0
    assert m.completed_tasks == 0
    assert m.total_tokens == 0


def test_sprint_metrics_completion_rate():
    m = SprintMetrics(total_tasks=10, completed_tasks=7)
    assert m.completion_rate == 0.7


def test_sprint_metrics_zero_tasks():
    m = SprintMetrics(total_tasks=0, completed_tasks=0)
    assert m.completion_rate == 0.0  # Not division by zero


def test_sprint_metrics_full_completion():
    m = SprintMetrics(total_tasks=5, completed_tasks=5)
    assert m.completion_rate == 1.0
