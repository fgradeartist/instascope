@echo off
title InstaScope v2.0 — Launcher
color 0A
chcp 65001 >nul 2>&1

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║     📸  InstaScope v2.0 — Instagram Analyzer        ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

:: ── Check Python ─────────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [!] Python not found.
    echo.
    echo  Please install Python 3.10+ from:
    echo       https://www.python.org/downloads/
    echo.
    echo  IMPORTANT: Check "Add Python to PATH" during install.
    echo.
    pause
    start https://www.python.org/downloads/
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  [OK] Python %PYVER%

:: ── Check tkinter ─────────────────────────────────────────────────────────────
python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo  [!] tkinter missing — reinstall Python and select "tcl/tk and IDLE"
    pause
    exit /b 1
)
echo  [OK] tkinter

:: ── Install matplotlib ────────────────────────────────────────────────────────
python -c "import matplotlib" >nul 2>&1
if errorlevel 1 (
    echo  [..] Installing matplotlib ^(charts^)...
    python -m pip install --quiet --upgrade matplotlib
    if errorlevel 1 ( echo  [!]  matplotlib failed — charts will be disabled
    ) else ( echo  [OK] matplotlib installed )
) else ( echo  [OK] matplotlib )

:: ── Install tkinterdnd2 (drag and drop support) ───────────────────────────────
python -c "import tkinterdnd2" >nul 2>&1
if errorlevel 1 (
    echo  [..] Installing tkinterdnd2 ^(drag and drop^)...
    python -m pip install --quiet --upgrade tkinterdnd2
    if errorlevel 1 ( echo  [!]  tkinterdnd2 failed — drag and drop will be disabled
    ) else ( echo  [OK] tkinterdnd2 installed )
) else ( echo  [OK] tkinterdnd2 ^(drag and drop^) )

:: ── Check instascope.py ───────────────────────────────────────────────────────
if not exist "%~dp0instascope.py" (
    echo.
    echo  [!] instascope.py not found in:
    echo      %~dp0
    echo  Make sure this .bat is in the same folder as instascope.py
    pause
    exit /b 1
)

echo.
echo  [OK] All checks passed. Launching InstaScope...
echo.
timeout /t 1 /nobreak >nul

cd /d "%~dp0"
start "" pythonw instascope.py

exit /b 0
