"""Plugin system models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PluginType(str, Enum):
    """Plugin type enumeration."""
    ROLE = "role"
    TOOL = "tool" 
    INTEGRATION = "integration"


class PluginStatus(str, Enum):
    """Plugin status enumeration."""
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class RolePluginSpec(BaseModel):
    """Specification for a role plugin."""
    name: str
    persona: str
    skills: list[str]
    tools: list[str]
    default_model: str
    autonomy_level: str = "notify"


class ToolPluginSpec(BaseModel):
    """Specification for a tool plugin."""
    name: str
    description: str
    implementation: str  # Python module path
    configuration_schema: dict[str, Any] = Field(default_factory=dict)


class IntegrationPluginSpec(BaseModel):
    """Specification for an integration plugin."""
    name: str
    service_type: str
    webhook_endpoints: list[str] = Field(default_factory=list)
    configuration_schema: dict[str, Any] = Field(default_factory=dict)
    auth_methods: list[str] = Field(default_factory=list)


class Plugin(BaseModel):
    """Plugin model."""
    id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    name: str
    version: str
    plugin_type: PluginType
    author: str = "unknown"
    description: str = ""
    
    # Plugin specifications
    role_spec: RolePluginSpec | None = None
    tool_spec: ToolPluginSpec | None = None
    integration_spec: IntegrationPluginSpec | None = None
    
    # Metadata
    dependencies: list[str] = Field(default_factory=list)
    configuration: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    
    # Status
    status: PluginStatus = PluginStatus.INSTALLED
    installed_at: datetime = Field(default_factory=datetime.utcnow)
    enabled: bool = True
    
    # Repository info
    repository_url: str | None = None
    documentation_url: str | None = None
    license: str = "MIT"


class PluginListing(BaseModel):
    """Plugin listing from marketplace."""
    id: str
    name: str
    description: str
    author: str
    version: str
    plugin_type: PluginType
    download_count: int = 0
    rating: float = 0.0
    rating_count: int = 0
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    
    # Rich metadata
    screenshots: list[str] = Field(default_factory=list)
    documentation_url: str | None = None
    repository_url: str | None = None
    license: str = "MIT"
    
    # Compatibility
    foundrai_version: str = ">=0.4.0"
    dependencies: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Plugin validation result."""
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)