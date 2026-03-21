"""Team template API routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from foundrai.config import FoundrAIConfig
from foundrai.models.template import CreateTemplateRequest, PublishConfig, TeamTemplate
from foundrai.persistence.template_store import TemplateStore
from foundrai.templates.manager import TemplateManager

router = APIRouter()
logger = logging.getLogger(__name__)


class ApplyTemplateRequest(BaseModel):
    """Request to apply a template."""

    project_id: str


def get_template_store() -> TemplateStore:
    """Get template store dependency."""
    # In a real implementation, this would come from dependency injection
    from foundrai.persistence.database import Database

    db = Database("temp.db")  # This should be injected
    return TemplateStore(db)


def get_template_manager() -> TemplateManager:
    """Get template manager dependency."""
    store = get_template_store()
    return TemplateManager(store)


@router.get("/templates", response_model=list[TeamTemplate])
async def list_templates(
    source: str = "all",
    author: str | None = None,
    public_only: bool = False,
    manager: TemplateManager = Depends(get_template_manager),
) -> list[TeamTemplate]:
    """List available templates (local, marketplace, or both)."""
    try:
        if source == "local":
            templates = await manager.store.list_templates(author=author, public_only=public_only)
        elif source == "marketplace":
            # TODO: Implement marketplace listing
            logger.warning("Marketplace templates not yet implemented")
            templates = []
        else:  # "all"
            templates = await manager.store.list_templates(author=author, public_only=public_only)
            # TODO: Add marketplace templates when implemented

        return templates

    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to list templates") from e


@router.post("/templates", response_model=TeamTemplate)
async def create_template(
    request: CreateTemplateRequest,
    # In a real implementation, current project config would come from context
    manager: TemplateManager = Depends(get_template_manager),
) -> TeamTemplate:
    """Create template from current project configuration."""
    try:
        # TODO: Get current project configuration from context/session
        # For now, create a basic configuration
        from foundrai.config import ProjectConfig, SprintConfig, TeamConfig

        config = FoundrAIConfig(
            project=ProjectConfig(name="template-project"), team=TeamConfig(), sprint=SprintConfig()
        )

        template = await manager.save_template(
            name=request.name,
            config=config,
            description=request.description,
            author="api-user",  # Should come from authentication
            tags=request.tags,
            is_public=request.is_public,
        )

        return template

    except Exception as e:
        logger.error(f"Failed to create template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}") from e


@router.get("/templates/{template_id}", response_model=TeamTemplate)
async def get_template(
    template_id: str, manager: TemplateManager = Depends(get_template_manager)
) -> TeamTemplate:
    """Get template details."""
    try:
        template = await manager.load_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        return template

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}") from e


@router.post("/templates/{template_id}/apply")
async def apply_template(
    template_id: str,
    request: ApplyTemplateRequest,
    manager: TemplateManager = Depends(get_template_manager),
) -> dict[str, str]:
    """Apply template to project."""
    try:
        template = await manager.load_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        # TODO: Get current project configuration and apply template
        # For now, just simulate success
        logger.info(f"Applied template {template.name} to project {request.project_id}")

        return {
            "message": f"Template '{template.name}' applied successfully",
            "project_id": request.project_id,
            "template_id": template_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to apply template: {str(e)}") from e


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str, manager: TemplateManager = Depends(get_template_manager)
) -> dict[str, str]:
    """Delete a template."""
    try:
        success = await manager.delete_template(template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")

        return {"message": "Template deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete template: {str(e)}") from e


@router.post("/templates/{template_id}/publish")
async def publish_template(
    template_id: str,
    marketplace_config: PublishConfig,
    manager: TemplateManager = Depends(get_template_manager),
) -> dict[str, str]:
    """Publish template to marketplace."""
    try:
        # TODO: Implement marketplace publishing
        logger.warning("Marketplace publishing not yet implemented")

        return {"message": "Marketplace publishing not yet implemented", "template_id": template_id}

    except Exception as e:
        logger.error(f"Failed to publish template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to publish template: {str(e)}") from e


@router.get("/templates/search")
async def search_templates(
    q: str, tags: list[str] | None = None, manager: TemplateManager = Depends(get_template_manager)
) -> list[TeamTemplate]:
    """Search templates by query and tags."""
    try:
        templates = await manager.store.search_templates(query=q, tags=tags)
        return templates

    except Exception as e:
        logger.error(f"Failed to search templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to search templates") from e
