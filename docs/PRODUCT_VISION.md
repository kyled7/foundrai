# FoundrAI — Product Vision

## Vision Statement
FoundrAI is the mission control center for autonomous AI teams. Define a goal, watch AI agents self-organize into Agile sprints, and ship real results — with full visibility and human control.

## Target Users
- **Primary:** Developers and technical founders who want to automate software development workflows
- **Secondary:** Non-technical founders who want AI to build their MVP
- **Future:** Any team that wants AI agents working on marketing, research, content, or operations

## Core Value Proposition
"You give it a goal. It gives you a team. You watch them build."

Unlike code-first agent libraries (CrewAI, AutoGen) or one-shot script runners (MetaGPT, ChatDev), FoundrAI provides:
1. A **visual, interactive dashboard** to watch and control your AI team
2. **Real Agile methodology** with iterative sprints that improve over time
3. **Configurable autonomy** — you decide how much control to keep

## Feature Tiers

### 🔥 MVP (Phase 1-2)
- **Live Sprint Board** — Kanban with real-time task status as agents work
- **Agent Communication Timeline** — Scrollable, filterable message feed with reasoning traces
- **Goal Decomposition Visualizer** — Watch PM agent break goals into epics → stories → tasks
- **Configurable Autonomy Levels** — Per-agent and per-action approval policies
- **Multi-model Support** — Assign different LLMs per agent role via LiteLLM
- **CLI Interface** — Full headless operation via `foundrai` command

### ⭐ Version 2
- **Sprint Retrospectives & Learning** — Agents analyze and improve across sprints
- **Agent Performance Analytics** — Per-agent metrics: completion rate, cost, quality
- **Custom Team Templates** — Prebuilt and shareable team configurations
- **Multi-Model Roster** — A/B test model performance per role

### 🚀 Version 3+
- **Agent Marketplace & Plugin System** — Community-built roles, tools, templates
- **Multi-Team Coordination** — Multiple AI teams collaborating on the same project
- **Real Environment Integration** — Agents commit to GitHub, deploy to Vercel, post to social media
- **Team Types Beyond Software** — Marketing, research, content, operations teams

## Agent Roles (Default Software Team)

### 📋 Product Manager
- Breaks down high-level goals into epics, stories, and tasks
- Prioritizes the backlog based on user value and dependencies
- Writes acceptance criteria for each story
- Communicates decisions to the team

### 🏗️ Architect
- Designs system architecture and component structure
- Chooses appropriate technologies and patterns
- Reviews technical decisions made by other agents
- Ensures consistency and quality of technical approach

### 💻 Developer(s)
- Implements code from user stories and task specifications
- Submits work for code review
- Fixes bugs reported by QA
- Follows architecture decisions from the Architect

### 🧪 QA Engineer
- Creates test cases from acceptance criteria
- Reviews code output for bugs and quality issues
- Reports bugs back to Developer with reproduction steps
- Validates fixes and signs off on completed work

### 🎨 Designer
- Creates UI/UX mockups and wireframes
- Defines user flows and interaction patterns
- Reviews visual output against design specs

### 🚀 DevOps
- Sets up CI/CD pipeline configuration
- Manages deployment specifications
- Monitors performance and reliability concerns

## Positioning

### vs CrewAI
"CrewAI is a code library. FoundrAI is a product. You watch your team work on a live dashboard — you don't write Python scripts."

### vs MetaGPT
"MetaGPT runs once and gives you output. FoundrAI runs in sprints, learns, and improves. And you can intervene at any point."

### vs ChatDev
"ChatDev is a research demo. FoundrAI is a production tool with real Agile methodology and human-in-the-loop control."

### vs AutoGen
"AutoGen is a conversation framework. FoundrAI is an Agile team simulator with visual orchestration and sprint management."
