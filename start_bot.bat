@echo off
title Moncho Discord Bot 🤖

cd /d "%~dp0"

call venv\Scripts\activate

echo 🔌 Iniciando bot...
python main.py

echo ❌ El bot se ha detenido
pause
