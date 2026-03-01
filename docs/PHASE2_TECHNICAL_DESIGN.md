# FoundrAI — Phase 2 Technical Design Document

> **Status:** Draft  
> **Version:** 1.0  
> **Date:** 2026-03-01  
> **Scope:** Agile Engine — Full sprint lifecycle with iteration and learning  
> **Depends on:** Phase 0 (Foundation) ✅, Phase 1 (Visual Layer) ✅

---

## Table of Contents

1. [Scope & Goals](#1-scope--goals)
2. [Sprint Ceremonies](#2-sprint-ceremonies)
3. [Parallel Task Execution](#3-parallel-task-execution)
4. [VectorMemory Integration](#4-vectormemory-integration)
5. [Multi-Sprint Support](#5-multi-sprint-support)
6. [New Agent Roles](#6-new-agent-roles)
7. [Per-Agent Autonomy Configuration](#7-per-agent-autonomy-configuration)
8. [Multi-Model Support](#8-multi-model-support)
9. [Backend Changes](#9-backend-changes)
10. [Frontend Changes](#10-frontend-changes)
11. [Database Schema Changes](#11-database-schema-changes)
12. [API Changes](#12-api-changes)
13. [Testing Strategy](#13-testing-strategy)

---

## 1. Scope & Goals

### What Phase 2 Delivers

Phase 2 transforms FoundrAI from a single-pass sprint into a full **Agile engine** with ceremonies, parallel execution, persistent learning via vector memory, and multi-sprint iteration.

### Deliverables

| Deliverable | Description |
|---|---|
| Sprint Planning ceremony | PM decomposes, team estimates effort, prioritizes |
| Parallel task execution | Concurrent execution where dependencies allow |
| Sprint Review ceremony | Agents present work, quality scoring |
| Sprint Retrospective | Agents analyze perf, generate learnings |
| VectorMemory (ChromaDB) | Persistent learnings across sprints |
| Multi-sprint support | Learnings carry forward, backlog rolls over |
| Architect agent | System design, tech decisions |
| Designer agent | UI/UX specs, design decisions |
| Per-agent autonomy UI | Configure autonomy per agent in frontend |
| Multi-model support | Assign different LLMs per agent role |

### Definition of Done

A user can run multiple sprints on the same project and observe the AI team improving its process and output quality over time.

---

## 2. Sprint Ceremonies

### 2.1 Sprint Planning

The planning phase expands from simple PM decomposition to a team ceremony:

1. PM decomposes goal into tasks (existing)
2. **NEW**: Architect reviews task list and adds technical considerations
3. **NEW**: Team "estimates" effort (token budget per task)
4. **NEW**: PM prioritizes final backlog based on estimates + dependencies

```python
# foundrai/orchestration/ceremonies.py

class SprintPlanning:
    """Sprint Planning ceremony orchestrator."""
    
    async def run(self, goal: str, agents: dict, context: SprintContext, 
                  vector_memory: VectorMemory | None = None) -> list[Task]:
        """Run full planning ceremony."""
        # 1. PM decomposes
        tasks = await agents["product_manager"].decompose_goal(goal)
        
        # 2. Architect reviews (if available)
        if "architect" in agents:
            tasks = await agents["architect"].review_plan(tasks, context)
        
        # 3. Retrieve past learnings
        if vector_memory:
            learnings = await vector_memory.query_relevant(goal, k=5)
            if learnings:
                tasks = await agents["product_manager"].refine_with_learnings(tasks, learnings)
        
        # 4. Estimate effort
        for task in tasks:
            task.estimated_tokens = self._estimate_effort(task)
        
        return tasks
    
    def _estimate_effort(self, task: Task) -> int:
        """Heuristic effort estimation based on task complexity."""
        base = 1000
        base += len(task.acceptance_criteria) * 500
        base += len(task.description) * 2
        return min(base, 8000)
```

### 2.2 Sprint Review

After execution, agents present completed work for quality scoring:

```python
class SprintReview:
    """Sprint Review ceremony — agents present work, quality assessed."""
    
    async def run(self, state: SprintState, agents: dict) -> ReviewSummary:
        """Run sprint review."""
        completed = [t for t in state["tasks"] if t.status == TaskStatus.DONE]
        failed = [t for t in state["tasks"] if t.status == TaskStatus.FAILED]
        
        # QA provides overall quality score
        if "qa_engineer" in agents:
            quality_score = await agents["qa_engineer"].score_sprint(completed)
        else:
            quality_score = self._auto_score(completed, failed)
        
        return ReviewSummary(
            completed_count=len(completed),
            failed_count=len(failed),
            quality_score=quality_score,
            incomplete_tasks=[t for t in state["tasks"] 
                            if t.status not in (TaskStatus.DONE, TaskStatus.FAILED)],
        )
```

### 2.3 Sprint Retrospective

Agents analyze what went well/wrong and generate learnings for vector memory:

```python
class SprintRetrospective:
    """Sprint Retrospective — analyze and learn."""
    
    async def run(self, state: SprintState, agents: dict, 
                  vector_memory: VectorMemory | None = None) -> RetroSummary:
        """Run retrospective, store learnings."""
        # PM generates retrospective analysis
        pm = agents.get("product_manager")
        if not pm:
            return RetroSummary(learnings=[])
        
        analysis = await pm.run_retrospective(state)
        
        # Store learnings in vector memory
        if vector_memory and analysis.learnings:
            for learning in analysis.learnings:
                await vector_memory.store_learning(learning)
        
        return analysis
```

---

## 3. Parallel Task Execution

### Design

Replace sequential execution with concurrent execution using `asyncio.gather` for tasks whose dependencies are all satisfied:

```python
async def _execute_node(self, state: SprintState) -> SprintState:
    """Execute tasks in parallel where dependencies allow."""
    while True:
        ready = self.task_graph.get_ready_tasks()
        if not ready:
            break
        
        # Execute ready tasks concurrently
        results = await asyncio.gather(
            *[self._execute_single_task(task, state) for task in ready],
            return_exceptions=True,
        )
        
        # Process results
        for task, result in zip(ready, results):
            if isinstance(result, Exception):
                task.status = TaskStatus.FAILED
            # ... handle result
        
        # Check if we made progress
        if not any(t.status == TaskStatus.DONE for t in ready):
            break  # All failed, stop
```

The `max_tasks_parallel` config setting (existing in `SprintConfig`) limits concurrency via `asyncio.Semaphore`.

---

## 4. VectorMemory Integration

### ChromaDB-backed persistent memory

```python
# foundrai/persistence/vector_memory.py

class VectorMemory:
    """ChromaDB-based vector memory for persistent learnings."""
    
    def __init__(self, config: MemoryConfig) -> None:
        import chromadb
        self.client = chromadb.PersistentClient(path=config.chromadb_path)
        self.collection = self.client.get_or_create_collection(
            name="foundrai_learnings",
            metadata={"hnsw:space": "cosine"},
        )
    
    async def store_learning(self, learning: Learning) -> None:
        """Store a learning in vector memory."""
        self.collection.add(
            ids=[learning.id],
            documents=[learning.content],
            metadatas=[{
                "sprint_id": learning.sprint_id,
                "project_id": learning.project_id,
                "category": learning.category,
                "timestamp": learning.timestamp,
            }],
        )
    
    async def query_relevant(self, query: str, k: int = 5, 
                             project_id: str | None = None) -> list[Learning]:
        """Query for relevant learnings."""
        where = {"project_id": project_id} if project_id else None
        results = self.collection.query(
            query_texts=[query], n_results=k, where=where,
        )
        return self._parse_results(results)
```

### Learning Model

```python
class Learning(BaseModel):
    """A learning stored in vector memory."""
    id: str = Field(default_factory=generate_id)
    content: str
    category: str  # "process", "technical", "quality", "estimation"
    sprint_id: str
    project_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
```

---

## 5. Multi-Sprint Support

### Backlog Rollover

Failed/incomplete tasks from Sprint N are automatically added to Sprint N+1's backlog.

### Learnings Carry Forward

The retrospective learnings from Sprint N are queried during Sprint N+1's planning phase, allowing the team to improve.

### Engine Changes

```python
async def run_sprint(self, goal: str, project_id: str) -> SprintState:
    # Get previous sprint's incomplete tasks
    prev = await self.sprint_store.get_latest_sprint(project_id)
    rollover_tasks = []
    if prev:
        rollover_tasks = [t for t in prev.get("tasks", []) 
                         if t.status not in (TaskStatus.DONE,)]
    
    # Planning with learnings
    planning = SprintPlanning()
    tasks = await planning.run(goal, self.agents, context, self.vector_memory)
    
    # Add rollover tasks
    tasks.extend(rollover_tasks)
    ...
```

---

## 6. New Agent Roles

### 6.1 Architect Agent

```python
class ArchitectAgent(BaseAgent):
    """Architect — system design, tech decisions, plan review."""
    
    PERSONA = """You are a senior software architect. You make high-level technical 
decisions, review system designs, and ensure code quality and architectural consistency.

When reviewing a plan:
1. Evaluate technical feasibility
2. Identify architectural concerns
3. Suggest technical approach for each task
4. Add technical acceptance criteria

When reviewing code:
1. Check architectural patterns
2. Verify consistency with design decisions
3. Flag technical debt

Return structured JSON responses."""
    
    async def review_plan(self, tasks: list[Task], context: SprintContext) -> list[Task]:
        """Review and enhance the task plan with technical considerations."""
        ...
    
    async def execute_task(self, task: Task) -> TaskResult:
        """Execute architecture/design tasks."""
        ...
```

### 6.2 Designer Agent

```python
class DesignerAgent(BaseAgent):
    """Designer — UI/UX specs, design decisions."""
    
    PERSONA = """You are a senior UI/UX designer. You create design specifications,
wireframe descriptions, and ensure consistent user experience.

When given a task:
1. Create detailed UI/UX specifications
2. Define component hierarchy
3. Specify user interactions and flows
4. Document design decisions

Return design specs as structured documents."""
    
    async def execute_task(self, task: Task) -> TaskResult:
        """Execute design tasks."""
        ...
```

---

## 7. Per-Agent Autonomy Configuration

### API Endpoint

```
PUT /api/projects/{project_id}/agents/{agent_role}/config
```

```python
class AgentConfigUpdate(BaseModel):
    autonomy_level: AutonomyLevel | None = None
    model: str | None = None
    enabled: bool | None = None
```

### Frontend

New "Team" tab in SprintPage showing each agent with autonomy dropdown and model selector.

---

## 8. Multi-Model Support

Each agent role can be assigned a different LLM model. The config already supports this via `TeamConfig.{role}.model`. Phase 2 makes this configurable at runtime via API and visible in the UI.

---

## 9. Backend Changes

### New Files

| File | Purpose |
|---|---|
| `foundrai/orchestration/ceremonies.py` | Planning, Review, Retrospective |
| `foundrai/persistence/vector_memory.py` | ChromaDB integration |
| `foundrai/models/learning.py` | Learning data model |
| `foundrai/agents/personas/architect.py` | Architect agent |
| `foundrai/agents/personas/designer.py` | Designer agent |
| `foundrai/api/routes/agents.py` | Agent config endpoints |

### Modified Files

| File | Changes |
|---|---|
| `foundrai/orchestration/engine.py` | Parallel execution, ceremonies, vector memory |
| `foundrai/agents/roles.py` | Register architect + designer roles |
| `foundrai/models/sprint.py` | Add review/retro summaries to state |
| `foundrai/models/task.py` | Add estimated_tokens field |
| `foundrai/config.py` | Already supports all needed config |
| `foundrai/api/app.py` | Add agents route |

---

## 10. Frontend Changes

### New Components

| Component | Purpose |
|---|---|
| `TeamPanel.tsx` | Agent config panel (autonomy, model) |
| `RetrospectiveView.tsx` | Display retrospective learnings |
| `SprintHistory.tsx` | Multi-sprint timeline |

### Modified Components

| Component | Changes |
|---|---|
| `SprintPage.tsx` | Add Team + History tabs |
| `AgentAvatar.tsx` | Support architect + designer roles |
| `FeedFilters.tsx` | Add new agent roles to filter |
| `types/index.ts` | Add new types |

---

## 11. Database Schema Changes

```sql
-- Learnings table
CREATE TABLE IF NOT EXISTS learnings (
    learning_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    sprint_id TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_learnings_project ON learnings(project_id);
CREATE INDEX IF NOT EXISTS idx_learnings_sprint ON learnings(sprint_id);

-- Sprint review/retro results
-- Stored as JSON in sprints.metrics_json (extended)

-- Agent config table
CREATE TABLE IF NOT EXISTS agent_configs (
    project_id TEXT NOT NULL,
    agent_role TEXT NOT NULL,
    autonomy_level TEXT NOT NULL DEFAULT 'notify',
    model TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (project_id, agent_role)
);
```

---

## 12. API Changes

### New Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/projects/{id}/agents` | List agent configs |
| `PUT` | `/api/projects/{id}/agents/{role}` | Update agent config |
| `GET` | `/api/sprints/{id}/retrospective` | Get retro results |
| `GET` | `/api/projects/{id}/learnings` | List learnings |

---

## 13. Testing Strategy

### Unit Tests

- `test_ceremonies.py` — Planning, Review, Retrospective
- `test_vector_memory.py` — ChromaDB integration
- `test_parallel_execution.py` — Parallel task execution
- `test_architect.py` — Architect agent
- `test_designer.py` — Designer agent
- `test_multi_sprint.py` — Multi-sprint with learning carryover

### Integration Tests

- `test_integration_multi_sprint.py` — Full multi-sprint lifecycle

### Frontend Tests

- Component rendering for new components
- Store updates for new state
