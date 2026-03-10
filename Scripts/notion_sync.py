#!/usr/bin/env python3
"""
Notion Auto-Sync v2.0
========================================================
Что делает:
  1. Tasks DB → Calendar DB (Notion)  — задачи с дедлайнами становятся событиями
  2. Calendar DB → .ics файл          — Apple Calendar подписывается на него
  3. Рутинные события                 — фиксированное расписание Саши
  4. Дедлайны из Tasks                — P1/P2 задачи с датами → в календарь

Запуск: python3 ~/Scripts/notion_sync.py
Автозапуск: launchd (каждые 15 минут)
Зависимости: pip3 install requests icalendar pytz --user

НЕ зависит от OpenClaw. Работает сам.
"""

import requests
import json
import os
import re
import sys
import uuid
import hashlib
from datetime import datetime, timedelta, date
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    from icalendar import Calendar, Event, vText
except ImportError:
    print("⚠️  icalendar не установлен. Устанавливаю...")
    os.system(f"{sys.executable} -m pip install --user icalendar pytz -q")
    from icalendar import Calendar, Event, vText

# ═══════════════════════════════════════════════════
# КОНФИГ
# ═══════════════════════════════════════════════════

NOTION_TOKEN     = "YOUR_NOTION_TOKEN_HERE"
TASKS_DB_ID      = "1d957f271fdf47008fdc1eb87f3bfa55"
CALENDAR_DB_ID   = "1e0a20031084464caebae05cc1181bee"  # 📅 Календарь (основной)
ICS_OUTPUT_PATH  = Path("/Users/botus_bbot/Scripts/notion_calendar.ics")
TZ               = ZoneInfo("Asia/Novosibirsk")  # UTC+7

NOTION_API     = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}

# ═══════════════════════════════════════════════════
# ФИКСИРОВАННОЕ РАСПИСАНИЕ (рутина)
# ═══════════════════════════════════════════════════

RECURRING_EVENTS = [
    # (weekday 0=Mon, title, start_h, start_m, duration_min, type)
    (1, "🏓 Падл с Женей",         10, 0, 90,  "Встреча"),   # Вт
    (3, "🏓 Падл с Женей",         10, 0, 90,  "Встреча"),   # Чт
    (3, "🧖 Сандуны (Женя+Папа)",  18, 0, 120, "Встреча"),   # Чт
    (6, "⛪ Храм с дядей",          9, 0, 180, "Событие"),   # Вс
]

# ═══════════════════════════════════════════════════
# 1. NOTION: ПОЛУЧИТЬ ЗАДАЧИ С ДЕДЛАЙНАМИ
# ═══════════════════════════════════════════════════

def fetch_tasks() -> list[dict]:
    """Загружает задачи с датами (статус НЕ Done) из Tasks DB."""
    print("📋 Загружаю задачи из Notion Tasks DB...")
    url = f"{NOTION_API}/databases/{TASKS_DB_ID}/query"
    payload = {
        "filter": {
            "and": [
                {"property": "Due",    "date":   {"is_not_empty": True}},
                {"property": "Status", "status": {"does_not_equal": "Done"}},
            ]
        },
        "sorts": [{"property": "Due", "direction": "ascending"}],
        "page_size": 100,
    }
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=15)
    resp.raise_for_status()

    tasks = []
    for item in resp.json().get("results", []):
        props = item["properties"]

        title_list = props.get("Title", {}).get("title", [])
        title = title_list[0]["plain_text"] if title_list else "Untitled"

        due = (props.get("Due", {}).get("date") or {}).get("start")
        if not due:
            continue

        priority_sel = (props.get("Priority", {}).get("select") or {}).get("name", "P3")
        area_sel     = (props.get("Area",     {}).get("select") or {}).get("name", "Работа")
        energy_sel   = (props.get("Energy",   {}).get("select") or {}).get("name", "Medium")
        time_min     = (props.get("Time (min)", {}).get("number")) or None

        tasks.append({
            "id":          item["id"],
            "title":       title,
            "due":         due,          # "2026-03-11" or "2026-03-11T09:00:00+07:00"
            "priority":    priority_sel,
            "area":        area_sel,
            "energy":      energy_sel,
            "duration":    time_min,
        })

    print(f"   → {len(tasks)} задач с датами")
    return tasks


# ═══════════════════════════════════════════════════
# 2. NOTION: ПОЛУЧИТЬ / СОЗДАТЬ / ОБНОВИТЬ СОБЫТИЯ
# ═══════════════════════════════════════════════════

def fetch_calendar_events() -> dict[str, str]:
    """Возвращает {title: page_id} для событий в Calendar DB."""
    url = f"{NOTION_API}/databases/{CALENDAR_DB_ID}/query"
    resp = requests.post(url, headers=HEADERS, json={"page_size": 200}, timeout=15)
    resp.raise_for_status()

    events = {}
    for item in resp.json().get("results", []):
        props = item["properties"]
        title_list = props.get("Event", {}).get("title", [])
        t = title_list[0]["plain_text"] if title_list else ""
        if t:
            events[t] = item["id"]
    return events


def _build_event_times(task: dict) -> tuple[str, str]:
    """Возвращает (start_iso, end_iso) с временем по таймзоне UTC+7."""
    raw = task["due"]
    duration = task["duration"] or _default_duration(task["energy"])

    # Если дата уже содержит время — используем её
    if "T" in raw:
        start_dt = datetime.fromisoformat(raw)
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=TZ)
    else:
        # Только дата → назначаем время по приоритету/energy
        h, m = _default_time(task["priority"], task["energy"])
        start_dt = datetime(
            *map(int, raw.split("-")), h, m, tzinfo=TZ
        )

    end_dt = start_dt + timedelta(minutes=duration)
    return start_dt.isoformat(), end_dt.isoformat()


def _default_time(priority: str, energy: str) -> tuple[int, int]:
    if priority == "P1":
        return 9, 30    # Deep work утром
    if energy == "High":
        return 9, 30
    if energy == "Medium":
        return 13, 30
    return 16, 0        # Low energy → вечер


def _default_duration(energy: str) -> int:
    return {"High": 120, "Medium": 90, "Low": 60}.get(energy, 90)


def _priority_to_type(priority: str) -> str:
    return {"P1": "Дедлайн", "P2": "Важное", "P3": "Работа"}.get(priority, "Работа")


def upsert_calendar_event(task: dict, existing: dict[str, str]):
    """Создать новое или обновить существующее событие в Calendar DB."""
    start_iso, end_iso = _build_event_times(task)
    event_type = _priority_to_type(task["priority"])

    props = {
        "Event": {"title": [{"type": "text", "text": {"content": task["title"]}}]},
        "Start": {"date": {"start": start_iso}},
        "End":   {"date": {"start": end_iso}},
        "Type":  {"select": {"name": event_type}},
    }

    title = task["title"]
    if title in existing:
        # Обновить
        url = f"{NOTION_API}/pages/{existing[title]}"
        resp = requests.patch(url, headers=HEADERS, json={"properties": props}, timeout=15)
    else:
        # Создать
        url = f"{NOTION_API}/pages"
        resp = requests.post(url, headers=HEADERS,
                             json={"parent": {"database_id": CALENDAR_DB_ID}, "properties": props},
                             timeout=15)

    if resp.status_code in (200, 201):
        action = "↻ обновлено" if title in existing else "✅ создано"
        print(f"   {action}: {title} | {start_iso[:16]}")
        return True
    else:
        print(f"   ❌ ошибка для '{title}': {resp.status_code} {resp.text[:120]}")
        return False


# ═══════════════════════════════════════════════════
# 3. ГЕНЕРАТОР .ics (Apple Calendar подписка)
# ═══════════════════════════════════════════════════

def _make_uid(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest() + "@botus-notion"


def generate_ics(tasks: list[dict]) -> None:
    """Генерирует .ics файл из задач + рутинных событий на 4 недели вперёд."""
    cal = Calendar()
    cal.add("prodid", "-//Botus Notion Sync//notion_sync.py//RU")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("x-wr-calname", "Notion — Саша")
    cal.add("x-wr-timezone", "Asia/Novosibirsk")
    cal.add("refresh-interval;value=duration", "PT15M")

    now = datetime.now(tz=TZ)
    added = 0

    # Задачи из Notion
    for task in tasks:
        try:
            start_iso, end_iso = _build_event_times(task)
            start_dt = datetime.fromisoformat(start_iso)
            end_dt   = datetime.fromisoformat(end_iso)

            ev = Event()
            ev.add("summary", task["title"])
            ev.add("dtstart", start_dt)
            ev.add("dtend",   end_dt)
            ev.add("uid",     _make_uid(task["id"] + task["due"]))
            ev.add("status",  "CONFIRMED")
            ev.add("description",
                   f"Priority: {task['priority']}\nArea: {task['area']}\nNotion ID: {task['id']}")
            cal.add_component(ev)
            added += 1
        except Exception as e:
            print(f"   ⚠️  ics skip '{task['title']}': {e}")

    # Рутинные события (4 недели вперёд)
    for offset in range(28):
        day = (now + timedelta(days=offset)).date()
        weekday = day.weekday()
        for wd, title, h, m, dur, etype in RECURRING_EVENTS:
            if weekday == wd:
                start_dt = datetime(day.year, day.month, day.day, h, m, tzinfo=TZ)
                end_dt   = start_dt + timedelta(minutes=dur)
                ev = Event()
                ev.add("summary", title)
                ev.add("dtstart", start_dt)
                ev.add("dtend",   end_dt)
                ev.add("uid",     _make_uid(f"{title}-{day}"))
                ev.add("categories", [etype])
                cal.add_component(ev)
                added += 1

    ICS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ICS_OUTPUT_PATH.write_bytes(cal.to_ical())
    print(f"\n📅 .ics сохранён: {ICS_OUTPUT_PATH}  ({added} событий)")


# ═══════════════════════════════════════════════════
# 4. MAIN
# ═══════════════════════════════════════════════════

def main():
    print("\n" + "═"*60)
    print("🔄  Notion Auto-Sync v2.0  —  " + datetime.now(tz=TZ).strftime("%d.%m.%Y %H:%M"))
    print("═"*60)

    try:
        tasks = fetch_tasks()
    except Exception as e:
        print(f"❌  Ошибка при загрузке задач: {e}")
        sys.exit(1)

    # 1. Синхронизировать Tasks → Calendar DB в Notion
    print("\n→ Синхронизирую в Notion Calendar DB...")
    try:
        existing = fetch_calendar_events()
        ok = 0
        for task in tasks:
            if upsert_calendar_event(task, existing):
                ok += 1
        print(f"   Итого: {ok}/{len(tasks)} событий обновлено/создано")
    except Exception as e:
        print(f"   ⚠️  Ошибка Notion Calendar: {e}")

    # 2. Генерировать .ics для Apple Calendar
    print("\n→ Генерирую .ics файл...")
    try:
        generate_ics(tasks)
    except Exception as e:
        print(f"   ⚠️  Ошибка .ics: {e}")

    print("\n✅  Синхронизация завершена\n")


if __name__ == "__main__":
    main()
