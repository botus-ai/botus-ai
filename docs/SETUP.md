# Setup Guide — Botus OS v3.0

This guide covers setting up the Notion ↔ Calendar sync pipeline on macOS.

---

## Prerequisites

- macOS with Python 3.9+
- Notion account with a Tasks DB and Calendar DB
- Notion integration token (Internal Integration)

---

## Step 1 — Create Notion Integration

1. Go to https://www.notion.so/my-integrations
2. Click **+ New integration**
3. Name it (e.g. "AutoSync"), select your workspace
4. Copy the **Internal Integration Token** (`ntn_...`)

---

## Step 2 — Connect Integration to Databases

For each database (Tasks DB + Calendar DB):
1. Open the database in Notion
2. Click **•••** (top right) → **Connections** → **Add connections**
3. Find and select your integration

This is required — Notion doesn't grant access automatically.

---

## Step 3 — Configure the Script

Edit `Scripts/notion_sync.py` and set your values:

```python
NOTION_TOKEN     = "ntn_your_token_here"
TASKS_DB_ID      = "your_tasks_db_id"
CALENDAR_DB_ID   = "your_calendar_db_id"
ICS_OUTPUT_PATH  = Path("/Users/yourname/Scripts/notion_calendar.ics")
TZ               = ZoneInfo("Asia/Novosibirsk")  # your timezone
```

To find a database ID: open the database in Notion → copy the URL → the 32-char hex string is the ID.

---

## Step 4 — Install

```bash
bash Scripts/install_sync.sh
```

This will:
- Install Python dependencies (`requests`, `icalendar`, `pytz`) via `pip3 --user`
- Verify Notion API access
- Run a test sync
- Register the launchd agent (auto-runs every 15 min)
- Open the `.ics` file in Apple Calendar for subscription

---

## Step 5 — Apple Calendar Subscription

When the `.ics` file opens:
1. Apple Calendar will ask to add or subscribe
2. Choose **Subscribe** for auto-refresh
3. Or **Add All** to import once

The `.ics` path is `~/Scripts/notion_calendar.ics` — refreshed every 15 min by launchd.

---

## Verify It's Working

```bash
# Check launchd status
launchctl list | grep botus

# Run sync manually
python3 ~/Scripts/notion_sync.py

# View logs
tail -f ~/Scripts/logs/notion_sync.log
```

---

## Troubleshooting

**404 from Notion API**
→ Integration not connected to the database. See Step 2.

**`icalendar` module not found**
→ Run: `pip3 install --user icalendar pytz requests`

**launchd not running**
→ Reload: `launchctl unload ~/Library/LaunchAgents/com.botus.notion-sync.plist && launchctl load ~/Library/LaunchAgents/com.botus.notion-sync.plist`

**Calendar not updating**
→ In Apple Calendar: right-click the calendar → Refresh

---

## Recurring Events (Hardcoded)

The sync script also adds these personal recurring events to the `.ics`:

| Event | Schedule |
|-------|---------|
| Padel | Every Tuesday + Thursday |
| Sauna (Sanduny) | Every Thursday |
| Church | Every Sunday |

To modify, edit the `RECURRING_EVENTS` list in `notion_sync.py`.
