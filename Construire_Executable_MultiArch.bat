@echo off
REM ====================================================================
REM   ADALM2000 Laboratory - Constructeur d'Executable Multi-Architecture
REM   Copyright (c) 2024-2026 Odin De Baerdemaker - Tous droits reserves
REM
REM   Ce script detecte automatiquement l'architecture du processeur
REM   et construit la version appropriee du logiciel :
REM     - x86-64  : sur PC Intel/AMD classique
REM     - ARM64   : sur PC/tablette Windows ARM (Snapdragon, Surface Pro X...)
REM ====================================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo.
echo  ========================================================
echo    ADALM2000 - Construction Multi-Architecture
echo  ========================================================
echo.

REM --- 1. Detecter l'architecture du processeur ---
echo  [Detection] Architecture du processeur...

set "ARCH=x64"
set "SPEC_FILE=ADALM2000.spec"
set "DIST_NAME=ADALM2000_Oscilloscope_x64"

REM PROCESSOR_ARCHITECTURE vaut "ARM64" nativement sur ARM64
REM Sur un processus 32-bit emule, PROCESSOR_ARCHITEW6432 contient la vraie arch
if /I "%PROCESSOR_ARCHITECTURE%"=="ARM64" (
    set "ARCH=ARM64"
    set "SPEC_FILE=ADALM2000_ARM64.spec"
    set "DIST_NAME=ADALM2000_Oscilloscope_ARM64"
)
if /I "%PROCESSOR_ARCHITEW6432%"=="ARM64" (
    set "ARCH=ARM64"
    set "SPEC_FILE=ADALM2000_ARM64.spec"
    set "DIST_NAME=ADALM2000_Oscilloscope_ARM64"
)

echo.
echo  *** Architecture detectee : !ARCH! ***
echo  *** Spec utilise          : !SPEC_FILE! ***
echo  *** Dossier de sortie     : dist\!DIST_NAME!\ ***
echo.

REM --- 2. Chercher Python ---
echo  [1/4] Recherche de Python...
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
    echo.
    echo  ATTENTION : Sur ARM64, assurez-vous d'installer Python ARM64 natif
    echo  (pas la version x86 emulee) depuis https://python.org/downloads/
    pause
    exit /b 1
)

echo  [OK] Python trouve : !PY!
!PY! --version
echo.

REM --- 2b. Verifier que Python est natif ARM64 (avertissement seulement) ---
if /I "!ARCH!"=="ARM64" (
    for /f "tokens=*" %%A in ('!PY! -c "import platform; print(platform.machine())"') do set "PY_ARCH=%%A"
    echo  [Info] Architecture de Python : !PY_ARCH!
    if /I not "!PY_ARCH!"=="ARM64" (
        echo.
        echo  [AVERTISSEMENT] Python n'est pas ARM64 natif ^(!PY_ARCH!^).
        echo  L'exe produit ne sera PAS optimise pour ARM64.
        echo  Installez Python ARM64 natif depuis https://python.org/downloads/
        echo  pour un binaire ARM64 optimal.
        echo.
        timeout /t 5 /nobreak >nul
    ) else (
        echo  [OK] Python ARM64 natif detecte.
    )
    echo.
)

REM --- 3. Installer PyInstaller si necessaire ---
echo  [2/4] Verification de PyInstaller...
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
echo  [OK] PyInstaller est pret.
echo.

REM --- 4. Verifier les dependances du projet ---
echo  [3/4] Verification des dependances du projet...
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
echo  [OK] Toutes les dependances sont presentes.
echo.

REM --- 5. Nettoyer les anciens builds ---
echo  [4/4] Nettoyage et construction...
if exist "build" (
    rmdir /s /q "build" >nul 2>&1
    if exist "build" (
        echo        Le dossier build est verrouille. Utilisation d'un dossier temporaire.
        set "WORK_OPT=--workpath %TEMP%\ADALM2000_build"
    ) else (
        set "WORK_OPT="
    )
) else (
    set "WORK_OPT="
)

if exist "dist\!DIST_NAME!" (
    rmdir /s /q "dist\!DIST_NAME!" >nul 2>&1
)

echo.
echo  Construction de l'executable !ARCH!...
echo  Cela peut prendre 2-5 minutes, veuillez patienter...
echo.

!PY! -m PyInstaller !SPEC_FILE! --noconfirm !WORK_OPT!

if errorlevel 1 (
    echo.
    echo  [ERREUR] La construction a echoue !
    echo  Verifiez les messages d'erreur ci-dessus.
    pause
    exit /b 1
)

REM --- 6. Copier config.json si existant ---
if exist "src\config.json" (
    copy /Y "src\config.json" "dist\!DIST_NAME!\_internal\config.json" >nul 2>&1
    echo  [OK] config.json copie dans le dossier de distribution.
)

echo.
echo  ========================================================
echo        CONSTRUCTION !ARCH! REUSSIE !
echo  ========================================================
echo.
echo  L'executable est pret dans :
echo    dist\!DIST_NAME!\!DIST_NAME!.exe
echo.
if /I "!ARCH!"=="ARM64" (
    echo  NOTE ARM64 : Le driver libm2k (Analog Devices) doit etre
    echo  installe en version ARM64 pour que l'acquisition fonctionne.
    echo  Verifiez : https://github.com/analogdevicesinc/libm2k/releases
    echo.
)
echo  Pour distribuer : copiez tout le dossier
echo  "dist\!DIST_NAME!" sur une cle USB ou zip.
echo.
echo  Vos amis n'ont qu'a double-cliquer sur le .exe !
echo.
pause
