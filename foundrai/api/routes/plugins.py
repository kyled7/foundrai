"""Plugin management API routes."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from foundrai.models.plugin import Plugin, PluginListing, PluginType
from foundrai.persistence.database import Database
from foundrai.persistence.plugin_store import PluginStore
from foundrai.plugins.loader import PluginLoader
from foundrai.plugins.registry import PluginRegistry

router = APIRouter()
logger = logging.getLogger(__name__)


class PluginInfo(BaseModel):
    """Plugin information for API responses."""
    id: str
    name: str
    version: str
    plugin_type: PluginType
    author: str
    description: str
    enabled: bool
    dependencies: list[str] = []
    tags: list[str] = []


class InstallPluginRequest(BaseModel):
    """Request to install a plugin."""
    source: str  # "marketplace", "local", "url"
    identifier: str  # Plugin name/ID/URL
    version: str | None = None


class TogglePluginRequest(BaseModel):
    """Request to toggle plugin state."""
    enabled: bool


def get_plugin_store() -> PluginStore:
    """Get plugin store dependency."""
    # In a real implementation, this would come from dependency injection
    from foundrai.persistence.database import Database
    db = Database("temp.db")  # This should be injected
    return PluginStore(db)


def get_plugin_registry() -> PluginRegistry:
    """Get plugin registry dependency."""
    return PluginRegistry()


@router.get("/plugins", response_model=list[PluginInfo])
async def list_plugins(
    plugin_type: PluginType | None = None,
    enabled_only: bool = True,
    store: PluginStore = Depends(get_plugin_store)
) -> list[PluginInfo]:
    """List installed plugins."""
    try:
        plugins = await store.list_plugins(plugin_type=plugin_type, enabled_only=enabled_only)
        
        return [
            PluginInfo(
                id=plugin.id,
                name=plugin.name,
                version=plugin.version,
                plugin_type=plugin.plugin_type,
                author=plugin.author,
                description=plugin.description,
                enabled=plugin.enabled,
                dependencies=plugin.dependencies,
                tags=plugin.tags
            )
            for plugin in plugins
        ]
    except Exception as e:
        logger.error(f"Failed to list plugins: {e}")
        raise HTTPException(status_code=500, detail="Failed to list plugins")


@router.post("/plugins/install", response_model=PluginInfo)
async def install_plugin(
    request: InstallPluginRequest,
    store: PluginStore = Depends(get_plugin_store),
    registry: PluginRegistry = Depends(get_plugin_registry)
) -> PluginInfo:
    """Install plugin from marketplace or local file."""
    try:
        if request.source == "local":
            # Load plugin from local plugin directory
            loader = PluginLoader()
            plugin = loader.load_plugin(request.identifier)
            
            # Save to database
            await store.create_plugin(plugin)
            
        elif request.source == "marketplace":
            # TODO: Download from marketplace
            raise HTTPException(
                status_code=501, 
                detail="Marketplace installation not yet implemented"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported plugin source: {request.source}"
            )
        
        return PluginInfo(
            id=plugin.id,
            name=plugin.name,
            version=plugin.version,
            plugin_type=plugin.plugin_type,
            author=plugin.author,
            description=plugin.description,
            enabled=plugin.enabled,
            dependencies=plugin.dependencies,
            tags=plugin.tags
        )
        
    except Exception as e:
        logger.error(f"Failed to install plugin {request.identifier}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to install plugin: {str(e)}"
        )


@router.delete("/plugins/{plugin_id}")
async def uninstall_plugin(
    plugin_id: str,
    store: PluginStore = Depends(get_plugin_store)
) -> dict[str, str]:
    """Uninstall plugin."""
    try:
        success = await store.delete_plugin(plugin_id)
        if not success:
            raise HTTPException(status_code=404, detail="Plugin not found")
            
        return {"message": "Plugin uninstalled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to uninstall plugin {plugin_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to uninstall plugin: {str(e)}"
        )


@router.put("/plugins/{plugin_id}/toggle", response_model=PluginInfo)
async def toggle_plugin(
    plugin_id: str,
    request: TogglePluginRequest,
    store: PluginStore = Depends(get_plugin_store)
) -> PluginInfo:
    """Enable or disable plugin."""
    try:
        success = await store.toggle_plugin(plugin_id, request.enabled)
        if not success:
            raise HTTPException(status_code=404, detail="Plugin not found")
        
        # Get updated plugin
        plugin = await store.get_plugin(plugin_id)
        if not plugin:
            raise HTTPException(status_code=404, detail="Plugin not found")
        
        return PluginInfo(
            id=plugin.id,
            name=plugin.name,
            version=plugin.version,
            plugin_type=plugin.plugin_type,
            author=plugin.author,
            description=plugin.description,
            enabled=plugin.enabled,
            dependencies=plugin.dependencies,
            tags=plugin.tags
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle plugin {plugin_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to toggle plugin: {str(e)}"
        )


@router.get("/plugins/marketplace", response_model=list[PluginListing])
async def browse_marketplace(
    plugin_type: PluginType | None = None,
    search: str | None = None
) -> list[PluginListing]:
    """Browse plugins in the marketplace."""
    try:
        # TODO: Implement marketplace client
        # For now, return empty list
        logger.warning("Marketplace browsing not yet implemented")
        return []
        
    except Exception as e:
        logger.error(f"Failed to browse marketplace: {e}")
        raise HTTPException(status_code=500, detail="Failed to browse marketplace")