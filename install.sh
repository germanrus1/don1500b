#!/bin/bash
set -e

echo "=== Бортовой компьютер Дон 1500б — установка на Raspberry Pi 5 ==="
echo ""

# ── Системные пакеты ───────────────────────────────────────────────────────
# PyQt6 и Qt ставятся из pip (см. requirements-rpi.txt): только pip-версия
# содержит модули QtQml/QtQuick для QML-интерфейса.
# Здесь — только системные библиотеки для платформы xcb (libGL, libxcb-*, ...).
echo "[1/4] Устанавливаем системные пакеты..."
sudo apt-get update -q
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    libxkbcommon-x11-0 \
    libgl1 \
    libegl1 \
    libdbus-1-3 \
    libfontconfig1

# ── Виртуальное окружение ──────────────────────────────────────────────────
echo "[2/4] Создаём виртуальное окружение..."
# Чистый venv без --system-site-packages: все зависимости (включая PyQt6)
# берём из pip, чтобы гарантированно была версия с QtQml/QtQuick.
# Если остался старый venv с --system-site-packages (от прежнего install.sh),
# он «протекает» системным PyQt6 без модулей QtQuick — пересоздаём чистым.
if [ -f .venv/pyvenv.cfg ] && grep -q "^include-system-site-packages = true" .venv/pyvenv.cfg; then
    echo "    устаревший venv (--system-site-packages) — пересоздаём"
    rm -rf .venv
fi
python3 -m venv .venv

# ── Pip зависимости ────────────────────────────────────────────────────────
echo "[3/4] Устанавливаем pip зависимости..."
.venv/bin/pip install --upgrade pip --quiet
# --only-binary=PyQt6,PyQt6-Qt6 — только wheel (есть для aarch64, manylinux_2_28),
# чтобы pip не пытался собирать Qt из исходников на старом glibc.
.venv/bin/pip install --only-binary=PyQt6,PyQt6-Qt6 -r requirements-rpi.txt --quiet

# ── Права GPIO ────────────────────────────────────────────────────────────
echo "[4/4] Настраиваем права доступа к GPIO..."
sudo usermod -aG gpio "$USER" 2>/dev/null || true

chmod +x run.sh

echo ""
echo "=== Установка завершена ==="
echo ""
echo "ВАЖНО: выйдите из системы и войдите снова (logout/login)"
echo "       чтобы права GPIO вступили в силу."
echo ""
echo "Запуск программы:  ./run.sh"
echo "Запуск с отладкой: ./run.sh --debug"
