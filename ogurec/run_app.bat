@echo off
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel%==0 (
    python program.py
) else (
    py -3 program.py
)
if %errorlevel% neq 0 pause
