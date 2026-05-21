#!/bin/bash
set -e

cd "$(dirname "$0")"

# Qt требует X11 (xcb) — работает надёжнее Wayland для kiosk-приложений
export QT_QPA_PLATFORM=xcb
export DISPLAY="${DISPLAY:-:0}"

# Подавить лишние предупреждения Qt
export QT_LOGGING_RULES="*.debug=false;qt.qpa.*=false"

if [ "$1" = "--debug" ]; then
    .venv/bin/python main.py &
    .venv/bin/python app/dev/debug_window.py
else
    exec .venv/bin/python main.py
fi
