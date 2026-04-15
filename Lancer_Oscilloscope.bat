@echo off
REM ====================================================================
REM   ADALM2000 Laboratory - Lanceur Rapide Windows
REM   Copyright (c) 2024-2026 Odin De Baerdemaker - Tous droits reserves
REM ====================================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"
chcp 65001 >nul

REM --- Chercher Python ---
set "PY="

REM Essayer python
where python >nul 2>&1
if not errorlevel 1 (
    python -c "import sys; sys.exit(0)" >nul 2>&1
    if not errorlevel 1 set "PY=python"
)

REM Essayer python3
if not defined PY (
    where python3 >nul 2>&1
    if not errorlevel 1 set "PY=python3"
)

REM Essayer py launcher
if not defined PY (
    where py >nul 2>&1
    if not errorlevel 1 set "PY=py"
)

REM Essayer des chemins courants
if not defined PY (
    for %%P in (
        "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
    ) do (
        if exist %%P (
            if not defined PY set "PY=%%~P"
        )
    )
)

if not defined PY (
    echo.
    echo  ERREUR : Python n'est pas installe !
    echo  Lancez d'abord "Installer_ADALM2000.bat"
    echo.
    pause
    exit /b 1
)

REM --- Lancer l'application ---
start "" !PY! src/main_oscilloscope.py
