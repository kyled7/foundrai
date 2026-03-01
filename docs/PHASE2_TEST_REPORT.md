# FoundrAI — Phase 2 Test Report

> **Date:** 2026-03-01 (updated after bugfix pass)  
> **Phase:** Phase 2 — Agile Engine  
> **Result:** ✅ ALL PASS

---

## Bugfixes Applied (2026-03-01)

1. **QA agent crash on execution** — Engine now skips QA in execute node; QA only called in review node
2. **Hardcoded/invalid model names** — All defaults unified to `anthropic/claude-sonnet-4-20250514`
3. **CLI/Dashboard DB mismatch** — `foundrai serve` now resolves DB path relative to project directory
4. **SPA routing 404s** — Added catch-all route serving `index.html` for non-API paths

---

## Test Results

```
159 passed in 2.83s
Overall coverage: 79%
```

### Test Breakdown

| Test Suite | Tests | Status |
|---|---|---|
| `test_agents/test_base.py` | 3 | ✅ |
| `test_agents/test_roles.py` | 2 | ✅ |
| `test_agents/test_runtime.py` | 18 | ✅ |
| `test_api/test_approvals.py` | 4 | ✅ |
| `test_api/test_events.py` | 4 | ✅ |
| `test_api/test_projects.py` | 5 | ✅ |
| `test_api/test_sprints.py` | 8 | ✅ |
| `test_api/test_tasks.py` | 3 | ✅ |
| `test_api/test_websocket.py` | 2 | ✅ |
| `test_cli.py` | 15 | ✅ |
| `test_config.py` | 5 | ✅ |
| `test_integration_sprint.py` | 5 | ✅ |
| `test_models/test_enums.py` | 5 | ✅ |
| `test_models/test_sprint.py` | 4 | ✅ |
| `test_models/test_task.py` | 7 | ✅ |
| `test_orchestration/test_engine.py` | 11 | ✅ |
| `test_orchestration/test_message_bus.py` | 4 | ✅ |
| `test_orchestration/test_task_graph.py` | 9 | ✅ |
| `test_persistence/test_database.py` | 3 | ✅ |
| `test_persistence/test_event_log.py` | 3 | ✅ |
| `test_persistence/test_sprint_store.py` | 4 | ✅ |
| **Phase 2 New Tests** | | |
| `test_phase2/test_ceremonies.py` | 9 | ✅ |
| `test_phase2/test_new_agents.py` | 7 | ✅ |
| `test_phase2/test_parallel_execution.py` | 3 | ✅ |
| `test_phase2/test_multi_sprint.py` | 4 | ✅ |
| `test_phase2/test_vector_memory.py` | 6 | ✅ |

### Lint

```
ruff check foundrai/ → All checks passed!
ruff check tests/test_phase2/ → All checks passed!
```

### Frontend Build

```
tsc && vite build → ✓ built in 1.08s (0 errors, 0 warnings)
```

---

## Phase 2 Features Implemented

### Backend

1. **Sprint Ceremonies** (`foundrai/orchestration/ceremonies.py`)
   - `SprintPlanning` — PM decomposition + architect review + learning integration + effort estimation
   - `SprintReview` — Quality scoring of completed work
   - `SprintRetrospective` — Analysis, learning generation, vector memory storage

2. **Parallel Task Execution** (`foundrai/orchestration/engine.py`)
   - Wave-based parallel execution using `asyncio.gather`
   - Respects task dependencies via `TaskGraph.get_ready_tasks()`
   - Configurable concurrency limit via `SprintConfig.max_tasks_parallel`

3. **VectorMemory Integration** (`foundrai/persistence/vector_memory.py`)
   - ChromaDB-backed persistent learning storage
   - Query relevant learnings by similarity
   - Project-scoped filtering

4. **Multi-Sprint Support**
   - Sprint numbers auto-increment per project
   - Learnings stored in vector memory carry across sprints
   - Planning ceremony queries past learnings to refine tasks

5. **Architect Agent** (`foundrai/agents/personas/architect.py`)
   - Plan review with technical considerations
   - Adds technical acceptance criteria
   - Can execute architecture/design tasks

6. **Designer Agent** (`foundrai/agents/personas/designer.py`)
   - UI/UX design task execution
   - Design specification generation

7. **Per-Agent Autonomy Configuration** (`foundrai/api/routes/agents.py`)
   - `GET /api/projects/{id}/agents` — list agent configs
   - `PUT /api/projects/{id}/agents/{role}` — update autonomy, model, enabled

8. **Multi-Model Support**
   - Each agent role can have a different LLM model
   - Configurable via API and frontend

9. **Learnings API** (`foundrai/api/routes/learnings.py`)
   - `GET /api/projects/{id}/learnings` — list project learnings
   - `GET /api/sprints/{id}/retrospective` — get retro results

### Frontend

1. **TeamPanel** — Configure agent autonomy levels and models per role
2. **RetrospectiveView** — Display went well/wrong/action items
3. **Updated SprintPage** — Added Team and Retro tabs
4. **Updated FeedFilters** — Added architect and designer to filters
5. **Updated types** — AgentConfig, LearningResponse, RetroResponse

### Database Schema Additions

- `learnings` table for persistent learning storage
- `agent_configs` table for per-project agent configuration

---

## Backward Compatibility

All Phase 0 and Phase 1 tests continue to pass. Key changes:

- `TaskGraph.mark_completed()` now only tracks completion for dependency resolution (doesn't mutate task status)
- `SprintEngine` now includes retrospective node in the graph
- `_register_default_roles()` now registers Architect and Designer roles
- Existing tests updated to reflect new behavior (2 test assertions adjusted)
