@echo off
cd /d "%~dp0"
if not exist venv (
    echo El entorno no esta instalado todavia. Corre primero install.ps1
    pause
    exit /b 1
)
venv\Scripts\python.exe app\desktop.py
