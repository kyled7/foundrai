"""Tests for the template system."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from foundrai.config import FoundrAIConfig, SprintConfig, TeamConfig
from foundrai.models.template import TeamTemplate
from foundrai.persistence.database import Database
from foundrai.persistence.template_store import TemplateStore
from foundrai.templates.manager import TemplateManager


class TestTemplateStore:
    """Test template store functionality."""
    
    @pytest.fixture
    async def db(self):
        """Create test database."""
        db = Database(":memory:")
        await db.connect()
        return db
    
    @pytest.fixture
    def template_store(self, db):
        """Create template store with test database."""
        return TemplateStore(db)
    
    @pytest.fixture
    def sample_template(self) -> TeamTemplate:
        """Create sample template for testing."""
        from foundrai.config import SprintConfig, TeamConfig
        return TeamTemplate(
            name="test-template",
            description="Test template",
            author="test-user",
            version="1.0.0",
            tags=["test", "development"],
            team_config=TeamConfig().model_dump(),
            sprint_config=SprintConfig().model_dump(),
            required_plugins=["test-plugin"],
            recommended_plugins=["optional-plugin"],
            is_public=True
        )
    
    async def test_create_template(self, template_store: TemplateStore, sample_template: TeamTemplate):
        """Test creating a template."""
        created = await template_store.create_template(sample_template)
        
        assert created.id == sample_template.id
        assert created.name == "test-template"
        assert created.author == "test-user"
    
    async def test_get_template(self, template_store: TemplateStore, sample_template: TeamTemplate):
        """Test retrieving a template."""
        await template_store.create_template(sample_template)
        
        retrieved = await template_store.get_template(sample_template.id)
        
        assert retrieved is not None
        assert retrieved.name == "test-template"
        assert retrieved.tags == ["test", "development"]
    
    async def test_get_template_not_found(self, template_store: TemplateStore):
        """Test retrieving non-existent template."""
        retrieved = await template_store.get_template("non-existent-id")
        
        assert retrieved is None
    
    async def test_list_templates(self, template_store: TemplateStore, sample_template: TeamTemplate):
        """Test listing templates."""
        await template_store.create_template(sample_template)
        
        # Create another template
        template2 = TeamTemplate(
            name="template-2",
            description="Second template",
            author="different-user",
            team_config=TeamConfig().model_dump(),
            sprint_config=SprintConfig().model_dump()
        )
        await template_store.create_template(template2)
        
        # List all templates
        all_templates = await template_store.list_templates()
        assert len(all_templates) == 2
        
        # Filter by author
        user_templates = await template_store.list_templates(author="test-user")
        assert len(user_templates) == 1
        assert user_templates[0].name == "test-template"
        
        # Filter public only
        public_templates = await template_store.list_templates(public_only=True)
        assert len(public_templates) == 1  # Only sample_template is public
    
    async def test_update_template(self, template_store: TemplateStore, sample_template: TeamTemplate):
        """Test updating a template."""
        await template_store.create_template(sample_template)
        
        # Update template
        sample_template.description = "Updated description"
        sample_template.tags = ["updated", "test"]
        
        updated = await template_store.update_template(sample_template)
        
        assert updated.description == "Updated description"
        assert updated.tags == ["updated", "test"]
        
        # Verify in database
        retrieved = await template_store.get_template(sample_template.id)
        assert retrieved.description == "Updated description"
    
    async def test_delete_template(self, template_store: TemplateStore, sample_template: TeamTemplate):
        """Test deleting a template."""
        await template_store.create_template(sample_template)
        
        # Verify exists
        retrieved = await template_store.get_template(sample_template.id)
        assert retrieved is not None
        
        # Delete
        success = await template_store.delete_template(sample_template.id)
        assert success
        
        # Verify deleted
        retrieved = await template_store.get_template(sample_template.id)
        assert retrieved is None
    
    async def test_search_templates(self, template_store: TemplateStore):
        """Test searching templates."""
        # Create templates with different content
        template1 = TeamTemplate(
            name="web-dev-template",
            description="Template for web development projects",
            author="dev-user",
            tags=["web", "frontend"],
            team_config=TeamConfig().model_dump(),
            sprint_config=SprintConfig().model_dump()
        )
        
        template2 = TeamTemplate(
            name="mobile-template", 
            description="Template for mobile app development",
            author="mobile-user",
            tags=["mobile", "app"],
            team_config=TeamConfig().model_dump(),
            sprint_config=SprintConfig().model_dump()
        )
        
        await template_store.create_template(template1)
        await template_store.create_template(template2)
        
        # Search by name
        results = await template_store.search_templates("web")
        assert len(results) == 1
        assert results[0].name == "web-dev-template"
        
        # Search by description
        results = await template_store.search_templates("development")
        assert len(results) == 2  # Both have "development" in description
        
        # Search with tags
        results = await template_store.search_templates("template", tags=["web"])
        assert len(results) == 1
        assert results[0].tags == ["web", "frontend"]


class TestTemplateManager:
    """Test template manager functionality."""
    
    @pytest.fixture
    async def db(self):
        """Create test database."""
        db = Database(":memory:")
        await db.connect()
        return db
    
    @pytest.fixture
    def template_manager(self, db):
        """Create template manager with test database."""
        store = TemplateStore(db)
        return TemplateManager(store)
    
    @pytest.fixture 
    def sample_config(self) -> FoundrAIConfig:
        """Create sample configuration."""
        return FoundrAIConfig(
            team=TeamConfig(),
            sprint=SprintConfig(max_tasks_parallel=2, token_budget=50000)
        )
    
    async def test_save_template(self, template_manager: TemplateManager, sample_config: FoundrAIConfig):
        """Test saving a template from configuration."""
        template = await template_manager.save_template(
            name="saved-template",
            config=sample_config,
            description="Template saved from config",
            author="test-author",
            tags=["saved", "test"],
            is_public=True
        )
        
        assert template.name == "saved-template"
        assert template.description == "Template saved from config"
        assert template.author == "test-author"
        assert template.sprint_config["max_tasks_parallel"] == 2
        assert template.sprint_config["token_budget"] == 50000
    
    async def test_load_template(self, template_manager: TemplateManager, sample_config: FoundrAIConfig):
        """Test loading a template."""
        # Save template first
        template = await template_manager.save_template(
            name="load-test",
            config=sample_config,
            author="test-author"
        )
        
        # Load it back
        loaded = await template_manager.load_template(template.id)
        
        assert loaded is not None
        assert loaded.name == "load-test"
        assert loaded.author == "test-author"
    
    async def test_apply_template(self, template_manager: TemplateManager, sample_config: FoundrAIConfig):
        """Test applying a template to configuration."""
        # Create template with specific configuration
        custom_sprint_config = SprintConfig(
            max_tasks_parallel=5,
            token_budget=100000,
            max_sprints=3
        )
        
        template = TeamTemplate(
            name="apply-test",
            description="Test template",
            author="test-author",
            team_config=sample_config.team.model_dump(),
            sprint_config=custom_sprint_config.model_dump()
        )
        
        # Apply template to base config
        updated_config = await template_manager.apply_template(template, sample_config)
        
        assert updated_config.sprint.max_tasks_parallel == 5
        assert updated_config.sprint.token_budget == 100000
        assert updated_config.sprint.max_sprints == 3
    
    async def test_list_templates(self, template_manager: TemplateManager, sample_config: FoundrAIConfig):
        """Test listing templates."""
        # Save some templates
        await template_manager.save_template("template-1", sample_config, author="user1")
        await template_manager.save_template("template-2", sample_config, author="user2")
        
        # List all templates
        templates = await template_manager.list_templates("local")
        
        assert len(templates) == 2
        template_names = [t.name for t in templates]
        assert "template-1" in template_names
        assert "template-2" in template_names
    
    async def test_delete_template(self, template_manager: TemplateManager, sample_config: FoundrAIConfig):
        """Test deleting a template."""
        # Save template
        template = await template_manager.save_template("delete-test", sample_config, author="test")
        
        # Delete it
        success = await template_manager.delete_template(template.id)
        assert success
        
        # Verify deleted
        loaded = await template_manager.load_template(template.id)
        assert loaded is None
    
    async def test_export_import_template(self, template_manager: TemplateManager, sample_config: FoundrAIConfig):
        """Test exporting and importing templates."""
        # Save template
        original = await template_manager.save_template(
            "export-test",
            sample_config,
            description="Export test template",
            author="test-author",
            tags=["export", "test"]
        )
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            export_path = Path(f.name)
        
        success = await template_manager.export_template(original.id, export_path)
        assert success
        assert export_path.exists()
        
        # Import template
        imported = await template_manager.import_template(export_path)
        
        assert imported is not None
        assert imported.name == "export-test"
        assert imported.description == "Export test template"
        assert imported.author == "test-author"
        assert imported.tags == ["export", "test"]
        assert imported.id != original.id  # Should have new ID
        
        # Clean up
        export_path.unlink()