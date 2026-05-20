@echo off
cd /d "%~dp0"
start "" python main.py
start "" python app\dev\debug_window.py
