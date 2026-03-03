# FoundrAI — Phase 4 Technical Design Document

> **Status:** Implementation Ready  
> **Version:** 1.0  
> **Date:** 2026-03-04  
> **Scope:** Ecosystem — Plugin architecture, integrations, and community features  
> **Depends on:** Phase 0 (Foundation) ✅, Phase 1 (Visual Layer) ✅, Phase 2 (Agile Engine) ✅, Phase 3 (Observability) ✅

---

## Table of Contents

1. [Scope & Goals](#1-scope--goals)
2. [Plugin Architecture](#2-plugin-architecture)
3. [Team Template System](#3-team-template-system)
4. [GitHub Integration](#4-github-integration)
5. [Jira/Linear Integration](#5-jiralinear-integration)
6. [Slack Integration](#6-slack-integration)
7. [Community Marketplace](#7-community-marketplace)
8. [DevOps Agent Enhancement](#8-devops-agent-enhancement)
9. [Multi-Team Coordination](#9-multi-team-coordination)
10. [Database Schema Changes](#10-database-schema-changes)
11. [API Changes](#11-api-changes)
12. [Frontend Changes](#12-frontend-changes)
13. [Testing Strategy](#13-testing-strategy)

---

## 1. Scope & Goals

### What Phase 4 Delivers

Phase 4 transforms FoundrAI from a standalone AI team simulator into a comprehensive **ecosystem** with extensibility, real-world integrations, and community features. It enables custom roles, external tool integrations, team configuration sharing, and multi-team coordination.

### Deliverables

| Deliverable | Description |
|---|---|
| Plugin Architecture | Load custom agent roles, tools, and integrations from plugins |
| Team Template System | Save, load, and share team configurations with marketplace |
| GitHub Integration | Agents create repositories, branches, and pull requests automatically |
| Jira/Linear Integration | Bi-directional sync of tasks with external project management |
| Slack Integration | Notifications, approvals, and team coordination via Slack |
| Community Marketplace | Discover and install plugins and templates from the community |
| DevOps Agent Enhancement | Real CI/CD capabilities with deployment automation |
| Multi-Team Coordination | Multiple AI teams working on the same project |

### Definition of Done

FoundrAI has a thriving plugin ecosystem, integrates with real development tools, supports multiple teams on one project, and has an active open source community contributing templates and plugins.

---

## 2. Plugin Architecture

### 2.1 Plugin System Overview

```
Plugin Architecture:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Core System    │    │  Plugin Loader  │    │  Plugin Store   │
│                 │────│                 │────│                 │
│ • Agent Runtime │    │ • Discovery     │    │ • Role Plugins  │
│ • Tool Registry │    │ • Validation    │    │ • Tool Plugins  │
│ • Role Registry │    │ • Loading       │    │ • Integration   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2.2 Plugin Types

**Role Plugins** — Custom agent roles with personas and tools
```python
class RolePlugin(BaseModel):
    name: str                    # e.g., "DataScientist"
    version: str                # Semantic versioning
    persona: str                # System prompt template
    skills: list[str]           # Capability descriptions
    tools: list[str]            # Required tool names
    default_model: str          # Recommended LLM model
    dependencies: list[str] = []  # Other plugins required
```

**Tool Plugins** — Extend agent capabilities with new tools
```python
class ToolPlugin(BaseModel):
    name: str                   # e.g., "docker_runner"
    version: str
    description: str
    implementation: str         # Python module path
    configuration_schema: dict  # JSON schema for settings
    dependencies: list[str] = []
```

**Integration Plugins** — Connect to external services
```python
class IntegrationPlugin(BaseModel):
    name: str                   # e.g., "github"
    version: str
    service_type: str          # "source_control", "project_management", etc.
    webhook_endpoints: list[str] = []
    configuration_schema: dict
    auth_methods: list[str]    # "oauth2", "token", "basic"
```

### 2.3 Plugin Loading System

**Plugin Discovery**
```python
# foundrai/plugins/loader.py
class PluginLoader:
    def __init__(self, plugin_dir: Path = Path(".foundrai/plugins")):
        self.plugin_dir = plugin_dir
        self.loaded_plugins: dict[str, Plugin] = {}
    
    def discover_plugins(self) -> list[PluginMetadata]:
        """Scan plugin directory for valid plugin.yaml files."""
        
    def load_plugin(self, plugin_name: str) -> Plugin:
        """Load and validate a plugin, checking dependencies."""
        
    def validate_plugin(self, plugin: Plugin) -> ValidationResult:
        """Ensure plugin meets requirements and has no conflicts."""
```

**Plugin Configuration**
```yaml
# .foundrai/plugins/data-scientist/plugin.yaml
name: data-scientist
version: 1.0.0
type: role
author: community
description: Agent specialized in data analysis and ML model development

role:
  name: DataScientist
  persona: |
    You are a senior data scientist with expertise in Python, pandas, scikit-learn,
    and statistical analysis. You excel at exploratory data analysis, feature
    engineering, model development, and result interpretation.
  skills:
    - "Data analysis and visualization"
    - "Machine learning model development"
    - "Statistical hypothesis testing"
    - "Feature engineering"
  tools:
    - file_manager
    - code_executor
    - data_visualizer  # Custom tool from this plugin
  default_model: anthropic/claude-sonnet-4-20250514

dependencies:
  - data-visualizer-tool >= 1.0.0

configuration:
  default_notebook_kernel: python3
  max_dataset_size_mb: 100
```

### 2.4 Plugin Security

**Sandboxing**
- Plugins execute in isolated environments
- Tool plugins run with restricted file system access
- Network access controlled via allowlist
- Resource limits (CPU, memory, execution time)

**Validation**
- Plugin signature verification for marketplace plugins
- Static analysis of plugin code for security vulnerabilities
- Runtime permission system for sensitive operations

---

## 3. Team Template System

### 3.1 Template Structure

```python
# foundrai/models/template.py
class TeamTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    author: str
    version: str = "1.0.0"
    tags: list[str] = []
    
    # Core configuration
    team_config: TeamConfig
    sprint_config: SprintConfig
    
    # Plugin requirements
    required_plugins: list[str] = []
    recommended_plugins: list[str] = []
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    downloads: int = 0
    rating: float = 0.0
    
    # Marketplace
    is_public: bool = False
    marketplace_url: str | None = None
```

### 3.2 Template Management

**Local Templates**
```python
# foundrai/templates/manager.py
class TemplateManager:
    def save_template(self, name: str, config: FoundrAIConfig) -> TeamTemplate:
        """Save current project configuration as a reusable template."""
        
    def load_template(self, template_id: str) -> TeamTemplate:
        """Load template from local store or marketplace."""
        
    def apply_template(self, template: TeamTemplate, project_config: FoundrAIConfig):
        """Apply template configuration to current project."""
        
    def list_templates(self, source: str = "all") -> list[TeamTemplate]:
        """List available templates (local, marketplace, or both)."""
```

**Template Storage**
```sql
-- New table for local templates
CREATE TABLE team_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    author TEXT NOT NULL,
    version TEXT NOT NULL,
    tags TEXT, -- JSON array
    team_config TEXT NOT NULL, -- JSON
    sprint_config TEXT NOT NULL, -- JSON
    required_plugins TEXT, -- JSON array
    recommended_plugins TEXT, -- JSON array
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    is_public BOOLEAN DEFAULT FALSE,
    marketplace_url TEXT
);
```

### 3.3 Template Sharing

**Export/Import**
```bash
# Export template to shareable file
foundrai template export "my-template" --output my-template.json

# Import template from file
foundrai template import my-template.json

# Apply template to project
foundrai template apply "agile-web-team"
```

**Marketplace Integration**
- Templates can be published to community marketplace
- Automatic updates when template authors release new versions
- Rating and review system for quality control
- Template dependency resolution

---

## 4. GitHub Integration

### 4.1 GitHub Service Architecture

```python
# foundrai/integrations/github/service.py
class GitHubService:
    def __init__(self, token: str, org: str | None = None):
        self.client = Github(token)
        self.org = org
    
    async def create_repository(self, name: str, description: str) -> Repository:
        """Create a new repository for the sprint."""
        
    async def create_branch(self, repo: Repository, branch_name: str) -> Reference:
        """Create feature branch for task implementation."""
        
    async def create_pull_request(
        self,
        repo: Repository,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main"
    ) -> PullRequest:
        """Create pull request with agent-generated changes."""
        
    async def create_issue(self, repo: Repository, title: str, body: str) -> Issue:
        """Create GitHub issue for tracking tasks."""
        
    async def sync_task_to_issue(self, task: Task, repo: Repository) -> Issue:
        """Sync FoundrAI task with GitHub issue."""
```

### 4.2 Agent Integration

**Enhanced Developer Agent**
```python
# foundrai/agents/personas/developer.py (enhanced)
class DeveloperAgent(BaseAgent):
    async def implement_task(self, task: Task) -> TaskResult:
        # Existing implementation logic...
        
        # NEW: GitHub integration
        if self.config.integrations.github.enabled:
            await self._create_feature_branch(task)
            result = await super().implement_task(task)
            await self._commit_changes(task, result)
            await self._create_pull_request(task, result)
            
        return result
        
    async def _create_feature_branch(self, task: Task):
        branch_name = f"feature/task-{task.id}"
        await self.github.create_branch(self.repo, branch_name)
        
    async def _create_pull_request(self, task: Task, result: TaskResult):
        pr_title = f"[Task {task.id}] {task.title}"
        pr_body = self._generate_pr_description(task, result)
        await self.github.create_pull_request(
            self.repo, pr_title, pr_body, f"feature/task-{task.id}"
        )
```

### 4.3 Workflow Integration

**Sprint → Repository Mapping**
```python
# foundrai/integrations/github/sprint_sync.py
class GitHubSprintSync:
    async def setup_sprint_repository(self, sprint: Sprint) -> Repository:
        """Create or connect to repository for this sprint."""
        repo_name = f"{sprint.project.name}-sprint-{sprint.number}"
        return await self.github.create_repository(repo_name, sprint.description)
        
    async def sync_tasks_to_issues(self, sprint: Sprint):
        """Create GitHub issues for all sprint tasks."""
        for task in sprint.tasks:
            await self.github.sync_task_to_issue(task, sprint.repository)
```

### 4.4 Configuration

```yaml
# foundrai.yaml (extended)
integrations:
  github:
    enabled: true
    token: ${GITHUB_TOKEN}  # Environment variable
    organization: my-org    # Optional: create repos in org
    auto_create_repos: true
    auto_create_prs: true
    pr_template: |
      ## Task: {{task.title}}
      
      **Description:** {{task.description}}
      
      **Changes:**
      {{changes_summary}}
      
      **Testing:**
      {{testing_notes}}
    
    # Branch naming convention
    branch_prefix: "foundrai/"
    
    # Repository settings
    default_branch: main
    auto_merge_on_approval: false
```

---

## 5. Jira/Linear Integration

### 5.1 Project Management Abstraction

```python
# foundrai/integrations/project_management/base.py
class ProjectManagementService(ABC):
    @abstractmethod
    async def create_epic(self, title: str, description: str) -> Epic:
        """Create epic/initiative for sprint."""
        
    @abstractmethod
    async def create_task(self, epic_id: str, title: str, description: str) -> PMTask:
        """Create task/story in project management system."""
        
    @abstractmethod
    async def update_task_status(self, task_id: str, status: str):
        """Update task status (To Do, In Progress, Done)."""
        
    @abstractmethod
    async def sync_task_bidirectional(self, foundrai_task: Task, pm_task: PMTask):
        """Bi-directional sync between systems."""
```

### 5.2 Jira Implementation

```python
# foundrai/integrations/jira/service.py
class JiraService(ProjectManagementService):
    def __init__(self, server: str, email: str, token: str):
        self.jira = JIRA(server=server, basic_auth=(email, token))
    
    async def create_epic(self, title: str, description: str) -> Epic:
        epic_data = {
            'project': self.project_key,
            'summary': title,
            'description': description,
            'issuetype': {'name': 'Epic'},
            'customfield_10011': title  # Epic Name field
        }
        return self.jira.create_issue(fields=epic_data)
    
    async def create_task(self, epic_id: str, title: str, description: str) -> PMTask:
        task_data = {
            'project': self.project_key,
            'summary': title,
            'description': description,
            'issuetype': {'name': 'Task'},
            'customfield_10014': epic_id  # Epic Link
        }
        return self.jira.create_issue(fields=task_data)
```

### 5.3 Linear Implementation

```python
# foundrai/integrations/linear/service.py
class LinearService(ProjectManagementService):
    def __init__(self, api_key: str, team_id: str):
        self.client = LinearClient(api_key)
        self.team_id = team_id
    
    async def create_task(self, epic_id: str, title: str, description: str) -> PMTask:
        return await self.client.create_issue(
            team_id=self.team_id,
            title=title,
            description=description,
            project_id=epic_id
        )
    
    async def update_task_status(self, task_id: str, status: str):
        linear_status = self._map_status_to_linear(status)
        await self.client.update_issue(task_id, state_id=linear_status.id)
```

### 5.4 Synchronization Engine

```python
# foundrai/integrations/project_management/sync.py
class PMSyncEngine:
    def __init__(self, pm_service: ProjectManagementService):
        self.pm_service = pm_service
        
    async def sync_sprint_to_pm(self, sprint: Sprint):
        """Create epic and tasks in external PM system."""
        # Create epic for sprint
        epic = await self.pm_service.create_epic(
            f"Sprint {sprint.number}: {sprint.goal}",
            sprint.description
        )
        
        # Create tasks
        for task in sprint.tasks:
            pm_task = await self.pm_service.create_task(
                epic.id, task.title, task.description
            )
            
            # Store mapping for bi-directional sync
            await self._store_task_mapping(task, pm_task)
    
    async def sync_status_updates(self):
        """Bi-directional status sync between systems."""
        mappings = await self._get_all_task_mappings()
        
        for mapping in mappings:
            # Sync FoundrAI → PM system
            if mapping.foundrai_task.updated_at > mapping.last_sync:
                await self.pm_service.update_task_status(
                    mapping.pm_task_id, 
                    self._map_status_to_pm(mapping.foundrai_task.status)
                )
            
            # Sync PM system → FoundrAI
            pm_task = await self.pm_service.get_task(mapping.pm_task_id)
            if pm_task.updated_at > mapping.last_sync:
                await self._update_foundrai_task_status(
                    mapping.foundrai_task,
                    self._map_status_from_pm(pm_task.status)
                )
```

---

## 6. Slack Integration

### 6.1 Slack Bot Architecture

```python
# foundrai/integrations/slack/bot.py
class FoundrAISlackBot:
    def __init__(self, token: str, signing_secret: str):
        self.app = App(token=token, signing_secret=signing_secret)
        self._setup_handlers()
    
    def _setup_handlers(self):
        self.app.event("app_mention")(self.handle_mention)
        self.app.command("/foundrai")(self.handle_slash_command)
        self.app.action("approve_task")(self.handle_approval)
        self.app.action("reject_task")(self.handle_rejection)
    
    async def handle_mention(self, event, say):
        """Handle @foundrai mentions in channels."""
        text = event["text"]
        if "sprint status" in text:
            await self._send_sprint_status(say)
        elif "start sprint" in text:
            await self._start_sprint_interactive(say)
    
    async def handle_slash_command(self, ack, command, say):
        """Handle /foundrai slash command."""
        await ack()
        
        subcommand = command["text"].split()[0] if command["text"] else "help"
        
        if subcommand == "status":
            await self._send_sprint_status(say)
        elif subcommand == "approve":
            await self._approve_pending_tasks(say)
        elif subcommand == "team":
            await self._send_team_status(say)
```

### 6.2 Notification System

```python
# foundrai/integrations/slack/notifications.py
class SlackNotificationService:
    async def send_sprint_started(self, sprint: Sprint, channel: str):
        """Notify channel that a new sprint has started."""
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🚀 Sprint {sprint.number} Started"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Goal:* {sprint.goal}"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Tasks:* {len(sprint.tasks)}"},
                    {"type": "mrkdwn", "text": f"*Duration:* {sprint.duration_hours}h"}
                ]
            }
        ]
        
        await self.slack.send_message(channel, blocks=blocks)
    
    async def send_approval_request(self, task: Task, channel: str):
        """Request approval for a task via Slack."""
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Task:* {task.title}\n*Agent:* {task.assigned_agent}"}
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Approve"},
                        "style": "primary",
                        "action_id": "approve_task",
                        "value": task.id
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Reject"},
                        "style": "danger",
                        "action_id": "reject_task",
                        "value": task.id
                    }
                ]
            }
        ]
        
        await self.slack.send_message(channel, blocks=blocks)
```

### 6.3 Interactive Features

**Slash Commands**
- `/foundrai status` — Show current sprint status
- `/foundrai team` — Show team member status and autonomy levels  
- `/foundrai approve [task_id]` — Approve specific task
- `/foundrai budget` — Show token usage and remaining budget

**Interactive Buttons**
- Approve/Reject buttons on approval requests
- Quick actions for common operations
- Sprint control buttons (pause, resume, abort)

### 6.4 Configuration

```yaml
# foundrai.yaml (extended)
integrations:
  slack:
    enabled: true
    bot_token: ${SLACK_BOT_TOKEN}
    signing_secret: ${SLACK_SIGNING_SECRET}
    
    # Default channels for notifications
    channels:
      sprint_updates: "#foundrai-sprints"
      approvals: "#foundrai-approvals"  
      alerts: "#foundrai-alerts"
    
    # Notification preferences
    notifications:
      sprint_start: true
      sprint_complete: true
      task_approval_required: true
      budget_warning: true
      errors: true
    
    # Interactive features
    slash_commands_enabled: true
    approval_buttons: true
```

---

## 7. Community Marketplace

### 7.1 Marketplace API

```python
# foundrai/marketplace/client.py
class MarketplaceClient:
    def __init__(self, base_url: str = "https://marketplace.foundrai.dev"):
        self.base_url = base_url
        self.session = httpx.AsyncClient()
    
    async def search_plugins(
        self, 
        query: str, 
        plugin_type: str | None = None,
        tags: list[str] | None = None
    ) -> list[PluginListing]:
        """Search plugins in the marketplace."""
        
    async def search_templates(
        self,
        query: str,
        tags: list[str] | None = None
    ) -> list[TemplateListing]:
        """Search team templates in the marketplace."""
        
    async def download_plugin(self, plugin_id: str, version: str) -> Path:
        """Download and verify plugin package."""
        
    async def download_template(self, template_id: str) -> TeamTemplate:
        """Download team template."""
        
    async def publish_plugin(self, plugin: Plugin, api_key: str) -> PublishResult:
        """Publish plugin to marketplace (requires auth)."""
        
    async def publish_template(self, template: TeamTemplate, api_key: str) -> PublishResult:
        """Publish template to marketplace (requires auth)."""
```

### 7.2 Marketplace Integration

**Plugin Installation**
```bash
# Search marketplace
foundrai plugin search "data science"

# Install plugin from marketplace
foundrai plugin install data-scientist-role --version 1.2.0

# List installed plugins
foundrai plugin list

# Update plugins
foundrai plugin update --all
```

**Template Management**
```bash
# Browse templates
foundrai template browse --tag "web-development"

# Install template
foundrai template install agile-web-team

# Publish local template
foundrai template publish my-template --public
```

### 7.3 Discovery and Ratings

**Plugin/Template Listing**
```python
class PluginListing(BaseModel):
    id: str
    name: str
    description: str
    author: str
    version: str
    download_count: int
    rating: float
    rating_count: int
    tags: list[str]
    created_at: datetime
    updated_at: datetime
    
    # Rich metadata
    screenshots: list[str] = []
    documentation_url: str | None = None
    repository_url: str | None = None
    license: str = "MIT"
    
    # Compatibility
    foundrai_version: str  # Minimum required version
    dependencies: list[str] = []
```

**Rating System**
- 5-star rating system for plugins and templates
- Written reviews with pros/cons
- Verification badges for trusted authors
- Usage metrics and compatibility reports

---

## 8. DevOps Agent Enhancement

### 8.1 Enhanced DevOps Capabilities

```python
# foundrai/agents/personas/devops.py (enhanced)
class DevOpsAgent(BaseAgent):
    """Enhanced DevOps agent with real CI/CD capabilities."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tools.extend([
            "docker_manager",
            "kubernetes_manager", 
            "terraform_manager",
            "ci_pipeline_manager",
            "monitoring_setup"
        ])
    
    async def setup_cicd_pipeline(self, project: Project) -> CICDPipeline:
        """Create complete CI/CD pipeline for the project."""
        
    async def deploy_application(self, deployment_spec: DeploymentSpec) -> Deployment:
        """Deploy application to specified environment."""
        
    async def setup_monitoring(self, application: Application) -> MonitoringStack:
        """Set up monitoring and alerting for deployed application."""
        
    async def manage_infrastructure(self, infra_spec: InfrastructureSpec) -> Infrastructure:
        """Provision and manage infrastructure resources."""
```

### 8.2 CI/CD Pipeline Tools

**Docker Management Tool**
```python
# foundrai/tools/docker_manager.py
class DockerManager(BaseTool):
    name = "docker_manager"
    description = "Manage Docker containers, images, and compose files"
    
    async def build_image(self, dockerfile_path: str, tag: str) -> str:
        """Build Docker image from Dockerfile."""
        
    async def run_container(self, image: str, config: dict) -> str:
        """Run container with specified configuration."""
        
    async def create_compose_file(self, services: list[dict]) -> str:
        """Generate docker-compose.yml for multi-service applications."""
```

**Kubernetes Management Tool**
```python  
# foundrai/tools/kubernetes_manager.py
class KubernetesManager(BaseTool):
    name = "kubernetes_manager"
    description = "Deploy and manage Kubernetes resources"
    
    async def create_deployment(self, app_spec: dict) -> dict:
        """Create Kubernetes deployment manifest."""
        
    async def create_service(self, service_spec: dict) -> dict:
        """Create Kubernetes service manifest."""
        
    async def apply_manifests(self, namespace: str, manifests: list[dict]) -> dict:
        """Apply manifests to Kubernetes cluster."""
```

**CI Pipeline Manager Tool**
```python
# foundrai/tools/ci_pipeline_manager.py
class CIPipelineManager(BaseTool):
    name = "ci_pipeline_manager"
    description = "Create and manage CI/CD pipelines"
    
    async def create_github_actions(self, workflow_spec: dict) -> str:
        """Generate GitHub Actions workflow file."""
        
    async def create_gitlab_ci(self, pipeline_spec: dict) -> str:
        """Generate GitLab CI/CD pipeline file."""
        
    async def setup_deployment_pipeline(self, deployment_spec: dict) -> dict:
        """Create complete deployment pipeline."""
```

### 8.3 Infrastructure as Code

**Terraform Integration**
```python
# foundrai/tools/terraform_manager.py
class TerraformManager(BaseTool):
    name = "terraform_manager"
    description = "Manage infrastructure with Terraform"
    
    async def generate_terraform_config(self, infra_spec: dict) -> str:
        """Generate Terraform configuration files."""
        
    async def plan_infrastructure(self, config_path: str) -> dict:
        """Run terraform plan and return changes."""
        
    async def apply_infrastructure(self, config_path: str) -> dict:
        """Apply terraform configuration."""
```

### 8.4 Deployment Automation

**Multi-Environment Support**
```python
class DeploymentSpec(BaseModel):
    application_name: str
    version: str
    environment: str  # dev, staging, prod
    
    # Container configuration
    docker_image: str
    replicas: int = 1
    resources: dict = {}
    
    # Environment variables
    env_vars: dict = {}
    secrets: list[str] = []
    
    # Networking
    ports: list[int] = []
    ingress_rules: list[dict] = []
    
    # Monitoring
    health_check_path: str = "/health"
    metrics_enabled: bool = True
```

---

## 9. Multi-Team Coordination

### 9.1 Multi-Team Architecture

```python
# foundrai/models/team.py (new)
class Team(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    project_id: str
    
    # Team composition
    agents: list[AgentConfig]
    template_id: str | None = None
    
    # Coordination
    lead_agent: str | None = None  # Agent role acting as team lead
    coordination_channel: str | None = None  # Slack channel for coordination
    
    # Sprint configuration
    sprint_config: SprintConfig
    current_sprint_id: str | None = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### 9.2 Inter-Team Communication

```python
# foundrai/orchestration/multi_team_coordinator.py
class MultiTeamCoordinator:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.teams = {}
        self.coordination_bus = MessageBus()
    
    async def coordinate_sprint_planning(self, teams: list[Team]) -> MultiTeamSprintPlan:
        """Coordinate sprint planning across multiple teams."""
        
        # Collect goals from each team
        team_goals = {}
        for team in teams:
            team_goals[team.id] = await self._get_team_goals(team)
        
        # Identify dependencies and conflicts
        dependencies = await self._analyze_dependencies(team_goals)
        conflicts = await self._identify_conflicts(team_goals)
        
        # Generate coordinated plan
        plan = await self._create_coordinated_plan(team_goals, dependencies)
        
        return plan
    
    async def sync_progress(self, teams: list[Team]):
        """Synchronize progress across teams, handle blockers."""
        
    async def handle_cross_team_dependency(self, dependency: CrossTeamDependency):
        """Coordinate when one team needs deliverables from another."""
```

### 9.3 Cross-Team Dependencies

```python
class CrossTeamDependency(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dependent_team_id: str
    provider_team_id: str
    
    # Dependency details
    dependency_type: str  # "api", "component", "data", "deployment"
    title: str
    description: str
    
    # Status tracking
    status: DependencyStatus = DependencyStatus.PENDING
    due_date: datetime | None = None
    
    # Communication
    discussion_thread: str | None = None  # Slack thread
    resolution_notes: str | None = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
```

### 9.4 Team Coordination Dashboard

**Multi-Team Sprint Board**
```typescript
// frontend/src/components/multi-team/MultiTeamSprintBoard.tsx
interface MultiTeamSprintBoardProps {
    teams: Team[];
    dependencies: CrossTeamDependency[];
}

export function MultiTeamSprintBoard({ teams, dependencies }: MultiTeamSprintBoardProps) {
    return (
        <div className="multi-team-board">
            <DependencyGraph dependencies={dependencies} />
            
            <div className="team-lanes">
                {teams.map(team => (
                    <TeamLane key={team.id} team={team} />
                ))}
            </div>
            
            <CoordinationPanel teams={teams} />
        </div>
    );
}
```

---

## 10. Database Schema Changes

### 10.1 New Tables

```sql
-- Plugin management
CREATE TABLE plugins (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    version TEXT NOT NULL,
    type TEXT NOT NULL, -- 'role', 'tool', 'integration'
    metadata TEXT NOT NULL, -- JSON
    config_schema TEXT, -- JSON schema
    installed_at TIMESTAMP NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    UNIQUE(name, version)
);

-- Team templates
CREATE TABLE team_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    author TEXT NOT NULL,
    version TEXT NOT NULL,
    tags TEXT, -- JSON array
    team_config TEXT NOT NULL, -- JSON
    sprint_config TEXT NOT NULL, -- JSON
    required_plugins TEXT, -- JSON array
    recommended_plugins TEXT, -- JSON array
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    is_public BOOLEAN DEFAULT FALSE,
    marketplace_url TEXT,
    downloads INTEGER DEFAULT 0,
    rating REAL DEFAULT 0.0
);

-- Multi-team support
CREATE TABLE teams (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    project_id TEXT NOT NULL,
    agents TEXT NOT NULL, -- JSON array of AgentConfig
    template_id TEXT,
    lead_agent TEXT,
    coordination_channel TEXT,
    sprint_config TEXT NOT NULL, -- JSON
    current_sprint_id TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects (id),
    FOREIGN KEY (template_id) REFERENCES team_templates (id),
    FOREIGN KEY (current_sprint_id) REFERENCES sprints (id)
);

-- Cross-team dependencies  
CREATE TABLE cross_team_dependencies (
    id TEXT PRIMARY KEY,
    dependent_team_id TEXT NOT NULL,
    provider_team_id TEXT NOT NULL,
    dependency_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    due_date TIMESTAMP,
    discussion_thread TEXT,
    resolution_notes TEXT,
    created_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP,
    FOREIGN KEY (dependent_team_id) REFERENCES teams (id),
    FOREIGN KEY (provider_team_id) REFERENCES teams (id)
);

-- Integration configurations
CREATE TABLE integrations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL, -- 'github', 'jira', 'slack'
    project_id TEXT NOT NULL,
    config TEXT NOT NULL, -- JSON configuration
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects (id),
    UNIQUE(name, project_id)
);

-- External task mappings (for Jira/Linear sync)
CREATE TABLE external_task_mappings (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    external_system TEXT NOT NULL, -- 'jira', 'linear'
    external_task_id TEXT NOT NULL,
    external_url TEXT,
    last_sync TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks (id),
    UNIQUE(task_id, external_system)
);

-- Marketplace cache
CREATE TABLE marketplace_cache (
    id TEXT PRIMARY KEY,
    item_type TEXT NOT NULL, -- 'plugin', 'template'
    item_data TEXT NOT NULL, -- JSON
    cached_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL
);
```

### 10.2 Schema Migrations

```python
# foundrai/persistence/migrations/004_phase4.py
def upgrade_phase4(connection: sqlite3.Connection):
    """Apply Phase 4 database schema changes."""
    cursor = connection.cursor()
    
    # Create new tables
    cursor.execute(CREATE_PLUGINS_TABLE)
    cursor.execute(CREATE_TEAM_TEMPLATES_TABLE)
    cursor.execute(CREATE_TEAMS_TABLE)
    cursor.execute(CREATE_CROSS_TEAM_DEPENDENCIES_TABLE)
    cursor.execute(CREATE_INTEGRATIONS_TABLE)
    cursor.execute(CREATE_EXTERNAL_TASK_MAPPINGS_TABLE)
    cursor.execute(CREATE_MARKETPLACE_CACHE_TABLE)
    
    # Add new columns to existing tables
    cursor.execute("ALTER TABLE projects ADD COLUMN template_id TEXT")
    cursor.execute("ALTER TABLE sprints ADD COLUMN team_id TEXT")
    
    connection.commit()
```

---

## 11. API Changes

### 11.1 Plugin Management Endpoints

```python
# foundrai/api/routes/plugins.py (new)
@router.get("/plugins")
async def list_plugins(
    plugin_type: str | None = None,
    enabled_only: bool = True
) -> list[PluginInfo]:
    """List installed plugins."""

@router.post("/plugins/install")
async def install_plugin(request: InstallPluginRequest) -> PluginInfo:
    """Install plugin from marketplace or local file."""

@router.delete("/plugins/{plugin_id}")
async def uninstall_plugin(plugin_id: str) -> dict:
    """Uninstall plugin."""

@router.put("/plugins/{plugin_id}/toggle")
async def toggle_plugin(plugin_id: str, enabled: bool) -> PluginInfo:
    """Enable or disable plugin."""
```

### 11.2 Team Template Endpoints

```python
# foundrai/api/routes/templates.py (new)
@router.get("/templates")
async def list_templates(source: str = "all") -> list[TeamTemplate]:
    """List available templates (local, marketplace, or both)."""

@router.post("/templates")
async def create_template(request: CreateTemplateRequest) -> TeamTemplate:
    """Create template from current project configuration."""

@router.get("/templates/{template_id}")
async def get_template(template_id: str) -> TeamTemplate:
    """Get template details."""

@router.post("/templates/{template_id}/apply")
async def apply_template(
    template_id: str, 
    project_id: str
) -> dict:
    """Apply template to project."""

@router.post("/templates/{template_id}/publish")
async def publish_template(
    template_id: str,
    marketplace_config: PublishConfig
) -> dict:
    """Publish template to marketplace."""
```

### 11.3 Multi-Team Endpoints

```python
# foundrai/api/routes/teams.py (new)
@router.get("/projects/{project_id}/teams")
async def list_teams(project_id: str) -> list[Team]:
    """List teams in project."""

@router.post("/projects/{project_id}/teams")
async def create_team(project_id: str, team: CreateTeamRequest) -> Team:
    """Create new team in project."""

@router.get("/teams/{team_id}/dependencies")
async def list_dependencies(team_id: str) -> list[CrossTeamDependency]:
    """List dependencies for team."""

@router.post("/teams/{team_id}/dependencies")
async def create_dependency(
    team_id: str, 
    dependency: CreateDependencyRequest
) -> CrossTeamDependency:
    """Create cross-team dependency."""
```

### 11.4 Integration Endpoints

```python
# foundrai/api/routes/integrations.py (new)
@router.get("/projects/{project_id}/integrations")
async def list_integrations(project_id: str) -> list[IntegrationConfig]:
    """List configured integrations."""

@router.post("/projects/{project_id}/integrations/{integration_name}/enable")
async def enable_integration(
    project_id: str,
    integration_name: str,
    config: dict
) -> IntegrationConfig:
    """Enable and configure integration."""

@router.post("/integrations/github/webhook")
async def github_webhook(request: GitHubWebhookRequest) -> dict:
    """Handle GitHub webhook events."""

@router.post("/integrations/slack/events")
async def slack_events(request: SlackEventRequest) -> dict:
    """Handle Slack events and interactions."""
```

---

## 12. Frontend Changes

### 12.1 Plugin Management UI

```typescript
// frontend/src/pages/PluginsPage.tsx (new)
export function PluginsPage() {
    const [plugins, setPlugins] = useState<Plugin[]>([]);
    const [marketplacePlugins, setMarketplacePlugins] = useState<PluginListing[]>([]);

    return (
        <div className="plugins-page">
            <h1>Plugin Management</h1>
            
            <Tabs defaultValue="installed">
                <TabsList>
                    <TabsTrigger value="installed">Installed</TabsTrigger>
                    <TabsTrigger value="marketplace">Marketplace</TabsTrigger>
                </TabsList>
                
                <TabsContent value="installed">
                    <InstalledPluginsList plugins={plugins} />
                </TabsContent>
                
                <TabsContent value="marketplace">
                    <MarketplacePluginsList plugins={marketplacePlugins} />
                </TabsContent>
            </Tabs>
        </div>
    );
}
```

### 12.2 Team Template UI

```typescript
// frontend/src/pages/TemplatesPage.tsx (new)
export function TemplatesPage() {
    return (
        <div className="templates-page">
            <h1>Team Templates</h1>
            
            <div className="template-actions">
                <Button onClick={() => createTemplate()}>
                    Save Current Configuration
                </Button>
                <Button variant="secondary" onClick={() => browseMarketplace()}>
                    Browse Marketplace
                </Button>
            </div>
            
            <TemplateGrid templates={templates} />
        </div>
    );
}
```

### 12.3 Multi-Team Dashboard

```typescript
// frontend/src/pages/MultiTeamDashboard.tsx (new)
export function MultiTeamDashboard() {
    const { teams, dependencies } = useMultiTeamData();
    
    return (
        <div className="multi-team-dashboard">
            <MultiTeamSprintBoard teams={teams} dependencies={dependencies} />
            <DependencyTracker dependencies={dependencies} />
            <TeamCoordinationPanel teams={teams} />
        </div>
    );
}
```

### 12.4 Integration Setup UI

```typescript
// frontend/src/components/integrations/IntegrationSetup.tsx (new)
export function IntegrationSetup({ integration }: { integration: string }) {
    const [config, setConfig] = useState({});
    
    return (
        <div className="integration-setup">
            <h3>Configure {integration}</h3>
            
            {integration === "github" && (
                <GitHubIntegrationForm 
                    config={config} 
                    onChange={setConfig} 
                />
            )}
            
            {integration === "slack" && (
                <SlackIntegrationForm 
                    config={config} 
                    onChange={setConfig} 
                />
            )}
            
            <Button onClick={() => enableIntegration(integration, config)}>
                Enable Integration
            </Button>
        </div>
    );
}
```

---

## 13. Testing Strategy

### 13.1 Plugin System Tests

```python
# tests/test_plugin_system.py (new)
class TestPluginLoader:
    def test_discover_valid_plugins(self):
        """Test plugin discovery finds valid plugins."""
        
    def test_load_role_plugin(self):
        """Test loading a role plugin."""
        
    def test_plugin_dependency_resolution(self):
        """Test plugin dependency resolution."""
        
    def test_plugin_validation_security(self):
        """Test plugin security validation."""

class TestPluginIntegration:
    def test_custom_role_in_sprint(self):
        """Test using custom role plugin in a sprint."""
        
    def test_custom_tool_execution(self):
        """Test executing custom tool from plugin."""
```

### 13.2 Integration Tests

```python
# tests/test_integrations.py (new)
class TestGitHubIntegration:
    async def test_create_repository(self):
        """Test GitHub repository creation."""
        
    async def test_create_pull_request(self):
        """Test pull request creation."""
        
    async def test_sync_tasks_to_issues(self):
        """Test syncing tasks to GitHub issues."""

class TestSlackIntegration:
    async def test_send_notification(self):
        """Test sending Slack notifications."""
        
    async def test_handle_approval_button(self):
        """Test handling approval button clicks."""
        
    async def test_slash_command_status(self):
        """Test /foundrai status command."""

class TestProjectManagementSync:
    async def test_jira_bidirectional_sync(self):
        """Test bi-directional sync with Jira."""
        
    async def test_linear_task_creation(self):
        """Test Linear task creation."""
```

### 13.3 Multi-Team Tests

```python
# tests/test_multi_team.py (new)
class TestMultiTeamCoordination:
    async def test_cross_team_dependency_creation(self):
        """Test creating cross-team dependencies."""
        
    async def test_coordinated_sprint_planning(self):
        """Test coordinated sprint planning across teams."""
        
    async def test_dependency_resolution(self):
        """Test resolving cross-team dependencies."""
```

### 13.4 E2E Integration Tests

```python
# tests/test_phase4_integration.py (new)
class TestPhase4Integration:
    async def test_full_plugin_workflow(self):
        """Test: install plugin → use in sprint → verify results."""
        
    async def test_template_apply_workflow(self):
        """Test: create template → share → apply to new project."""
        
    async def test_github_integration_workflow(self):
        """Test: enable GitHub → run sprint → verify repo/PRs created."""
        
    async def test_multi_team_coordination_workflow(self):
        """Test: create multiple teams → coordinate sprint → resolve dependencies."""
```

### 13.5 Frontend Component Tests

```typescript
// frontend/src/components/__tests__/PluginManagement.test.tsx (new)
describe('Plugin Management', () => {
    test('displays installed plugins', () => {
        // Test plugin list display
    });
    
    test('installs plugin from marketplace', () => {
        // Test plugin installation flow
    });
    
    test('toggles plugin enabled state', () => {
        // Test enabling/disabling plugins
    });
});
```

---

## Phase 4 Implementation Summary

Phase 4 transforms FoundrAI into a comprehensive ecosystem with:

1. **Plugin Architecture** — Extensible system for custom roles, tools, and integrations
2. **Team Templates** — Save, share, and reuse team configurations
3. **GitHub Integration** — Agents create real repos, branches, and pull requests
4. **Jira/Linear Sync** — Bi-directional task synchronization with external PM tools
5. **Slack Integration** — Team notifications, approvals, and coordination via Slack
6. **Community Marketplace** — Discover, install, and share plugins and templates
7. **Enhanced DevOps** — Real CI/CD capabilities with infrastructure management
8. **Multi-Team Support** — Coordinate multiple AI teams on complex projects

### Key Architectural Changes

- **Plugin system** with secure sandboxing and dependency resolution
- **Multi-team coordination** with cross-team dependency tracking  
- **Integration framework** for external service connections
- **Template system** for configuration sharing and reuse
- **Marketplace client** for community-driven ecosystem growth

### Backward Compatibility

All Phase 0-3 functionality remains intact. Phase 4 is purely additive, with existing projects continuing to work without changes while gaining access to new ecosystem features.