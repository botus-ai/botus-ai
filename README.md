# Hi, I'm Alexander (Sasha) 👋

**AI Developer · Novosibirsk, Russia · Building autonomous AI systems**

I design and build production-grade AI agent systems — from multi-bot Telegram workflows to autonomous task automation pipelines running on Claude, Notion, and local Mac hardware.

- 🤖 **Multi-agent systems** — OpenClaw-based bots with clear role separation (secretary + executor model)
- 🧠 **Autonomous pipelines** — Self-running workflows: Notion ↔ Calendar sync, task routing, sub-agent spawning
- 📬 **Telegram AI Bots** — Meeting processors, task managers, voice-to-task automation
- ⚙️ **Local-first stack** — Mac Mini M4 + local LLMs (Ollama) + cloud fallback (Claude Sonnet/Haiku)
- 🔧 **Open Source** — Contributing to OpenClaw ecosystem, publishing tools and agent configs

---

## 🏗️ Current System — Botus OS v3.0

My personal AI operating system running 24/7 on Mac Mini M4:

```
User (Telegram)
    │
    ▼
┌─────────────┐        ┌──────────────────────────────────┐
│  Assistant  │───────▶│  Notion (Tasks DB + Calendar DB)  │
│  (Secretary)│◀───────│  Source of truth for all tasks    │
└─────────────┘        └──────────────────────────────────┘
    │                               ▲
    ▼ sessions_send                 │ auto-sync every 15 min
┌─────────────┐        ┌──────────────────────────────────┐
│     CEO     │        │  notion_sync.py + macOS launchd   │
│  (Executor) │        │  → Apple Calendar (.ics)          │
│  sub-agents │        └──────────────────────────────────┘
└─────────────┘
    │
    ├── research_agent   (web search, analysis)
    ├── content_agent    (writing, copywriting)
    ├── code_agent       (scripts, automation)
    ├── analysis_agent   (data, decisions)
    ├── notion_agent     (Notion read/write)
    └── strategy_agent  (planning, roadmaps)
```

### Core Stack
| Layer | Tools |
|-------|-------|
| **AI** | Claude Sonnet 4.6 / Haiku 4.5 via OpenClaw, local Ollama models |
| **Task management** | Notion (Tasks DB + Calendar DB) |
| **Automation** | Python + macOS launchd (15-min sync cycle) |
| **Calendar** | Notion Calendar → Apple Calendar (.ics subscription) |
| **Version control** | GitHub (this repo) |
| **Runtime** | Mac Mini M4, 24/7 |

---

## 🤖 Agent Architecture (OpenClaw v3.0)

### Assistant — Personal Secretary
- Receives all incoming requests via Telegram
- Clarifies: what, deadline, priority (P1/P2/P3), context
- Creates entries in Notion Tasks DB + Calendar
- Notifies CEO via `sessions_send`
- Confirms completion back to Sasha
- **Does NOT execute tasks — intake only**

### CEO — Main Executor
- Reads task from Notion on notification
- Spawns specialized sub-agents via `sessions_spawn`
- Sends result directly to Sasha in Telegram
- Reports completion → Assistant marks Done in Notion

Full agent configs: [`openclaw/agents/`](./openclaw/agents/)

---

## 🚀 Projects

### [Meetus AI Bot](https://github.com/botus-ai/meetus-ai-bot)
SaaS Telegram bot for meeting processing. Transcribes audio/video (Whisper), extracts summaries and actionable tasks via LLM, subscription tiers with SQLite.

### [Agent Toolkit](https://github.com/botus-ai/agent-toolkit)
OpenClaw plugin toolkit — reusable skills and agent components.

### [Awesome OpenClaw Skills](https://github.com/botus-ai/awesome-openclaw-skills)
Curated collection of OpenClaw skills and use cases.

---

## 📁 This Repository

```
botus-ai/
├── README.md                         ← You are here
├── Scripts/
│   ├── notion_sync.py                ← Notion → Calendar auto-sync (15 min)
│   ├── install_sync.sh               ← One-command setup
│   └── com.botus.notion-sync.plist   ← macOS launchd config
├── openclaw/
│   ├── agents/
│   │   ├── assistant/SOUL.md         ← Secretary agent config
│   │   └── ceo/SOUL.md               ← Executor agent config
│   └── ARCHITECTURE.md               ← Full system architecture
└── docs/
    └── SETUP.md                      ← Setup guide
```

---

## ⚡ Quick Start — Notion Sync

```bash
# 1. Clone repo
git clone https://github.com/botus-ai/botus-ai.git
cd botus-ai

# 2. Set your Notion token in Scripts/notion_sync.py
# Create integration at: https://www.notion.so/my-integrations

# 3. Connect integration to your Notion databases
# (Tasks DB + Calendar DB → ••• → Connections → Add connection)

# 4. Install and start
bash Scripts/install_sync.sh
```

This registers a macOS launchd agent that syncs every 15 minutes and generates an `.ics` file for Apple Calendar subscription.

---

## 💻 Tech Stack

- **Python 3.9+** — macOS compatible, no venv required
- **Telegram Bot API** — python-telegram-bot
- **LLMs** — Claude Sonnet/Haiku (Anthropic), Ollama (local)
- **Databases** — Notion API, SQLite
- **Automation** — OpenClaw framework, macOS launchd
- **Calendar** — iCalendar (.ics), Apple Calendar
- **Hardware** — Mac Mini M4

---

## 📫 Contact

- **Email:** sasha0046657@gmail.com
- **Location:** Novosibirsk, Russia 🇷🇺
- **Open to:** Consulting, freelance, co-founding

*Building AI that actually works in production 🚀*
