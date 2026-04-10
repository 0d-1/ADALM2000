@echo off
REM ====================================================================
REM   ADALM2000 Laboratory - Installateur Automatique Windows
REM   Copyright (c) 2024-2026 Odin De Baerdemaker - Tous droits reserves
REM
REM   Ce script installe TOUT ce qui est necessaire pour faire tourner
REM   l'oscilloscope ADALM2000. Il suffit de double-cliquer dessus.
REM ====================================================================
setlocal EnableDelayedExpansion

REM --- Couleurs via mode con ---
title ADALM2000 Laboratory - Installation

REM --- Se placer dans le dossier du script ---
cd /d "%~dp0"

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║                                                            ║
echo  ║        ADALM2000 Laboratory - Installateur Complet         ║
echo  ║                                                            ║
echo  ║   Ce script va installer automatiquement tout ce dont      ║
echo  ║   vous avez besoin pour utiliser l'oscilloscope.           ║
echo  ║                                                            ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.
echo  Veuillez patienter, l'installation peut prendre quelques minutes...
echo.

REM ====================================================================
REM ETAPE 1 : Verifier / Installer Python
REM ====================================================================
echo  ──────────────────────────────────────────────────────────────
echo   [1/7] Verification de Python...
echo  ──────────────────────────────────────────────────────────────

set "PYTHON_CMD="

REM --- Essayer python dans le PATH ---
where python >nul 2>&1
if not errorlevel 1 (
    REM Verifier que ce n'est pas le stub Windows Store
    python --version >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=2" %%V in ('python --version 2^>^&1') do set PYTHON_VER=%%V
        REM Verifier que c'est un vrai Python (pas le redirecteur Windows Store)
        python -c "import sys; sys.exit(0)" >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_CMD=python"
            echo   [OK] Python !PYTHON_VER! detecte dans le PATH.
        )
    )
)

REM --- Essayer python3 ---
if not defined PYTHON_CMD (
    where python3 >nul 2>&1
    if not errorlevel 1 (
        python3 --version >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_CMD=python3"
            for /f "tokens=2" %%V in ('python3 --version 2^>^&1') do set PYTHON_VER=%%V
            echo   [OK] Python !PYTHON_VER! detecte (python3^).
        )
    )
)

REM --- Essayer py launcher ---
if not defined PYTHON_CMD (
    where py >nul 2>&1
    if not errorlevel 1 (
        py --version >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_CMD=py"
            for /f "tokens=2" %%V in ('py --version 2^>^&1') do set PYTHON_VER=%%V
            echo   [OK] Python !PYTHON_VER! detecte (py launcher^).
        )
    )
)

REM --- Essayer des chemins courants ---
if not defined PYTHON_CMD (
    for %%P in (
        "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
        "C:\Python313\python.exe"
        "C:\Python312\python.exe"
        "C:\Python311\python.exe"
        "C:\Python310\python.exe"
        "C:\Python39\python.exe"
    ) do (
        if exist %%P (
            if not defined PYTHON_CMD (
                set "PYTHON_CMD=%%~P"
                for /f "tokens=2" %%V in ('"%%~P" --version 2^>^&1') do set PYTHON_VER=%%V
                echo   [OK] Python !PYTHON_VER! trouve dans %%~P
            )
        )
    )
)

REM --- Si toujours pas, tenter installation automatique via winget ---
if not defined PYTHON_CMD (
    echo.
    echo   [!!] Python n'est pas installe sur cet ordinateur.
    echo.
    
    REM Essayer winget
    where winget >nul 2>&1
    if not errorlevel 1 (
        echo   Installation automatique de Python via winget...
        echo   (Cela peut prendre 1-2 minutes^)
        echo.
        winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements --silent
        
        if not errorlevel 1 (
            REM Rafraichir le PATH
            set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
            
            REM Verifier
            "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" --version >nul 2>&1
            if not errorlevel 1 (
                set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
                echo.
                echo   [OK] Python 3.12 installe avec succes !
            )
        )
    )
)

REM --- Dernier recours : telechargement direct ---
if not defined PYTHON_CMD (
    echo.
    echo   Tentative de telechargement direct de Python...
    
    set "PY_INSTALLER=%TEMP%\python_installer.exe"
    set "PY_URL=https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"
    
    REM Utiliser curl ou PowerShell pour telecharger
    where curl >nul 2>&1
    if not errorlevel 1 (
        curl -L -o "!PY_INSTALLER!" "!PY_URL!" 2>nul
    ) else (
        powershell -Command "Invoke-WebRequest -Uri '!PY_URL!' -OutFile '!PY_INSTALLER!'" 2>nul
    )
    
    if exist "!PY_INSTALLER!" (
        echo.
        echo   Installation de Python en mode silencieux...
        echo   (Ajout automatique au PATH inclus^)
        echo.
        "!PY_INSTALLER!" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
        
        REM Attendre la fin de l'installation
        timeout /t 30 /nobreak >nul
        
        REM Rafraichir le PATH
        set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
        
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" --version >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
            echo   [OK] Python installe avec succes !
        )
        
        del "!PY_INSTALLER!" 2>nul
    )
)

REM --- Echec total ---
if not defined PYTHON_CMD (
    echo.
    echo  ╔══════════════════════════════════════════════════════════════╗
    echo  ║  ERREUR : Impossible d'installer Python automatiquement    ║
    echo  ║                                                            ║
    echo  ║  Veuillez installer Python manuellement :                  ║
    echo  ║    1. Allez sur https://www.python.org/downloads/          ║
    echo  ║    2. Telechargez Python 3.12 ou plus recent               ║
    echo  ║    3. IMPORTANT : Cochez "Add Python to PATH" !            ║
    echo  ║    4. Relancez ce script apres l'installation.             ║
    echo  ╚══════════════════════════════════════════════════════════════╝
    echo.
    echo  Ouverture de la page de telechargement Python...
    start "" "https://www.python.org/downloads/"
    echo.
    pause
    exit /b 1
)

echo.

REM ====================================================================
REM ETAPE 2 : Verifier pip
REM ====================================================================
echo  ──────────────────────────────────────────────────────────────
echo   [2/7] Verification de pip...
echo  ──────────────────────────────────────────────────────────────
%PYTHON_CMD% -m pip --version >nul 2>&1
if errorlevel 1 (
    echo   Installation de pip...
    %PYTHON_CMD% -m ensurepip --upgrade >nul 2>&1
    if errorlevel 1 (
        echo   [!!] Tentative alternative pour installer pip...
        curl -sS https://bootstrap.pypa.io/get-pip.py -o "%TEMP%\get-pip.py" 2>nul
        if exist "%TEMP%\get-pip.py" (
            %PYTHON_CMD% "%TEMP%\get-pip.py" >nul 2>&1
            del "%TEMP%\get-pip.py" 2>nul
        )
    )
)
echo   [OK] pip est disponible.
echo.

REM ====================================================================
REM ETAPE 3 : Mise a jour de pip
REM ====================================================================
echo  ──────────────────────────────────────────────────────────────
echo   [3/7] Mise a jour de pip...
echo  ──────────────────────────────────────────────────────────────
%PYTHON_CMD% -m pip install --upgrade pip --quiet 2>nul
echo   [OK] pip est a jour.
echo.

REM ====================================================================
REM ETAPE 4 : Installation des dependances Python
REM ====================================================================
echo  ──────────────────────────────────────────────────────────────
echo   [4/7] Installation des paquets Python...
echo  ──────────────────────────────────────────────────────────────
echo.
echo   Installation de numpy...
%PYTHON_CMD% -m pip install numpy --quiet 2>nul
echo   Installation de PyQt6...
%PYTHON_CMD% -m pip install PyQt6 PyQt6-sip --quiet 2>nul
echo   Installation de pyqtgraph...
%PYTHON_CMD% -m pip install pyqtgraph --quiet 2>nul
echo   Installation de matplotlib...
%PYTHON_CMD% -m pip install matplotlib --quiet 2>nul
echo   Installation de pyopengl...
%PYTHON_CMD% -m pip install pyopengl --quiet 2>nul
echo.
echo   [OK] Paquets Python installes.
echo.

REM ====================================================================
REM ETAPE 5 : Installation de libm2k
REM ====================================================================
echo  ──────────────────────────────────────────────────────────────
echo   [5/7] Installation de libm2k (Analog Devices)...
echo  ──────────────────────────────────────────────────────────────
echo.

set LIBM2K_OK=0

REM Verifier si deja installe
%PYTHON_CMD% -c "import libm2k" >nul 2>&1
if not errorlevel 1 (
    echo   [OK] libm2k est deja installe.
    set LIBM2K_OK=1
)

REM Methode 1 : pip
if !LIBM2K_OK! EQU 0 (
    echo   Tentative via pip...
    %PYTHON_CMD% -m pip install libm2k --quiet 2>nul
    %PYTHON_CMD% -c "import libm2k" >nul 2>&1
    if not errorlevel 1 (
        echo   [OK] libm2k installe via pip.
        set LIBM2K_OK=1
    ) else (
        echo   [--] Pas de wheel pip disponible pour cette version de Python.
    )
)

REM Methode 2 : conda
if !LIBM2K_OK! EQU 0 (
    where conda >nul 2>&1
    if not errorlevel 1 (
        echo   Tentative via conda-forge...
        conda install -y -c conda-forge libm2k >nul 2>&1
        %PYTHON_CMD% -c "import libm2k" >nul 2>&1
        if not errorlevel 1 (
            echo   [OK] libm2k installe via conda-forge.
            set LIBM2K_OK=1
        )
    )
)

if !LIBM2K_OK! EQU 0 (
    echo.
    echo   ╔══════════════════════════════════════════════════════╗
    echo   ║  NOTE : libm2k n'a pas pu etre installe            ║
    echo   ║  automatiquement.                                   ║
    echo   ║                                                     ║
    echo   ║  L'oscilloscope fonctionnera en mode               ║
    echo   ║  "deconnecte" (sans materiel ADALM2000).            ║
    echo   ║                                                     ║
    echo   ║  Pour l'ADALM2000 physique, installez libm2k :     ║
    echo   ║  - conda install -c conda-forge libm2k             ║
    echo   ║  - Ou telechargez l'installeur .exe depuis :       ║
    echo   ║    github.com/analogdevicesinc/libm2k/releases     ║
    echo   ╚══════════════════════════════════════════════════════╝
    echo.
)

REM ====================================================================
REM ETAPE 6 : Configuration initiale
REM ====================================================================
echo  ──────────────────────────────────────────────────────────────
echo   [6/7] Configuration initiale...
echo  ──────────────────────────────────────────────────────────────

REM Creer config.json a partir de l'exemple s'il n'existe pas
if not exist "src\config.json" (
    if exist "src\config.json.example" (
        copy "src\config.json.example" "src\config.json" >nul 2>&1
        echo   [OK] Fichier de configuration cree (src\config.json^).
    ) else (
        REM Creer un config.json minimal
        echo { > "src\config.json"
        echo   "icon_path": "./icon/MSN Explorer.png", >> "src\config.json"
        echo   "gemini_api_key": "", >> "src\config.json"
        echo   "groq_api_key": "" >> "src\config.json"
        echo } >> "src\config.json"
        echo   [OK] Fichier de configuration cree.
    )
) else (
    echo   [OK] Fichier de configuration deja present.
)

REM Creer le lanceur rapide a cote de l'installeur
echo @echo off > "Lancer_Oscilloscope.bat"
echo REM Copyright (c) 2024-2026 Odin De Baerdemaker - Tous droits reserves >> "Lancer_Oscilloscope.bat"
echo cd /d "%%~dp0" >> "Lancer_Oscilloscope.bat"
echo start "" %PYTHON_CMD% src/main_oscilloscope.py >> "Lancer_Oscilloscope.bat"

echo   [OK] Lanceur rapide cree (Lancer_Oscilloscope.bat^).
echo.

REM ====================================================================
REM ETAPE 7 : Verification finale
REM ====================================================================
echo  ──────────────────────────────────────────────────────────────
echo   [7/7] Verification finale de l'installation...
echo  ──────────────────────────────────────────────────────────────
echo.

set ERRORS=0

%PYTHON_CMD% -c "import numpy; print('   [OK] numpy', numpy.__version__)" 2>nul
if errorlevel 1 (
    echo    [ECHEC] numpy
    set /a ERRORS+=1
)

%PYTHON_CMD% -c "from PyQt6.QtWidgets import QApplication; print('   [OK] PyQt6')" 2>nul
if errorlevel 1 (
    echo    [ECHEC] PyQt6
    set /a ERRORS+=1
)

%PYTHON_CMD% -c "import pyqtgraph; print('   [OK] pyqtgraph', pyqtgraph.__version__)" 2>nul
if errorlevel 1 (
    echo    [ECHEC] pyqtgraph
    set /a ERRORS+=1
)

%PYTHON_CMD% -c "import matplotlib; print('   [OK] matplotlib', matplotlib.__version__)" 2>nul
if errorlevel 1 (
    echo    [ECHEC] matplotlib
    set /a ERRORS+=1
)

%PYTHON_CMD% -c "import libm2k; print('   [OK] libm2k')" 2>nul
if errorlevel 1 (
    echo    [!!] libm2k non disponible (mode hors-ligne uniquement^)
)

echo.

if !ERRORS! GTR 0 (
    echo  ╔══════════════════════════════════════════════════════════════╗
    echo  ║  ATTENTION : Certains paquets n'ont pas pu etre installes  ║
    echo  ║  Verifiez les messages d'erreur ci-dessus.                 ║
    echo  ║  Essayez de relancer ce script en tant qu'Administrateur.  ║
    echo  ╚══════════════════════════════════════════════════════════════╝
) else (
    echo  ╔══════════════════════════════════════════════════════════════╗
    echo  ║                                                            ║
    echo  ║           INSTALLATION TERMINEE AVEC SUCCES !              ║
    echo  ║                                                            ║
    echo  ╠══════════════════════════════════════════════════════════════╣
    echo  ║                                                            ║
    echo  ║  Pour lancer l'oscilloscope :                              ║
    echo  ║                                                            ║
    echo  ║    - Double-cliquez sur "Lancer_Oscilloscope.bat"          ║
    echo  ║    - Ou sur "Demarrer_Oscilloscope(WIN).bat"               ║
    echo  ║                                                            ║
    echo  ╚══════════════════════════════════════════════════════════════╝
)

echo.
echo  ──────────────────────────────────────────────────────────────
echo   Voulez-vous lancer l'oscilloscope maintenant ? (O/N^)
echo  ──────────────────────────────────────────────────────────────
echo.
set /p LAUNCH="  Votre choix [O/N] : "

if /i "!LAUNCH!"=="O" (
    echo.
    echo   Lancement de ADALM2000 Laboratory...
    echo.
    start "" %PYTHON_CMD% src/main_oscilloscope.py
) else if /i "!LAUNCH!"=="Y" (
    echo.
    echo   Lancement de ADALM2000 Laboratory...
    echo.
    start "" %PYTHON_CMD% src/main_oscilloscope.py
)

echo.
echo  Merci d'utiliser ADALM2000 Laboratory !
echo.
pause
