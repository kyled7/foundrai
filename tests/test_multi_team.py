"""Tests for multi-team coordination."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from foundrai.config import AgentConfig, SprintConfig
from foundrai.models.team import CrossTeamDependency, DependencyStatus, Team
from foundrai.persistence.database import Database
from foundrai.persistence.team_store import TeamStore


class TestTeamStore:
    """Test team store functionality."""
    
    @pytest.fixture
    async def db(self):
        """Create test database."""
        db = Database(":memory:")
        await db.connect()
        return db
    
    @pytest.fixture
    async def team_store(self, db):
        """Create team store with test database."""
        # Create required projects for foreign key references
        await db.conn.execute("""
            INSERT OR IGNORE INTO projects (project_id, name, description)
            VALUES ('project-1', 'Test Project 1', 'Test project')
        """)
        await db.conn.execute("""
            INSERT OR IGNORE INTO projects (project_id, name, description)
            VALUES ('project-2', 'Test Project 2', 'Test project')
        """)
        await db.conn.commit()
        return TeamStore(db)
    
    @pytest.fixture
    def sample_team(self) -> Team:
        """Create sample team for testing."""
        from foundrai.config import AgentConfig, SprintConfig
        return Team(
            name="Frontend Team",
            description="Handles UI/UX development",
            project_id="project-1",
            agents=[
                AgentConfig(
                    enabled=True,
                    model="anthropic/claude-sonnet-4-20250514",
                    autonomy="notify"
                ).model_dump()
            ],
            template_id=None,
            lead_agent="ProductManager",
            coordination_channel="#frontend-team",
            sprint_config=SprintConfig(max_tasks_parallel=3).model_dump()
        )
    
    async def test_create_team(self, team_store: TeamStore, sample_team: Team):
        """Test creating a team."""
        created = await team_store.create_team(sample_team)
        
        assert created.id == sample_team.id
        assert created.name == "Frontend Team"
        assert created.project_id == "project-1"
        assert created.lead_agent == "ProductManager"
    
    async def test_get_team(self, team_store: TeamStore, sample_team: Team):
        """Test retrieving a team."""
        await team_store.create_team(sample_team)
        
        retrieved = await team_store.get_team(sample_team.id)
        
        assert retrieved is not None
        assert retrieved.name == "Frontend Team"
        assert retrieved.coordination_channel == "#frontend-team"
        assert len(retrieved.agents) == 1
    
    async def test_list_teams_by_project(self, team_store: TeamStore):
        """Test listing teams filtered by project."""
        # Create teams in different projects
        team1 = Team(
            name="Team 1",
            project_id="project-1",
            agents=[],
            sprint_config=SprintConfig().model_dump()
        )
        
        team2 = Team(
            name="Team 2", 
            project_id="project-1",
            agents=[],
            sprint_config=SprintConfig().model_dump()
        )
        
        team3 = Team(
            name="Team 3",
            project_id="project-2", 
            agents=[],
            sprint_config=SprintConfig().model_dump()
        )
        
        await team_store.create_team(team1)
        await team_store.create_team(team2)
        await team_store.create_team(team3)
        
        # List teams for project-1
        project1_teams = await team_store.list_teams("project-1")
        assert len(project1_teams) == 2
        
        team_names = [t.name for t in project1_teams]
        assert "Team 1" in team_names
        assert "Team 2" in team_names
        
        # List all teams
        all_teams = await team_store.list_teams()
        assert len(all_teams) == 3
    
    async def test_update_team(self, team_store: TeamStore, sample_team: Team):
        """Test updating a team."""
        await team_store.create_team(sample_team)
        
        # Update team
        sample_team.description = "Updated description"
        sample_team.coordination_channel = "#updated-channel"
        
        updated = await team_store.update_team(sample_team)
        
        assert updated.description == "Updated description"
        assert updated.coordination_channel == "#updated-channel"
        
        # Verify in database
        retrieved = await team_store.get_team(sample_team.id)
        assert retrieved.description == "Updated description"
    
    async def test_delete_team(self, team_store: TeamStore, sample_team: Team):
        """Test deleting a team."""
        await team_store.create_team(sample_team)
        
        # Verify exists
        retrieved = await team_store.get_team(sample_team.id)
        assert retrieved is not None
        
        # Delete
        success = await team_store.delete_team(sample_team.id)
        assert success
        
        # Verify deleted
        retrieved = await team_store.get_team(sample_team.id)
        assert retrieved is None


class TestCrossTeamDependencies:
    """Test cross-team dependency functionality."""
    
    @pytest.fixture
    async def db(self):
        """Create test database."""
        db = Database(":memory:")
        await db.connect()
        return db
    
    @pytest.fixture
    async def team_store(self, db):
        """Create team store with test database."""
        # Create required projects for foreign key references
        await db.conn.execute("""
            INSERT OR IGNORE INTO projects (project_id, name, description)
            VALUES ('project-1', 'Test Project 1', 'Test project')
        """)
        await db.conn.commit()
        return TeamStore(db)
    
    @pytest.fixture
    async def teams(self, team_store: TeamStore):
        """Create sample teams for dependency testing."""
        frontend_team = Team(
            name="Frontend Team",
            project_id="project-1",
            agents=[],
            sprint_config=SprintConfig().model_dump()
        )
        
        backend_team = Team(
            name="Backend Team", 
            project_id="project-1",
            agents=[],
            sprint_config=SprintConfig().model_dump()
        )
        
        await team_store.create_team(frontend_team)
        await team_store.create_team(backend_team)
        
        return frontend_team, backend_team
    
    @pytest.fixture
    def sample_dependency(self, teams) -> CrossTeamDependency:
        """Create sample dependency."""
        frontend_team, backend_team = teams
        
        return CrossTeamDependency(
            dependent_team_id=frontend_team.id,
            provider_team_id=backend_team.id,
            dependency_type="api",
            title="User Authentication API",
            description="Need REST API endpoints for user login/logout",
            due_date=datetime.utcnow() + timedelta(days=7),
            priority="high"
        )
    
    async def test_create_dependency(self, team_store: TeamStore, sample_dependency: CrossTeamDependency):
        """Test creating a cross-team dependency."""
        created = await team_store.create_dependency(sample_dependency)
        
        assert created.id == sample_dependency.id
        assert created.title == "User Authentication API"
        assert created.dependency_type == "api"
        assert created.status == DependencyStatus.PENDING
        assert created.priority == "high"
    
    async def test_get_dependency(self, team_store: TeamStore, sample_dependency: CrossTeamDependency):
        """Test retrieving a dependency."""
        await team_store.create_dependency(sample_dependency)
        
        retrieved = await team_store.get_dependency(sample_dependency.id)
        
        assert retrieved is not None
        assert retrieved.title == "User Authentication API"
        assert retrieved.description == "Need REST API endpoints for user login/logout"
    
    async def test_list_dependencies_by_team(self, team_store: TeamStore, teams):
        """Test listing dependencies filtered by team."""
        frontend_team, backend_team = teams
        
        # Create dependencies
        dep1 = CrossTeamDependency(
            dependent_team_id=frontend_team.id,
            provider_team_id=backend_team.id,
            dependency_type="api",
            title="Dependency 1"
        )
        
        dep2 = CrossTeamDependency(
            dependent_team_id=backend_team.id,
            provider_team_id=frontend_team.id,
            dependency_type="component",
            title="Dependency 2"
        )
        
        await team_store.create_dependency(dep1)
        await team_store.create_dependency(dep2)
        
        # List dependencies for frontend team (both as dependent and provider)
        frontend_deps = await team_store.list_dependencies(team_id=frontend_team.id)
        assert len(frontend_deps) == 2
        
        # List all dependencies
        all_deps = await team_store.list_dependencies()
        assert len(all_deps) == 2
    
    async def test_update_dependency(self, team_store: TeamStore, sample_dependency: CrossTeamDependency):
        """Test updating a dependency."""
        await team_store.create_dependency(sample_dependency)
        
        # Update dependency
        sample_dependency.status = DependencyStatus.IN_PROGRESS
        sample_dependency.resolution_notes = "Working on implementation"
        sample_dependency.discussion_thread = "slack://thread/123"
        
        updated = await team_store.update_dependency(sample_dependency)
        
        assert updated.status == DependencyStatus.IN_PROGRESS
        assert updated.resolution_notes == "Working on implementation"
        assert updated.discussion_thread == "slack://thread/123"
        
        # Verify in database
        retrieved = await team_store.get_dependency(sample_dependency.id)
        assert retrieved.status == DependencyStatus.IN_PROGRESS
    
    async def test_resolve_dependency(self, team_store: TeamStore, sample_dependency: CrossTeamDependency):
        """Test resolving a dependency."""
        await team_store.create_dependency(sample_dependency)
        
        # Resolve dependency
        sample_dependency.status = DependencyStatus.RESOLVED
        sample_dependency.resolution_notes = "API endpoints implemented and tested"
        sample_dependency.resolved_at = datetime.utcnow()
        
        updated = await team_store.update_dependency(sample_dependency)
        
        assert updated.status == DependencyStatus.RESOLVED
        assert updated.resolved_at is not None
        assert "implemented and tested" in updated.resolution_notes
    
    async def test_dependency_status_progression(self, team_store: TeamStore, sample_dependency: CrossTeamDependency):
        """Test dependency status progression through lifecycle."""
        await team_store.create_dependency(sample_dependency)
        
        # Initially pending
        dep = await team_store.get_dependency(sample_dependency.id)
        assert dep.status == DependencyStatus.PENDING
        
        # Move to in progress
        dep.status = DependencyStatus.IN_PROGRESS
        await team_store.update_dependency(dep)
        
        # Move to resolved
        dep.status = DependencyStatus.RESOLVED
        dep.resolved_at = datetime.utcnow()
        await team_store.update_dependency(dep)
        
        # Verify final state
        final_dep = await team_store.get_dependency(dep.id)
        assert final_dep.status == DependencyStatus.RESOLVED
        assert final_dep.resolved_at is not None


class TestMultiTeamCoordination:
    """Test multi-team coordination scenarios."""
    
    @pytest.fixture
    async def db(self):
        """Create test database."""
        db = Database(":memory:")
        await db.connect()
        return db
    
    @pytest.fixture
    async def team_store(self, db):
        """Create team store with test database."""
        # Create required projects for foreign key references
        await db.conn.execute("""
            INSERT OR IGNORE INTO projects (project_id, name, description)
            VALUES ('ecommerce-project', 'Ecommerce Project', 'Test project')
        """)
        await db.conn.execute("""
            INSERT OR IGNORE INTO projects (project_id, name, description)
            VALUES ('app', 'App Project', 'Test project')
        """)
        await db.conn.commit()
        return TeamStore(db)
    
    async def test_cross_team_dependency_creation(self, team_store: TeamStore):
        """Test creating cross-team dependencies."""
        # Create teams
        web_team = Team(
            name="Web Team",
            project_id="ecommerce-project",
            agents=[],
            sprint_config=SprintConfig().model_dump()
        )
        
        api_team = Team(
            name="API Team",
            project_id="ecommerce-project", 
            agents=[],
            sprint_config=SprintConfig().model_dump()
        )
        
        await team_store.create_team(web_team)
        await team_store.create_team(api_team)
        
        # Create dependency: Web team needs API from API team
        dependency = CrossTeamDependency(
            dependent_team_id=web_team.id,
            provider_team_id=api_team.id,
            dependency_type="api",
            title="Product Catalog API",
            description="Need product listing and search endpoints",
            due_date=datetime.utcnow() + timedelta(days=5),
            priority="critical"
        )
        
        created = await team_store.create_dependency(dependency)
        
        assert created.dependent_team_id == web_team.id
        assert created.provider_team_id == api_team.id
        assert created.dependency_type == "api"
        assert created.priority == "critical"
    
    async def test_dependency_resolution_workflow(self, team_store: TeamStore):
        """Test complete dependency resolution workflow."""
        # Create teams
        frontend = Team(name="Frontend", project_id="app", agents=[], sprint_config=SprintConfig().model_dump())
        backend = Team(name="Backend", project_id="app", agents=[], sprint_config=SprintConfig().model_dump())
        
        await team_store.create_team(frontend)
        await team_store.create_team(backend)
        
        # Create dependency
        dep = CrossTeamDependency(
            dependent_team_id=frontend.id,
            provider_team_id=backend.id,
            dependency_type="api",
            title="Authentication Service"
        )
        
        await team_store.create_dependency(dep)
        
        # Step 1: Acknowledge and start work
        dep.status = DependencyStatus.IN_PROGRESS
        dep.discussion_thread = "slack://channel/auth-discussion"
        await team_store.update_dependency(dep)
        
        # Step 2: Hit a blocker
        dep.status = DependencyStatus.BLOCKED
        dep.resolution_notes = "Blocked by infrastructure setup"
        await team_store.update_dependency(dep)
        
        # Step 3: Resume work
        dep.status = DependencyStatus.IN_PROGRESS
        dep.resolution_notes = "Infrastructure resolved, continuing development"
        await team_store.update_dependency(dep)
        
        # Step 4: Complete
        dep.status = DependencyStatus.RESOLVED
        dep.resolved_at = datetime.utcnow()
        dep.resolution_notes = "Authentication API deployed and documented"
        final_dep = await team_store.update_dependency(dep)
        
        assert final_dep.status == DependencyStatus.RESOLVED
        assert final_dep.resolved_at is not None
        assert "deployed and documented" in final_dep.resolution_notes
    
    async def test_multiple_dependencies_same_teams(self, team_store: TeamStore):
        """Test multiple dependencies between same teams."""
        # Create teams
        mobile = Team(name="Mobile", project_id="app", agents=[], sprint_config=SprintConfig().model_dump())
        backend = Team(name="Backend", project_id="app", agents=[], sprint_config=SprintConfig().model_dump())
        
        await team_store.create_team(mobile)
        await team_store.create_team(backend)
        
        # Create multiple dependencies
        deps = [
            CrossTeamDependency(
                dependent_team_id=mobile.id,
                provider_team_id=backend.id,
                dependency_type="api",
                title="User Management API"
            ),
            CrossTeamDependency(
                dependent_team_id=mobile.id,
                provider_team_id=backend.id,
                dependency_type="api",
                title="Push Notification API"
            ),
            CrossTeamDependency(
                dependent_team_id=backend.id,
                provider_team_id=mobile.id,
                dependency_type="data",
                title="Device Analytics Data"
            )
        ]
        
        for dep in deps:
            await team_store.create_dependency(dep)
        
        # List dependencies for mobile team
        mobile_deps = await team_store.list_dependencies(team_id=mobile.id)
        assert len(mobile_deps) == 3  # Mobile is involved in all 3
        
        # Count dependencies by type
        api_deps = [d for d in mobile_deps if d.dependency_type == "api"]
        data_deps = [d for d in mobile_deps if d.dependency_type == "data"]
        
        assert len(api_deps) == 2
        assert len(data_deps) == 1