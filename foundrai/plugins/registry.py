"""Plugin registry for managing loaded plugins."""

from __future__ import annotations

import logging
from typing import Any

from foundrai.models.plugin import Plugin, PluginType
from foundrai.plugins.loader import PluginLoader

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing loaded plugins and their capabilities."""

    def __init__(self, loader: PluginLoader | None = None) -> None:
        """Initialize plugin registry.

        Args:
            loader: Plugin loader instance. Creates default if None.
        """
        self.loader = loader or PluginLoader()
        self._role_plugins: dict[str, Plugin] = {}
        self._tool_plugins: dict[str, Plugin] = {}
        self._integration_plugins: dict[str, Plugin] = {}

    def load_all_plugins(self) -> dict[str, Plugin]:
        """Load all discovered plugins.

        Returns:
            Dictionary of loaded plugins by name
        """
        discovered = self.loader.discover_plugins()
        loaded = {}

        for plugin_meta in discovered:
            try:
                plugin = self.loader.load_plugin(plugin_meta["name"])
                loaded[plugin.name] = plugin
                self._register_plugin(plugin)
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_meta['name']}: {e}")

        return loaded

    def get_role_plugins(self) -> dict[str, Plugin]:
        """Get all loaded role plugins.

        Returns:
            Dictionary of role plugins by name
        """
        return self._role_plugins.copy()

    def get_tool_plugins(self) -> dict[str, Plugin]:
        """Get all loaded tool plugins.

        Returns:
            Dictionary of tool plugins by name
        """
        return self._tool_plugins.copy()

    def get_integration_plugins(self) -> dict[str, Plugin]:
        """Get all loaded integration plugins.

        Returns:
            Dictionary of integration plugins by name
        """
        return self._integration_plugins.copy()

    def get_plugin_by_name(self, name: str) -> Plugin | None:
        """Get plugin by name across all types.

        Args:
            name: Plugin name

        Returns:
            Plugin if found, None otherwise
        """
        for plugin_dict in [self._role_plugins, self._tool_plugins, self._integration_plugins]:
            if name in plugin_dict:
                return plugin_dict[name]
        return None

    def get_available_roles(self) -> list[str]:
        """Get list of available agent roles including plugins.

        Returns:
            List of role names
        """
        base_roles = [
            "ProductManager",
            "Architect",
            "Developer",
            "QAEngineer",
            "Designer",
            "DevOps"
        ]

        plugin_roles = [
            plugin.role_spec.name for plugin in self._role_plugins.values()
            if plugin.role_spec and plugin.enabled
        ]

        return base_roles + plugin_roles

    def get_available_tools(self) -> list[str]:
        """Get list of available tools including plugins.

        Returns:
            List of tool names
        """
        base_tools = [
            "file_manager",
            "code_executor"
        ]

        plugin_tools = [
            plugin.tool_spec.name for plugin in self._tool_plugins.values()
            if plugin.tool_spec and plugin.enabled
        ]

        return base_tools + plugin_tools

    def get_role_persona(self, role_name: str) -> str | None:
        """Get persona for a role, checking plugins first.

        Args:
            role_name: Role name to get persona for

        Returns:
            Persona string if found, None otherwise
        """
        for plugin in self._role_plugins.values():
            if (plugin.role_spec and
                plugin.role_spec.name == role_name and
                plugin.enabled):
                return plugin.role_spec.persona

        # Return None for base roles - they have their own persona system
        return None

    def get_role_tools(self, role_name: str) -> list[str] | None:
        """Get tools for a role from plugins.

        Args:
            role_name: Role name to get tools for

        Returns:
            List of tool names if role found in plugins, None otherwise
        """
        for plugin in self._role_plugins.values():
            if (plugin.role_spec and
                plugin.role_spec.name == role_name and
                plugin.enabled):
                return plugin.role_spec.tools

        return None

    def get_tool_implementation(self, tool_name: str) -> str | None:
        """Get implementation module path for a tool plugin.

        Args:
            tool_name: Tool name

        Returns:
            Implementation module path if found, None otherwise
        """
        for plugin in self._tool_plugins.values():
            if (plugin.tool_spec and
                plugin.tool_spec.name == tool_name and
                plugin.enabled):
                return plugin.tool_spec.implementation

        return None

    def get_integration_config_schema(self, integration_name: str) -> dict[str, Any] | None:
        """Get configuration schema for an integration plugin.

        Args:
            integration_name: Integration name

        Returns:
            Configuration schema if found, None otherwise
        """
        for plugin in self._integration_plugins.values():
            if (plugin.integration_spec and
                plugin.name == integration_name and
                plugin.enabled):
                return plugin.integration_spec.configuration_schema

        return None

    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin.

        Args:
            plugin_name: Plugin name to enable

        Returns:
            True if plugin was enabled, False if not found
        """
        plugin = self.get_plugin_by_name(plugin_name)
        if plugin:
            plugin.enabled = True
            return True
        return False

    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin.

        Args:
            plugin_name: Plugin name to disable

        Returns:
            True if plugin was disabled, False if not found
        """
        plugin = self.get_plugin_by_name(plugin_name)
        if plugin:
            plugin.enabled = False
            return True
        return False

    def _register_plugin(self, plugin: Plugin) -> None:
        """Register a plugin in the appropriate category."""
        if plugin.plugin_type == PluginType.ROLE:
            self._role_plugins[plugin.name] = plugin
        elif plugin.plugin_type == PluginType.TOOL:
            self._tool_plugins[plugin.name] = plugin
        elif plugin.plugin_type == PluginType.INTEGRATION:
            self._integration_plugins[plugin.name] = plugin

        logger.info(f"Registered {plugin.plugin_type.value} plugin: {plugin.name}")
