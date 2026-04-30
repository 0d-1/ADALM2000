@echo off
REM ====================================================================
REM   ADALM2000 Laboratory - Constructeur d'Executable Autonome (x86-64)
REM   Copyright (c) 2024-2026 Odin De Baerdemaker - Tous droits reserves
REM
REM   Ce script construit la version x86-64 (PC Intel/AMD classique).
REM   Pour construire automatiquement la version adaptee a votre
REM   processeur (x86-64 ou ARM64), utilisez :
REM     Construire_Executable_MultiArch.bat
REM ====================================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo.
echo  ========================================================
echo    ADALM2000 - Construction de l'Executable Autonome
echo  ========================================================
echo.

REM --- 1. Chercher Python ---
set "PY="
where python >nul 2>&1
if not errorlevel 1 (
    python -c "import sys; sys.exit(0)" >nul 2>&1
    if not errorlevel 1 set "PY=python"
)
if not defined PY (
    where python3 >nul 2>&1
    if not errorlevel 1 set "PY=python3"
)
if not defined PY (
    where py >nul 2>&1
    if not errorlevel 1 set "PY=py"
)

if not defined PY (
    echo  [ERREUR] Python n'est pas installe !
    echo  Installez Python 3.9+ depuis https://python.org
    pause
    exit /b 1
)

echo  [OK] Python trouve : !PY!
!PY! --version
echo.

REM --- 2. Installer PyInstaller si necessaire ---
echo  [1/3] Verification de PyInstaller...
!PY! -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo        Installation de PyInstaller...
    !PY! -m pip install pyinstaller --quiet
    if errorlevel 1 (
        echo  [ERREUR] Impossible d'installer PyInstaller.
        pause
        exit /b 1
    )
)
echo        PyInstaller est pret.
echo.

REM --- 3. Verifier que les dependances du projet sont installees ---
echo  [2/3] Verification des dependances du projet...
!PY! -c "import PyQt6; import pyqtgraph; import numpy" >nul 2>&1
if errorlevel 1 (
    echo        Installation des dependances manquantes...
    !PY! -m pip install PyQt6 pyqtgraph numpy --quiet
    if errorlevel 1 (
        echo  [ERREUR] Impossible d'installer les dependances.
        pause
        exit /b 1
    )
)
echo        Toutes les dependances sont presentes.
echo.

REM --- 4. Nettoyer les anciens builds (evite les erreurs OneDrive/verrouillage) ---
echo  [3/4] Nettoyage des anciens fichiers de build...
if exist "build" (
    rmdir /s /q "build" >nul 2>&1
    if exist "build" (
        echo        Le dossier build est verrouille. Tentative forcee...
        timeout /t 3 /nobreak >nul
        rmdir /s /q "build" >nul 2>&1
    )
    if exist "build" (
        echo        Impossible de supprimer build. Utilisation d'un dossier temporaire.
        set "WORK_OPT=--workpath %TEMP%\ADALM2000_build"
    ) else (
        echo        Ancien build supprime.
        set "WORK_OPT="
    )
) else (
    set "WORK_OPT="
)
if exist "dist\ADALM2000_Oscilloscope_x64" (
    rmdir /s /q "dist\ADALM2000_Oscilloscope_x64" >nul 2>&1
)
echo.

REM --- 5. Lancer la construction ---
echo  [4/4] Construction de l'executable...
echo        Cela peut prendre 2-5 minutes, veuillez patienter...
echo.

!PY! -m PyInstaller ADALM2000.spec --noconfirm !WORK_OPT!

if errorlevel 1 (
    echo.
    echo  [ERREUR] La construction a echoue !
    echo  Verifiez les messages d'erreur ci-dessus.
    pause
    exit /b 1
)

REM --- 6. Copier config.json si existant ---
if exist "src\config.json" (
    copy /Y "src\config.json" "dist\ADALM2000_Oscilloscope_x64\_internal\config.json" >nul 2>&1
    echo  [OK] config.json copie dans le dossier de distribution.
)

echo.
echo  ========================================================
echo           CONSTRUCTION REUSSIE !
echo  ========================================================
echo.
echo  L'executable est pret dans :
echo    dist\ADALM2000_Oscilloscope_x64\ADALM2000_Oscilloscope_x64.exe
echo.
echo  Pour distribuer : copiez tout le dossier
echo  "dist\ADALM2000_Oscilloscope_x64" sur une cle USB ou zip.
echo.
echo  Vos amis n'ont qu'a double-cliquer sur le .exe !
echo  Le driver ADALM2000 sera propose automatiquement
echo  si necessaire.
echo.
pause
