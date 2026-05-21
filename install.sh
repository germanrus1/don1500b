#!/bin/bash
set -e

echo "=== Бортовой компьютер Дон 1500б — установка на Raspberry Pi 5 ==="
echo ""

# ── Системные пакеты ───────────────────────────────────────────────────────
echo "[1/4] Устанавливаем системные пакеты..."
sudo apt-get update -q
sudo apt-get install -y \
    python3-pyqt6 \
    python3-pip \
    python3-venv \
    libxcb-cursor0 \
    libgl1

# ── Виртуальное окружение ──────────────────────────────────────────────────
echo "[2/4] Создаём виртуальное окружение..."
# --system-site-packages нужен чтобы venv видел системный python3-pyqt6
python3 -m venv --system-site-packages .venv

# ── Pip зависимости ────────────────────────────────────────────────────────
echo "[3/4] Устанавливаем pip зависимости..."
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements-rpi.txt --quiet

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
