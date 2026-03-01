"""Tests for configuration loading."""

import pytest

from foundrai.config import FoundrAIConfig, load_config


def test_load_default_config(tmp_path):
    yaml_content = "project:\n  name: test\n"
    (tmp_path / "foundrai.yaml").write_text(yaml_content)
    config = load_config(str(tmp_path))
    assert config.project.name == "test"
    assert config.team.developer.model == "anthropic/claude-sonnet-4-20250514"


def test_load_full_config(tmp_path):
    yaml_content = """
project:
  name: myapp
  description: A test project
team:
  product_manager:
    enabled: true
    model: anthropic/claude-sonnet-4-20250514
  developer:
    enabled: true
    model: openai/gpt-4o
sprint:
  token_budget: 50000
"""
    (tmp_path / "foundrai.yaml").write_text(yaml_content)
    config = load_config(str(tmp_path))
    assert config.project.name == "myapp"
    assert config.sprint.token_budget == 50000


def test_missing_config():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent_dir_12345")


def test_empty_yaml(tmp_path):
    (tmp_path / "foundrai.yaml").write_text("")
    config = load_config(str(tmp_path))
    assert config.project.name == "my-project"  # default


def test_config_defaults():
    config = FoundrAIConfig()
    assert config.persistence.database == "sqlite"
    assert config.sandbox.timeout_seconds == 30
    assert config.sprint.max_sprints == 5
