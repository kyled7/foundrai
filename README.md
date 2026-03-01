<div align="center">

# 🏢 FoundrAI

### Your AI-Powered Founding Team

**Autonomous AI agents working as an Agile startup team — with a live visual dashboard.**

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

## Getting Started

### Prerequisites
- Python 3.11+
- Docker (for sandboxed code execution)
- An API key for at least one LLM provider (OpenAI, Anthropic, etc.)

### Installation

```bash
pip install foundrai
```

### Quick Start

```bash
# Initialize a new project
foundrai init my-project
cd my-project

# Configure your LLM provider(s)
export OPENAI_API_KEY="sk-..."
# and/or
export ANTHROPIC_API_KEY="sk-ant-..."

# Start a sprint from CLI
foundrai sprint start "Build a REST API for a todo app with authentication"

# Or launch the web dashboard
foundrai serve
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

- **Phase 0** ✅ Core agent engine + CLI
- **Phase 1** 🔨 Visual dashboard (Sprint Board, Agent Feed)
- **Phase 2** 📋 Full Agile engine (sprints, retros, learning)
- **Phase 3** 📊 Observability (metrics, cost tracking, debugging)
- **Phase 4** 🔌 Ecosystem (plugins, integrations, marketplace)

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
