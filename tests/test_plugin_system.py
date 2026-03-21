"""Tests for the plugin system."""

from __future__ import annotations

from pathlib import Path

import pytest

from foundrai.models.plugin import Plugin, PluginType, RolePluginSpec
from foundrai.plugins.loader import PluginLoader
from foundrai.plugins.registry import PluginRegistry


class TestPluginLoader:
    """Test plugin loader functionality."""

    def test_discover_valid_plugins(self, tmp_path: Path):
        """Test plugin discovery finds valid plugins."""
        # Create test plugin structure
        plugin_dir = tmp_path / "plugins"
        test_plugin = plugin_dir / "test-plugin"
        test_plugin.mkdir(parents=True)

        # Create plugin.yaml
        plugin_config = {
            "name": "test-plugin",
            "version": "1.0.0",
            "type": "role",
            "author": "test",
            "description": "Test plugin",
            "role": {
                "name": "TestRole",
                "persona": "You are a test role",
                "skills": ["testing"],
                "tools": ["test_tool"],
                "default_model": "test-model",
            },
        }

        with open(test_plugin / "plugin.yaml", "w") as f:
            import yaml

            yaml.dump(plugin_config, f)

        # Test discovery
        loader = PluginLoader(plugin_dir)
        discovered = loader.discover_plugins()

        assert len(discovered) == 1
        assert discovered[0]["name"] == "test-plugin"
        assert discovered[0]["version"] == "1.0.0"

    def test_load_role_plugin(self, tmp_path: Path):
        """Test loading a role plugin."""
        # Create test plugin structure
        plugin_dir = tmp_path / "plugins"
        test_plugin = plugin_dir / "test-role"
        test_plugin.mkdir(parents=True)

        plugin_config = {
            "name": "test-role",
            "version": "1.0.0",
            "type": "role",
            "author": "test",
            "description": "Test role plugin",
            "role": {
                "name": "TestRole",
                "persona": "You are a test role for testing purposes",
                "skills": ["testing", "validation"],
                "tools": ["file_manager"],
                "default_model": "anthropic/claude-sonnet-4-20250514",
            },
        }

        with open(test_plugin / "plugin.yaml", "w") as f:
            import yaml

            yaml.dump(plugin_config, f)

        # Load plugin
        loader = PluginLoader(plugin_dir)
        plugin = loader.load_plugin("test-role")

        assert plugin.name == "test-role"
        assert plugin.plugin_type == PluginType.ROLE
        assert plugin.role_spec is not None
        assert plugin.role_spec.name == "TestRole"
        assert "testing" in plugin.role_spec.skills

    def test_plugin_validation_valid(self):
        """Test plugin validation with valid plugin."""
        plugin = Plugin(
            name="valid-plugin",
            version="1.0.0",
            plugin_type=PluginType.ROLE,
            role_spec=RolePluginSpec(
                name="ValidRole",
                persona="Test persona",
                skills=["test"],
                tools=["file_manager"],
                default_model="test-model",
            ),
        )

        loader = PluginLoader()
        result = loader.validate_plugin(plugin)

        assert result.valid
        assert len(result.errors) == 0

    def test_plugin_validation_missing_spec(self):
        """Test plugin validation with missing spec."""
        plugin = Plugin(
            name="invalid-plugin",
            version="1.0.0",
            plugin_type=PluginType.ROLE,
            role_spec=None,  # Missing required spec
        )

        loader = PluginLoader()
        result = loader.validate_plugin(plugin)

        assert not result.valid
        assert "Role plugin missing role_spec" in result.errors

    def test_plugin_validation_invalid_version(self):
        """Test plugin validation with invalid version."""
        plugin = Plugin(
            name="test-plugin",
            version="invalid-version",  # Invalid version format
            plugin_type=PluginType.ROLE,
            role_spec=RolePluginSpec(
                name="TestRole",
                persona="Test",
                skills=["test"],
                tools=["file_manager"],
                default_model="test-model",
            ),
        )

        loader = PluginLoader()
        result = loader.validate_plugin(plugin)

        assert result.valid  # Warnings don't make plugin invalid
        assert len(result.warnings) > 0
        assert "semantic versioning format" in result.warnings[0]


class TestPluginRegistry:
    """Test plugin registry functionality."""

    @pytest.fixture
    def sample_role_plugin(self) -> Plugin:
        """Create sample role plugin for testing."""
        return Plugin(
            name="sample-role",
            version="1.0.0",
            plugin_type=PluginType.ROLE,
            role_spec=RolePluginSpec(
                name="SampleRole",
                persona="You are a sample role for testing",
                skills=["sampling", "testing"],
                tools=["file_manager", "sample_tool"],
                default_model="test-model",
            ),
            enabled=True,
        )

    def test_get_available_roles_includes_plugins(self, sample_role_plugin: Plugin):
        """Test that available roles include plugin roles."""
        registry = PluginRegistry()
        registry._register_plugin(sample_role_plugin)

        available_roles = registry.get_available_roles()

        # Should include base roles + plugin role
        assert "ProductManager" in available_roles  # Base role
        assert "SampleRole" in available_roles  # Plugin role

    def test_get_role_persona_from_plugin(self, sample_role_plugin: Plugin):
        """Test getting role persona from plugin."""
        registry = PluginRegistry()
        registry._register_plugin(sample_role_plugin)

        persona = registry.get_role_persona("SampleRole")

        assert persona == "You are a sample role for testing"

    def test_get_role_persona_not_found(self):
        """Test getting persona for non-existent role."""
        registry = PluginRegistry()

        persona = registry.get_role_persona("NonExistentRole")

        assert persona is None

    def test_get_role_tools_from_plugin(self, sample_role_plugin: Plugin):
        """Test getting role tools from plugin."""
        registry = PluginRegistry()
        registry._register_plugin(sample_role_plugin)

        tools = registry.get_role_tools("SampleRole")

        assert tools == ["file_manager", "sample_tool"]

    def test_enable_disable_plugin(self, sample_role_plugin: Plugin):
        """Test enabling and disabling plugins."""
        registry = PluginRegistry()
        registry._register_plugin(sample_role_plugin)

        # Initially enabled
        assert sample_role_plugin.enabled

        # Disable
        success = registry.disable_plugin("sample-role")
        assert success
        assert not sample_role_plugin.enabled

        # Enable
        success = registry.enable_plugin("sample-role")
        assert success
        assert sample_role_plugin.enabled

    def test_get_plugin_by_name_not_found(self):
        """Test getting non-existent plugin returns None."""
        registry = PluginRegistry()

        plugin = registry.get_plugin_by_name("non-existent")

        assert plugin is None
