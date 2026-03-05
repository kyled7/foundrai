# FoundrAI — Development Roadmap

## Phase 0 — Foundation
**Goal:** Core agent orchestration engine that can run a simple sprint from CLI.

### Milestones
- [ ] Project scaffolding (pyproject.toml, folder structure, CI setup)
- [ ] BaseAgent class with role definition and tool access
- [ ] AgentRuntime execution loop using LangGraph
- [ ] Basic roles: ProductManager, Developer, QAEngineer
- [ ] Sequential task execution with message passing via MessageBus
- [ ] Simple CLI: `foundrai init`, `foundrai sprint start`
- [ ] SQLite persistence for sprint state and event log
- [ ] LiteLLM integration for model-agnostic LLM calls
- [ ] Basic sandboxed code execution (Docker)

### Definition of Done
A user can run `foundrai sprint start "Build a hello world API"` and watch 3 agents (PM, Dev, QA) decompose the goal, write code, and test it — all from the terminal.

---

## Phase 1 — Visual Layer
**Goal:** Web dashboard showing live sprint activity.

### Milestones
- [ ] FastAPI server with REST endpoints for projects, sprints, tasks
- [ ] WebSocket server streaming agent activity in real-time
- [ ] React frontend scaffolding (Vite + TypeScript)
- [ ] Sprint Board component (Kanban view with live task updates)
- [ ] Agent Activity Feed (timeline with reasoning traces)
- [ ] Goal Decomposition View (tree visualization of goal → tasks)
- [ ] Basic human approval gates (approve/reject via UI)
- [ ] `foundrai serve` command to launch web dashboard

### Definition of Done
A user can run `foundrai serve` and watch agents work on a beautiful live dashboard with a Kanban board, agent feed, and approval buttons.

---

## Phase 2 — Agile Engine
**Goal:** Full Agile sprint lifecycle with iteration and learning.

### Milestones
- [ ] Sprint Planning ceremony (PM decomposes, team estimates)
- [ ] Parallel task execution where dependencies allow
- [ ] Sprint Review ceremony (agents present work, quality scoring)
- [ ] Sprint Retrospective (agents analyze and generate learnings)
- [ ] VectorMemory integration (ChromaDB) for persistent learnings
- [ ] Multi-sprint support (learnings carry across sprints)
- [ ] Per-agent autonomy configuration in UI
- [ ] Multi-model support (assign different LLMs per role)
- [ ] Architect and Designer agent roles

### Definition of Done
A user can run multiple sprints on the same project and observe the AI team improving its process and output quality over time.

---

## Phase 3 — Observability
**Goal:** Full monitoring and debugging capabilities.

### Milestones
- [ ] Agent performance analytics dashboard (completion rate, quality, cost)
- [ ] Token cost tracking per agent, per sprint, per task
- [ ] Token budget system (set limits per sprint/agent)
- [ ] Decision trace viewer (expand any decision to see full reasoning chain)
- [ ] Communication graph visualization (who talked to whom)
- [ ] Sprint comparison view (velocity, quality across sprints)
- [ ] Error diagnosis tools (when agents fail, show why)
- [ ] Event replay system (replay any sprint from event log)

### Definition of Done
A user can fully understand why agents made every decision, track costs precisely, and diagnose any failures — like having Datadog for their AI team.

---

## Phase 4 — Ecosystem
**Goal:** Extensibility, integrations, and community.

### Milestones
- [ ] Plugin architecture (custom roles, tools, integrations)
- [ ] Team template system (save and share team configurations)
- [ ] GitHub integration (agents create real repos, branches, PRs)
- [ ] Jira/Linear integration (sync tasks to external project management)
- [ ] Slack integration (notifications and approvals via Slack)
- [ ] Community marketplace for templates and plugins
- [ ] DevOps agent role with real CI/CD capabilities
- [ ] Multi-team coordination (multiple AI teams on one project)
- [ ] Documentation and contribution guide

### Definition of Done
FoundrAI has a thriving plugin ecosystem, integrates with real development tools, and has an active open source community.

---

---

## v0.2 — UI-First Platform
**Goal:** Move all control from CLI to Web UI — zero terminal required.

Full design document: [`docs/V0.2_UI_FIRST_DESIGN.md`](./V0.2_UI_FIRST_DESIGN.md)

### Phases
| Phase | Focus | Duration |
|-------|-------|----------|
| 0.2.0 | Frontend Foundation (scaffold, API client, layout) | 3–4 days |
| 0.2.1 | Dashboard + Project Creation Wizard | 4–5 days |
| 0.2.2 | Sprint Command Center ⭐ (core experience) | 7–10 days |
| 0.2.3 | Analytics + Sprint Replay | 4–5 days |
| 0.2.4 | Settings, Polish, Desktop (Tauri) evaluation | 4–5 days |

### Key Deliverables
- **Project Wizard** — create projects entirely from UI (replaces `foundrai init`)
- **Team Config UI** — visual agent configuration (replaces YAML editing)
- **Sprint Command Center** — start/pause/cancel sprints, realtime feed, inline approvals, mid-sprint chat
- **Analytics Dashboard** — cost tracking, sprint history, learnings
- **Settings UI** — API keys, models, sandbox, health checks (replaces `foundrai doctor`)

### New Backend APIs
- Sprint lifecycle: `start`, `pause`, `resume`, `cancel`, `message`
- Settings: CRUD + test API key
- System health check
- WebSocket: full event bus broadcast (replaces ping/pong)

### Definition of Done
A new user opens browser → creates project → configures team → starts sprint → approves/rejects → views results. **Never opens terminal.**

---

## Risk Mitigations (Applied Throughout)
- **Token costs:** Model tiering, token budgets, cost estimator before execution
- **Quality degradation:** Structured handoff protocols, periodic sync steps, rich shared context
- **Coordination complexity:** Start sequential, add parallelism gradually, finite state machines
- **Scope creep:** V1 = software teams only. One vertical done well before expanding.
