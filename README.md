<div align="center">

# 🏢 FoundrAI

### Your AI-Powered Founding Team

**Autonomous AI agents working as an Agile startup team — with a live visual dashboard.**

[![PyPI version](https://img.shields.io/pypi/v/foundrai.svg)](https://pypi.org/project/foundrai/)
[![Python 3.11+](https://img.shields.io/pypi/pyversions/foundrai.svg)](https://pypi.org/project/foundrai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Getting Started](#getting-started) · [Documentation](./docs/) · [Roadmap](./docs/ROADMAP.md) · [Contributing](#contributing)

---

</div>

## What is FoundrAI?

FoundrAI is an open-source platform that orchestrates multiple AI agents as an autonomous Agile team. Give it a goal like *"Build a REST API for a todo app"*, and a team of specialized AI agents (Product Manager, Architect, Developer, QA) will self-organize into sprints to plan, build, test, and iterate — while you watch everything unfold on a real-time dashboard.

**Think of it as a virtual startup team you can observe, guide, and learn from.**

### Why FoundrAI?

| Feature | CrewAI | MetaGPT | ChatDev | AutoGen | **FoundrAI** |
|---------|--------|---------|---------|---------|-------------|
| Visual Dashboard | ❌ (Studio is commercial) | ❌ | Basic | Basic | ✅ **Real-time mission control** |
| Agile Sprints | ❌ | ❌ (single pass) | ❌ (waterfall) | ❌ | ✅ **Plan → Execute → Review → Retro** |
| Human-in-the-Loop | Basic | ❌ | ❌ | Basic | ✅ **Granular per-agent policies** |
| Iterative Learning | ❌ | ❌ | ❌ | ❌ | ✅ **Agents improve across sprints** |
| Model-Agnostic | Partial | Partial | ❌ | ✅ | ✅ **Different LLM per agent role** |
| Open Source UI | ❌ | ❌ | ❌ | Partial | ✅ **Fully open source** |

## Key Features

🎯 **Goal → Execution Pipeline** — Enter a high-level goal and watch agents decompose, plan, and execute it

📊 **Live Sprint Board** — Real-time Kanban showing what each agent is working on

💬 **Agent Communication Feed** — See every message, decision, and reasoning trace between agents

🎛️ **Configurable Autonomy** — Set per-agent approval policies (auto-approve code but review architecture decisions)

🔄 **Sprint Retrospectives** — Agents analyze and improve their process after each sprint

🔌 **Model-Agnostic** — Assign Claude for PM, GPT-4o for coding, a local model for QA

📈 **Performance Analytics** — Track token costs, agent performance, and sprint velocity

## Screenshots

### Dashboard
![Dashboard](./docs/screenshots/01-dashboard.jpg)
*Main dashboard with project stats, quick actions, and empty state onboarding*

### Project Creation Wizard
![Project Wizard](./docs/screenshots/02-wizard-step1.jpg)
*3-step project wizard — configure name, team, and settings with form validation*

### Template Browser
![Templates](./docs/screenshots/03-templates.jpg)
*Browse and search project templates with tag filtering*

### Settings — General
![Settings General](./docs/screenshots/04-settings-general.jpg)
*Configure default model, autonomy level, and budget limits with breadcrumb navigation*

### Settings — API Keys
![Settings API Keys](./docs/screenshots/05-settings-apikeys.jpg)
*Manage LLM provider API keys — add, test, and remove with masked display*

### Settings — Appearance
![Settings Appearance](./docs/screenshots/06-settings-appearance.jpg)
*Theme selector with Dark, Light, and System options*

### 404 Page
![404](./docs/screenshots/07-404.jpg)
*Clean error page with navigation back to dashboard*

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm (for the web dashboard)
- Docker (for sandboxed code execution)
- An API key for at least one LLM provider (OpenAI, Anthropic, etc.)

### Installation

```bash
# Clone the repo
git clone https://github.com/kyled7/foundrai.git
cd foundrai

# Install from PyPI
pip install foundrai

# Or install from source (for development)
pip install -e ".[dev]"

# Install frontend dependencies
cd frontend-v2
npm install
```

### Quick Start

```bash
# Configure your LLM provider(s)
export OPENAI_API_KEY="sk-..."
# and/or
export ANTHROPIC_API_KEY="sk-ant-..."

# Start the web dashboard (recommended)
cd frontend-v2
npm run dev
# → Open http://localhost:5173

# Or use the CLI directly
foundrai sprint start "Build a REST API for a todo app with authentication"
```

### Web Dashboard (v0.2)

The dashboard is the primary interface as of v0.2. From the UI you can:
- **Create projects** via the 3-step wizard (name → team → settings)
- **Browse templates** to quick-start common project types
- **Configure settings** — default model, autonomy level, budget, API keys, theme
- **Monitor sprints** — real-time agent feed, Kanban board, approvals (coming in v0.3)

## CLI Commands

FoundrAI also provides a CLI for headless usage:

```bash
foundrai doctor          # Check system health and prerequisites
foundrai sprint start    # Start a sprint from a goal description
foundrai status          # Project status and monitoring
foundrai logs            # View agent logs
foundrai serve           # Launch the web dashboard on port 8420
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              Frontend (React + TypeScript)            │
│  Sprint Board │ Agent Feed │ Goal Tree │ Metrics     │
├─────────────────────────────────────────────────────┤
│              API Layer (FastAPI + WebSocket)          │
├─────────────────────────────────────────────────────┤
│           Orchestration (LangGraph + SprintEngine)   │
├─────────────────────────────────────────────────────┤
│              Agent Layer (LiteLLM + Tools)            │
├─────────────────────────────────────────────────────┤
│           Persistence (SQLite + ChromaDB)             │
└─────────────────────────────────────────────────────┘
```

See [Architecture Documentation](./docs/ARCHITECTURE.md) for full details.

## Agent Roles

| Agent | Role | What They Do |
|-------|------|-------------|
| 📋 PM | Product Manager | Decomposes goals, writes stories, prioritizes backlog |
| 🏗️ Architect | System Architect | Designs architecture, reviews technical decisions |
| 💻 Dev | Developer | Writes code, submits for review, fixes bugs |
| 🧪 QA | QA Engineer | Tests code, reports bugs, validates fixes |
| 🎨 Designer | UI/UX Designer | Creates mockups, defines user flows |
| 🚀 DevOps | DevOps Engineer | CI/CD setup, deployment, monitoring |

## Configuration

```yaml
# foundrai.yaml
team:
  product_manager:
    model: anthropic/claude-sonnet-4-20250514
    autonomy: notify
  architect:
    model: anthropic/claude-sonnet-4-20250514
    autonomy: require_approval
  developer:
    model: openai/gpt-4o
    autonomy: auto_approve
    conditions:
      require_approval_if:
        lines_changed: ">50"
  qa_engineer:
    model: openai/gpt-4o-mini
    autonomy: auto_approve

sprint:
  max_tasks_parallel: 3
  token_budget: 100000
```

## Roadmap

- **v0.1** ✅ Core agent engine + CLI (Foundation, Visual Layer, Agile Engine, Observability, Ecosystem)
- **v0.2** ✅ UI-First Platform — Full web dashboard replacing CLI
  - v0.2.0 ✅ Frontend Foundation (React 19, TypeScript, Tailwind, TanStack Router/Query)
  - v0.2.1 ✅ Dashboard & Project Management (wizard, team config, templates)
  - v0.2.2 ✅ Sprint Command Center (realtime feed, WebSocket, approvals)
  - v0.2.3 ✅ Analytics & Insights (charts, cost tracking, sprint replay)
  - v0.2.4 ✅ Settings & Polish (settings page, error handling, accessibility)
- **v0.3** 🔨 Backend Integration — Connect frontend to live backend

See [full roadmap](./docs/ROADMAP.md) for details.

## Contributing

We'd love your help! FoundrAI is in early development and there are many ways to contribute:

- 🐛 Report bugs and suggest features via [Issues](../../issues)
- 🔧 Submit PRs (see our [Contributing Guide](./CONTRIBUTING.md))
- 📖 Improve documentation
- 🧪 Write tests
- 🎨 Design UI components
- 🔌 Build plugins and integrations

## License

MIT License — see [LICENSE](./LICENSE) for details.

---

<div align="center">

**Built with ❤️ by the FoundrAI community**

[⭐ Star us on GitHub](../../) · [📖 Read the Docs](./docs/) · [💬 Join the Discussion](../../discussions)

</div>
