# OpenClaw Architecture v3.0

**Last updated:** March 2026
**System:** Botus OS — personal AI operating system on Mac Mini M4

---

## Overview

The system is built around a **secretary + executor** model with strict role separation:

- **Assistant** = pure intake. Receives, clarifies, logs, notifies. Never executes.
- **CEO** = pure execution. Reads from Notion, spawns sub-agents, delivers results.
- **Notion** = single source of truth for all tasks and events.

---

## Task Lifecycle (8 Steps)

```
1. Sasha sends message to Assistant in Telegram
2. Assistant clarifies: what / deadline / priority / context
3. Assistant creates task in Notion Tasks DB
4. Assistant adds event to Notion Calendar (if date given)
5. Assistant sends CEO notification via sessions_send
6. CEO reads task from Notion, spawns appropriate sub-agent
7. CEO sends result to Sasha in Telegram
8. CEO notifies Assistant → Assistant marks task Done in Notion
```

---

## Agent Configs

### Assistant (Secretary)
- **Model:** claude-haiku-4-5 (fast responses)
- **Trigger:** any Telegram message to @BotusBot
- **Config:** `agents/assistant/SOUL.md`
- **Tools:** sessions_send, Notion API write

### CEO (Executor)
- **Model:** claude-sonnet-4-6 (complex reasoning)
- **Trigger:** sessions_send from Assistant
- **Config:** `agents/ceo/SOUL.md`
- **Tools:** sessions_spawn, Notion API read/write, web search, code execution

### Sub-agents (spawned by CEO)
| Agent | Purpose |
|-------|---------|
| `research_agent` | Web search, fact-finding, competitive analysis |
| `content_agent` | Writing, copywriting, editing |
| `code_agent` | Python scripts, automation, debugging |
| `analysis_agent` | Data analysis, decision support |
| `notion_agent` | Complex Notion read/write operations |
| `strategy_agent` | Planning, roadmaps, strategic thinking |

---

## Notion Structure

### Databases
- **Tasks DB** (`1d957f271fdf47008fdc1eb87f3bfa55`) — all tasks with priority, due date, status
- **Calendar DB** (`1e0a20031084464caebae05cc1181bee`) — events synced from Tasks + recurring events

### Task Properties
| Property | Type | Values |
|----------|------|--------|
| Name | Title | Task description |
| Status | Select | Not started / In progress / Done |
| Priority | Select | P1 / P2 / P3 |
| Due | Date | Deadline |
| Area | Select | Work / Personal / Health / etc |
| Project | Relation | Link to Projects DB |

---

## Automation Stack

### Notion ↔ Calendar Sync
- **Script:** `Scripts/notion_sync.py`
- **Schedule:** Every 15 minutes via macOS launchd
- **Logic:** Queries Tasks DB (not Done, has Due date) → upserts to Calendar DB → generates `.ics` for Apple Calendar
- **Recurring events:** Padel (Tue/Thu), Sauna (Thu), Church (Sun)

### launchd Config
- **File:** `Scripts/com.botus.notion-sync.plist`
- **Install:** `launchctl load ~/Library/LaunchAgents/com.botus.notion-sync.plist`
- **Log:** `~/Scripts/logs/notion_sync.log`

---

## Hardware

- **Mac Mini M4** — always-on runtime
- **Local models:** Ollama (llama3, mistral, etc) for offline/fast tasks
- **Cloud fallback:** Anthropic Claude (haiku → sonnet depending on complexity)

---

## Integration Points (Future)

- [ ] GitHub Actions — push to repo triggers Notion task creation
- [ ] GitHub → Notion webhook for issue/PR tracking
- [ ] Apple Reminders sync
- [ ] Mac notifications for P1 tasks
