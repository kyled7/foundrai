"""Plugin loading system."""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from foundrai.models.plugin import Plugin, PluginType, ValidationResult

logger = logging.getLogger(__name__)


class PluginLoader:
    """Plugin loader for discovering and loading plugins."""

    def __init__(self, plugin_dir: Path | None = None) -> None:
        """Initialize plugin loader.

        Args:
            plugin_dir: Directory to search for plugins. Defaults to .foundrai/plugins
        """
        self.plugin_dir = plugin_dir or Path(".foundrai/plugins")
        self.loaded_plugins: dict[str, Plugin] = {}

        # Ensure plugin directory exists
        self.plugin_dir.mkdir(parents=True, exist_ok=True)

    def discover_plugins(self) -> list[dict[str, Any]]:
        """Scan plugin directory for valid plugin.yaml files.

        Returns:
            List of plugin metadata dictionaries
        """
        plugins = []

        if not self.plugin_dir.exists():
            return plugins

        for plugin_path in self.plugin_dir.iterdir():
            if not plugin_path.is_dir():
                continue

            plugin_yaml = plugin_path / "plugin.yaml"
            if not plugin_yaml.exists():
                continue

            try:
                with open(plugin_yaml) as f:
                    plugin_data = yaml.safe_load(f)

                plugin_data["plugin_path"] = str(plugin_path)
                plugins.append(plugin_data)

            except Exception as e:
                logger.warning(f"Failed to load plugin metadata from {plugin_yaml}: {e}")
                continue

        return plugins

    def load_plugin(self, plugin_name: str) -> Plugin:
        """Load and validate a plugin, checking dependencies.

        Args:
            plugin_name: Name of the plugin to load

        Returns:
            Loaded plugin object

        Raises:
            FileNotFoundError: If plugin not found
            ValidationError: If plugin is invalid
        """
        if plugin_name in self.loaded_plugins:
            return self.loaded_plugins[plugin_name]

        plugin_path = self.plugin_dir / plugin_name
        if not plugin_path.exists():
            raise FileNotFoundError(f"Plugin '{plugin_name}' not found in {self.plugin_dir}")

        plugin_yaml = plugin_path / "plugin.yaml"
        if not plugin_yaml.exists():
            raise FileNotFoundError(f"Plugin '{plugin_name}' missing plugin.yaml")

        # Load plugin metadata
        with open(plugin_yaml) as f:
            plugin_data = yaml.safe_load(f)

        # Convert to Plugin object
        plugin = self._create_plugin_from_metadata(plugin_data, plugin_path)

        # Validate plugin
        validation_result = self.validate_plugin(plugin)
        if not validation_result.valid:
            raise ValidationError(f"Plugin validation failed: {validation_result.errors}")

        # Load dependencies first
        for dep in plugin.dependencies:
            if dep not in self.loaded_plugins:
                self.load_plugin(dep)

        # Load plugin implementation if it's a tool plugin
        if plugin.plugin_type == PluginType.TOOL and plugin.tool_spec:
            self._load_tool_implementation(plugin, plugin_path)

        self.loaded_plugins[plugin_name] = plugin
        logger.info(f"Loaded plugin: {plugin_name} v{plugin.version}")

        return plugin

    def validate_plugin(self, plugin: Plugin) -> ValidationResult:
        """Ensure plugin meets requirements and has no conflicts.

        Args:
            plugin: Plugin to validate

        Returns:
            Validation result with errors and warnings
        """
        errors = []
        warnings = []

        # Check required fields based on plugin type
        if plugin.plugin_type == PluginType.ROLE:
            if not plugin.role_spec:
                errors.append("Role plugin missing role_spec")
            elif not plugin.role_spec.persona:
                errors.append("Role plugin missing persona")

        elif plugin.plugin_type == PluginType.TOOL:
            if not plugin.tool_spec:
                errors.append("Tool plugin missing tool_spec")
            elif not plugin.tool_spec.implementation:
                errors.append("Tool plugin missing implementation")

        elif plugin.plugin_type == PluginType.INTEGRATION:
            if not plugin.integration_spec:
                errors.append("Integration plugin missing integration_spec")

        # Check version format
        if not self._is_valid_version(plugin.version):
            warnings.append(f"Plugin version '{plugin.version}' not in semantic versioning format")

        # Check for dependency cycles
        if self._has_dependency_cycle(plugin):
            errors.append("Plugin has circular dependencies")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin from memory.

        Args:
            plugin_name: Name of the plugin to unload

        Returns:
            True if plugin was unloaded, False if not found
        """
        if plugin_name in self.loaded_plugins:
            plugin = self.loaded_plugins[plugin_name]

            # Remove from Python modules if it's a tool plugin
            if plugin.plugin_type == PluginType.TOOL and plugin.tool_spec:
                module_name = plugin.tool_spec.implementation
                if module_name in sys.modules:
                    del sys.modules[module_name]

            del self.loaded_plugins[plugin_name]
            logger.info(f"Unloaded plugin: {plugin_name}")
            return True

        return False

    def _create_plugin_from_metadata(self, metadata: dict[str, Any], plugin_path: Path) -> Plugin:
        """Create Plugin object from metadata dictionary."""
        plugin_data = {
            "name": metadata["name"],
            "version": metadata["version"],
            "plugin_type": PluginType(metadata["type"]),
            "author": metadata.get("author", "unknown"),
            "description": metadata.get("description", ""),
            "dependencies": metadata.get("dependencies", []),
            "tags": metadata.get("tags", []),
            "repository_url": metadata.get("repository_url"),
            "documentation_url": metadata.get("documentation_url"),
            "license": metadata.get("license", "MIT"),
        }

        # Add type-specific specs
        if plugin_data["plugin_type"] == PluginType.ROLE:
            plugin_data["role_spec"] = metadata.get("role")
        elif plugin_data["plugin_type"] == PluginType.TOOL:
            plugin_data["tool_spec"] = metadata.get("tool")
        elif plugin_data["plugin_type"] == PluginType.INTEGRATION:
            plugin_data["integration_spec"] = metadata.get("integration")

        return Plugin(**plugin_data)

    def _load_tool_implementation(self, plugin: Plugin, plugin_path: Path) -> None:
        """Load tool implementation module."""
        if not plugin.tool_spec:
            return

        implementation_path = plugin_path / f"{plugin.tool_spec.implementation}.py"
        if not implementation_path.exists():
            raise FileNotFoundError(f"Tool implementation not found: {implementation_path}")

        spec = importlib.util.spec_from_file_location(
            plugin.tool_spec.implementation, implementation_path
        )
        if not spec or not spec.loader:
            raise ImportError(f"Failed to load tool implementation: {implementation_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[plugin.tool_spec.implementation] = module
        spec.loader.exec_module(module)

    def _is_valid_version(self, version: str) -> bool:
        """Check if version follows semantic versioning."""
        try:
            parts = version.split(".")
            return len(parts) >= 2 and all(part.isdigit() for part in parts[:3] if part)
        except Exception:
            return False

    def _has_dependency_cycle(self, plugin: Plugin) -> bool:
        """Check for circular dependencies."""
        # Simple cycle detection - could be enhanced
        visited = set()

        def check_deps(plugin_name: str) -> bool:
            if plugin_name in visited:
                return True
            visited.add(plugin_name)

            # This is simplified - in a real implementation we'd
            # need to load dependency metadata to check their deps
            for dep in plugin.dependencies:
                if check_deps(dep):
                    return True

            visited.remove(plugin_name)
            return False

        return check_deps(plugin.name)
