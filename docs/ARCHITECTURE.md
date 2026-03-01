# FoundrAI — System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Frontend Layer                     │
│  Sprint Board │ Agent Feed │ Goal Tree │ Metrics     │
├─────────────────────────────────────────────────────┤
│                    API Layer                          │
│    REST API (FastAPI) │ WebSocket │ CLI (Typer)      │
├─────────────────────────────────────────────────────┤
│               Orchestration Layer                    │
│  SprintEngine │ TaskGraph │ MessageBus │ HumanGate  │
├─────────────────────────────────────────────────────┤
│                   Agent Layer                        │
│  AgentRuntime │ RoleRegistry │ ToolKit │ Memory     │
├─────────────────────────────────────────────────────┤
│               Persistence Layer                      │
│  SprintStore │ ArtifactStore │ EventLog │ VectorMem │
└─────────────────────────────────────────────────────┘
```

## 1. Agent Layer

The brain of FoundrAI — individual AI agents with specialized roles.

### AgentRuntime
Core agent execution loop. Each agent instance contains:
- **Role definition** — System prompt defining persona, skills, and boundaries
- **Tool set** — Available tools for this role (e.g., Developer gets code_executor, Architect gets file_manager)
- **Working memory** — Current sprint context, conversation buffer (short-term)
- **Long-term memory** — Past decisions, learnings via vector store queries

**Technology:** LangGraph ReAct agent + LiteLLM for model abstraction

### RoleRegistry
Defines available agent roles with configurable attributes:

```python
class AgentRole(BaseModel):
    name: str                          # e.g., "ProductManager"
    persona: str                       # System prompt template
    skills: list[str]                  # Capability descriptors
    tools: list[str]                   # Tool names this role can use
    default_model: str                 # LiteLLM model string
    autonomy_level: AutonomyLevel      # auto, notify, require_approval, block
    max_tokens_per_action: int         # Cost control per action
```

Roles are defined in YAML config files for easy customization:

```yaml
# roles/product_manager.yaml
name: ProductManager
persona: |
  You are a senior Product Manager at a startup. You excel at breaking down
  ambiguous goals into clear, actionable user stories with acceptance criteria.
  You think in terms of user value and prioritize ruthlessly.
skills:
  - goal_decomposition
  - story_writing
  - backlog_prioritization
  - stakeholder_communication
tools:
  - web_search
  - file_manager
default_model: anthropic/claude-sonnet-4-20250514
autonomy_level: notify
```

### ToolKit
Extensible tool system for agent capabilities:

| Tool | Description | Used By |
|------|-------------|---------|
| code_executor | Sandboxed code execution (Docker/E2B) | Developer, QA |
| file_manager | Read/write/list project files | All agents |
| web_search | Search the web for information | PM, Architect, Developer |
| github_api | Create repos, branches, PRs, issues | Developer, DevOps |
| terminal | Run shell commands (sandboxed) | Developer, DevOps |
| image_generator | Generate UI mockups/wireframes | Designer |

### AgentMemory
Two-tier memory architecture:

**Working Memory (Short-term):**
- Current sprint context (goal, tasks, status)
- Recent conversation buffer (last N messages)
- Current task details and acceptance criteria

**Long-term Memory (Persistent):**
- Past sprint decisions and outcomes (ChromaDB embeddings)
- Code patterns and architecture decisions
- Retrospective learnings
- Team collaboration patterns

## 2. Orchestration Layer

The conductor — manages the Agile workflow and agent coordination.

### SprintEngine
Core state machine managing the sprint lifecycle:

```
┌──────────┐     ┌───────────┐     ┌──────────┐     ┌───────────┐
│ PLANNING │────→│ EXECUTING │────→│ REVIEWING│────→│   RETRO   │
└──────────┘     └───────────┘     └──────────┘     └───────────┘
     ↑                                                     │
     └─────────────────────────────────────────────────────┘
                        (Next Sprint)
```

**Implementation:** LangGraph StateGraph with checkpointing. Each state is a node in the graph with conditional edges based on sprint status.

**Sprint State Schema:**
```python
class SprintState(TypedDict):
    project_id: str
    sprint_number: int
    goal: str
    status: SprintStatus  # planning, executing, reviewing, retro, completed
    tasks: list[Task]
    agent_assignments: dict[str, str]  # task_id → agent_role
    messages: list[AgentMessage]
    artifacts: list[Artifact]
    metrics: SprintMetrics
    human_decisions: list[HumanDecision]
```

### TaskGraph
Directed Acyclic Graph (DAG) of tasks with dependencies:

```python
class TaskGraph:
    """Manages task dependencies and execution order."""
    
    def add_task(self, task: Task, depends_on: list[str] = None) -> None: ...
    def get_ready_tasks(self) -> list[Task]:
        """Return tasks whose dependencies are all completed."""
    def mark_completed(self, task_id: str, result: TaskResult) -> None: ...
    def get_critical_path(self) -> list[Task]: ...
    def visualize(self) -> dict:
        """Return graph data for frontend visualization."""
```

**Technology:** NetworkX for graph operations + custom scheduler for parallel execution.

### MessageBus
Inter-agent communication with typed messages:

```python
class MessageType(Enum):
    TASK_ASSIGNMENT = "task_assignment"
    CODE_REVIEW = "code_review"
    BUG_REPORT = "bug_report"
    QUESTION = "question"
    DECISION = "decision"
    STATUS_UPDATE = "status_update"
    APPROVAL_REQUEST = "approval_request"

class AgentMessage(BaseModel):
    id: str
    type: MessageType
    from_agent: str
    to_agent: str | None  # None = broadcast to team
    content: str
    metadata: dict
    timestamp: datetime
```

All messages are:
1. Logged to EventLog (persistence)
2. Streamed via WebSocket to frontend (real-time UI)
3. Delivered to target agent's working memory

### HumanGateway
Policy-based approval engine:

```python
class ApprovalPolicy(BaseModel):
    agent_role: str
    action_type: str          # "code_commit", "architecture_decision", "deploy", etc.
    policy: PolicyType         # auto_approve, notify, require_approval, block
    conditions: dict | None   # Optional conditions (e.g., "if lines_changed > 50")

# Example policies:
policies = [
    ApprovalPolicy(agent_role="Developer", action_type="code_commit", policy="auto_approve", conditions={"lines_changed_lt": 50}),
    ApprovalPolicy(agent_role="Developer", action_type="code_commit", policy="require_approval", conditions={"lines_changed_gte": 50}),
    ApprovalPolicy(agent_role="Architect", action_type="architecture_decision", policy="require_approval"),
    ApprovalPolicy(agent_role="DevOps", action_type="deploy", policy="require_approval"),
    ApprovalPolicy(agent_role="QA", action_type="bug_report", policy="notify"),
]
```

### AgileCoordinator
Implements Agile ceremonies as LangGraph sub-graphs:

**Sprint Planning:**
1. PM agent receives high-level goal
2. PM decomposes into epics → stories → tasks
3. Architect reviews technical feasibility
4. Team "estimates" (agent confidence scores)
5. Human reviews and approves sprint backlog

**Daily Sync (Automated):**
- Each agent reports: what they completed, what they're working on, blockers
- SprintEngine aggregates into status update
- Streamed to frontend dashboard

**Sprint Review:**
- Agents present completed artifacts
- QA reports test results
- Quality scores calculated
- Incomplete tasks return to backlog

**Retrospective:**
- Agents analyze: what worked, what didn't, what to improve
- Learnings stored in VectorMemory
- Process adjustments applied to next sprint config

## 3. Persistence Layer

### SprintStore
- Sprint metadata, task states, agent assignments
- Full history for retrospective analysis
- **Tech:** SQLite with async access via aiosqlite

### ArtifactStore
- Generated artifacts: PRDs, code, tests, designs, docs
- Versioned and linked to source task
- **Tech:** File system + SQLite index

### EventLog
- Append-only event stream
- Every agent message, state transition, tool call, human decision
- Enables full replay and debugging
- **Tech:** SQLite + structured JSON logging

### VectorMemory
- Embeddings of decisions, code patterns, learnings
- Queried by agents for context-aware decisions
- Grows smarter over time
- **Tech:** ChromaDB (embedded, zero-config)

## 4. API Layer

### REST API (FastAPI)
```
POST   /api/projects                  # Create project
GET    /api/projects/{id}             # Get project details
POST   /api/projects/{id}/team        # Configure team
POST   /api/projects/{id}/sprints     # Start new sprint
GET    /api/projects/{id}/sprints     # List sprints
GET    /api/sprints/{id}              # Sprint details
POST   /api/sprints/{id}/approve      # Approve pending decision
POST   /api/sprints/{id}/reject       # Reject pending decision
GET    /api/sprints/{id}/tasks        # List tasks
GET    /api/sprints/{id}/messages     # Get agent messages
GET    /api/sprints/{id}/artifacts    # List artifacts
GET    /api/sprints/{id}/metrics      # Sprint metrics
```

### WebSocket Server
```
WS /ws/sprints/{id}/feed             # Real-time sprint activity stream
```

Events streamed:
- `task.status_changed` — Task moved between columns
- `agent.message` — Inter-agent communication
- `agent.tool_call` — Agent used a tool
- `agent.reasoning` — Agent's chain of thought
- `sprint.status_changed` — Sprint phase transition
- `human.approval_required` — Approval gate triggered
- `artifact.created` — New artifact generated

### CLI Interface (Typer)
```bash
$ foundrai init my-project            # Initialize project
$ foundrai team create                # Interactive team setup
$ foundrai team show                  # Display team configuration
$ foundrai sprint start "Build a REST API for todo app"  # Start sprint
$ foundrai status                     # Current sprint status
$ foundrai logs                       # Stream agent activity
$ foundrai logs --agent Developer     # Filter by agent
$ foundrai serve                      # Start web dashboard (API + frontend)
$ foundrai serve --port 8080          # Custom port
```

## 5. Frontend Layer

### Sprint Board (SprintBoard.tsx)
- Real-time Kanban with columns: Backlog, In Progress, In Review, Done
- Cards show: task title, assigned agent (avatar + color), progress, time elapsed
- Drag to reprioritize (sends to API)
- Click to expand: full task details, agent reasoning, linked artifacts

### Agent Activity Feed (AgentFeed.tsx)
- Scrollable timeline of all agent activity
- Color-coded by agent role
- Filterable by agent, message type, time range
- Expandable entries showing full reasoning traces and tool calls
- Decision points highlighted with approve/reject buttons

### Goal Decomposition View (GoalTree.tsx)
- Interactive tree/graph: Goal → Epics → Stories → Tasks
- Created by PM agent during sprint planning
- Editable by human: add, remove, reprioritize nodes
- Visual progress indicators on each node
- **Tech:** React Flow for interactive graph

### Metrics Dashboard (MetricsDash.tsx)
- Sprint velocity (tasks completed per sprint)
- Token cost breakdown (per agent, per sprint)
- Agent performance scores
- Quality metrics (bugs found, test pass rate)
- Historical trends across sprints
- **Tech:** Recharts for data visualization

### Control Panel (ControlPanel.tsx)
- Team composition (add/remove agent roles)
- Per-agent settings: LLM model, autonomy level, token budget
- Approval policies configuration
- Sprint settings: duration, max parallel tasks
- Project-level settings
