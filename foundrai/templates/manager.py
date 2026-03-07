"""Team template management system."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from foundrai.config import FoundrAIConfig
from foundrai.models.template import TeamTemplate
from foundrai.persistence.template_store import TemplateStore

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manager for team templates."""

    def __init__(self, store: TemplateStore | None = None) -> None:
        """Initialize template manager.

        Args:
            store: Template store instance. Creates default if None.
        """
        self.store = store or TemplateStore()
        self.templates_dir = Path(".foundrai/templates")
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    async def save_template(
        self,
        name: str,
        config: FoundrAIConfig,
        description: str = "",
        author: str = "local",
        tags: list[str] | None = None,
        is_public: bool = False
    ) -> TeamTemplate:
        """Save current project configuration as a reusable template.

        Args:
            name: Template name
            config: Current project configuration
            description: Template description
            author: Template author
            tags: Template tags
            is_public: Whether template should be public

        Returns:
            Created template
        """
        template = TeamTemplate(
            name=name,
            description=description,
            author=author,
            tags=tags or [],
            team_config=config.team.model_dump(),
            sprint_config=config.sprint.model_dump(),
            is_public=is_public
        )

        # Save to database
        await self.store.create_template(template)

        # Also save as local file for backup/sharing
        self._save_template_file(template)

        logger.info(f"Saved template: {name}")
        return template

    async def load_template(self, template_id: str) -> TeamTemplate | None:
        """Load template from local store or marketplace.

        Args:
            template_id: Template ID to load

        Returns:
            Template if found, None otherwise
        """
        # Try local store first
        template = await self.store.get_template(template_id)
        if template:
            return template

        # TODO: Try marketplace if not found locally
        # For now, just return None
        return None

    async def apply_template(
        self,
        template: TeamTemplate,
        config: FoundrAIConfig
    ) -> FoundrAIConfig:
        """Apply template configuration to current project.

        Args:
            template: Template to apply
            config: Current project configuration to modify

        Returns:
            Updated configuration
        """
        from foundrai.config import SprintConfig, TeamConfig

        # Apply team configuration
        config.team = TeamConfig(**template.team_config)

        # Apply sprint configuration
        config.sprint = SprintConfig(**template.sprint_config)

        # TODO: Check for required plugins and install them
        if template.required_plugins:
            logger.warning(f"Template requires plugins: {template.required_plugins}")
            logger.warning("Plugin installation not yet implemented")

        logger.info(f"Applied template: {template.name}")
        return config

    async def list_templates(self, source: str = "all") -> list[TeamTemplate]:
        """List available templates.

        Args:
            source: Template source ('local', 'marketplace', 'all')

        Returns:
            List of available templates
        """
        templates = []

        if source in ("local", "all"):
            local_templates = await self.store.list_templates()
            templates.extend(local_templates)

        if source in ("marketplace", "all"):
            # TODO: Fetch from marketplace
            pass

        return templates

    async def delete_template(self, template_id: str) -> bool:
        """Delete a local template.

        Args:
            template_id: Template ID to delete

        Returns:
            True if deleted, False if not found
        """
        template = await self.store.get_template(template_id)
        if not template:
            return False

        # Delete from database
        await self.store.delete_template(template_id)

        # Delete local file if exists
        template_file = self.templates_dir / f"{template.name}.json"
        if template_file.exists():
            template_file.unlink()

        logger.info(f"Deleted template: {template.name}")
        return True

    async def export_template(
        self,
        template_id: str,
        output_path: Path | str
    ) -> bool:
        """Export template to shareable file.

        Args:
            template_id: Template ID to export
            output_path: Output file path

        Returns:
            True if exported successfully, False otherwise
        """
        template = await self.store.get_template(template_id)
        if not template:
            return False

        output_path = Path(output_path)

        # Convert to dict and save as JSON
        template_data = template.model_dump()
        with open(output_path, "w") as f:
            json.dump(template_data, f, indent=2, default=str)

        logger.info(f"Exported template {template.name} to {output_path}")
        return True

    async def import_template(self, file_path: Path | str) -> TeamTemplate | None:
        """Import template from file.

        Args:
            file_path: Path to template file

        Returns:
            Imported template if successful, None otherwise
        """
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error(f"Template file not found: {file_path}")
            return None

        try:
            with open(file_path) as f:
                template_data = json.load(f)

            # Remove ID to generate new one
            if "id" in template_data:
                del template_data["id"]

            template = TeamTemplate(**template_data)

            # Save to local store
            await self.store.create_template(template)

            logger.info(f"Imported template: {template.name}")
            return template

        except Exception as e:
            logger.error(f"Failed to import template from {file_path}: {e}")
            return None

    def _save_template_file(self, template: TeamTemplate) -> None:
        """Save template as local JSON file."""
        template_file = self.templates_dir / f"{template.name}.json"

        template_data = template.model_dump()
        with open(template_file, "w") as f:
            json.dump(template_data, f, indent=2, default=str)
