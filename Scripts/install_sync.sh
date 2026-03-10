#!/bin/bash
# ════════════════════════════════════════════════════
# Botus Notion Auto-Sync — установка
# Запуск: bash ~/Scripts/install_sync.sh
# ════════════════════════════════════════════════════

set -e
echo ""
echo "════════════════════════════════════════════════════"
echo "  Botus Notion Sync — установка"
echo "════════════════════════════════════════════════════"

# 1. Папка для логов
mkdir -p ~/Scripts/logs
echo "✅ Папка логов: ~/Scripts/logs"

# 2. Python зависимости
echo ""
echo "→ Устанавливаю Python зависимости..."
pip3 install --user -q requests icalendar pytz 2>&1 | tail -3
echo "✅ Зависимости установлены"

# 3. Проверка токена Notion
echo ""
echo "→ Проверяю доступ к Notion..."
NOTION_TOKEN="YOUR_NOTION_TOKEN_HERE"
TASKS_DB="1d957f271fdf47008fdc1eb87f3bfa55"

CHECK=$(python3 -c "
import requests, sys
token = '$NOTION_TOKEN'
headers = {'Authorization': f'Bearer {token}', 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json'}
r = requests.post(f'https://api.notion.com/v1/databases/$TASKS_DB/query', headers=headers, json={'page_size': 1})
sys.exit(0 if r.status_code == 200 else 1)
" 2>/dev/null && echo "ok" || echo "fail")

if [ "$CHECK" = "fail" ]; then
    echo ""
    echo "════════════════════════════════════════════════════"
    echo "  ⚠️  ТРЕБУЕТСЯ ОДНОРАЗОВАЯ НАСТРОЙКА В NOTION"
    echo "════════════════════════════════════════════════════"
    echo ""
    echo "  Интеграция не подключена к базам данных Notion."
    echo "  Сделай ЭТО ОДИН РАЗ (занимает 2 минуты):"
    echo ""
    echo "  1. Открой Notion → база данных «✅ Задачи»"
    echo "     Ссылка: https://notion.so/1d957f271fdf47008fdc1eb87f3bfa55"
    echo ""
    echo "  2. Нажми ••• (три точки) → «Connections» → «Add connections»"
    echo "     Найди интеграцию «Assistant» → подключи"
    echo ""
    echo "  3. То же самое для «📅 Календарь»:"
    echo "     Ссылка: https://notion.so/1e0a20031084464caebae05cc1181bee"
    echo ""
    echo "  4. После подключения запусти установку снова:"
    echo "     bash ~/Scripts/install_sync.sh"
    echo ""
    echo "════════════════════════════════════════════════════"
    exit 1
fi

echo "✅ Notion доступен — токен работает"

# 4. Тестовый запуск
echo ""
echo "→ Тестовый запуск синхронизации..."
python3 ~/Scripts/notion_sync.py
if [ $? -eq 0 ]; then
    echo "✅ Скрипт работает"
else
    echo "❌ Ошибка при запуске. Смотри вывод выше."
    exit 1
fi

# 5. Установка launchd
echo ""
echo "→ Устанавливаю launchd агент (автозапуск каждые 15 мин)..."
PLIST_SRC="$HOME/Scripts/com.botus.notion-sync.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.botus.notion-sync.plist"

# Выгрузить если уже был
launchctl unload "$PLIST_DST" 2>/dev/null || true

# Скопировать plist
cp "$PLIST_SRC" "$PLIST_DST"

# Загрузить
launchctl load "$PLIST_DST"
echo "✅ launchd агент установлен"

# 6. Apple Calendar: открыть .ics
ICS_PATH="$HOME/Scripts/notion_calendar.ics"
echo ""
echo "→ Открываю .ics файл в Apple Calendar..."
if [ -f "$ICS_PATH" ]; then
    open "$ICS_PATH"
    echo "✅ Apple Calendar открылся — нажми 'Добавить все' или 'Подписаться'"
else
    echo "⚠️  .ics файл не найден — запусти скрипт ещё раз"
fi

echo ""
echo "════════════════════════════════════════════════════"
echo "  ✅ УСТАНОВКА ЗАВЕРШЕНА"
echo ""
echo "  Синхронизация работает каждые 15 минут."
echo "  Логи: ~/Scripts/logs/notion_sync.log"
echo ""
echo "  Чтобы проверить статус:"
echo "  launchctl list | grep botus"
echo ""
echo "  Чтобы запустить вручную:"
echo "  python3 ~/Scripts/notion_sync.py"
echo "════════════════════════════════════════════════════"
echo ""
