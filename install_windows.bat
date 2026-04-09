@echo off
REM Copyright © 2024-2026 Odin De Baerdemaker - Tous droits réservés
setlocal EnableDelayedExpansion

REM ====================================================================
REM   ADALM2000 Laboratory - Installateur Windows
REM   Copyright © 2024-2026 Odin De Baerdemaker - Tous droits réservés
REM   Ce script installe toutes les dependances necessaires pour
REM   faire tourner l'oscilloscope ADALM2000 sous Windows.
REM ====================================================================

echo.
echo  ==============================================================
echo       ADALM2000 Laboratory - Installation des dependances
echo                        Windows Installer
echo  ==============================================================
echo.

REM --- Verifier que Python est installe ---
echo [1/6] Verification de Python...
where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERREUR : Python n'est pas installe ou n'est pas dans le PATH.
    echo.
    echo  Pour installer Python :
    echo    1. Allez sur https://www.python.org/downloads/
    echo    2. Telechargez Python 3.9 ou plus recent
    echo    3. IMPORTANT : Cochez "Add Python to PATH" pendant l'installation !
    echo    4. Relancez ce script apres l'installation.
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%V in ('python --version 2^>^&1') do set PYTHON_VER=%%V
echo  [OK] Python %PYTHON_VER% detecte.
echo.

REM --- Verifier que pip est disponible ---
echo [2/6] Verification de pip...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo  ERREUR : pip n'est pas installe.
    echo  Tentative d'installation de pip...
    python -m ensurepip --upgrade
    if errorlevel 1 (
        echo  ERREUR : Impossible d'installer pip automatiquement.
        pause
        exit /b 1
    )
)
echo  [OK] pip est disponible.
echo.

REM --- Mise a jour de pip ---
echo [3/6] Mise a jour de pip...
python -m pip install --upgrade pip
echo.

REM --- Installation des dependances Python (pip) ---
echo [4/6] Installation des paquets Python (numpy, PyQt6, pyqtgraph, matplotlib)...
echo.
python -m pip install numpy PyQt6 PyQt6-sip pyqtgraph matplotlib pyopengl
if errorlevel 1 (
    echo.
    echo  AVERTISSEMENT : Certains paquets pip n'ont pas pu etre installes.
    echo  Verifiez les messages d'erreur ci-dessus.
    echo.
) else (
    echo  [OK] Paquets pip installes avec succes.
)
echo.

REM --- Installation de libm2k ---
echo [5/6] Installation de libm2k (bibliotheque Analog Devices)...
echo.
echo  La bibliotheque libm2k necessite une installation speciale.
echo  Deux methodes sont disponibles :
echo.
echo    Option A : Via conda-forge (recommande si vous utilisez Anaconda/Miniconda)
echo    Option B : Via les wheels pre-compiles depuis GitHub
echo.

REM Essayer d'abord pip (wheels pre-compilees)
echo  Tentative d'installation via pip...
python -m pip install libm2k 2>nul
if errorlevel 1 (
    echo.
    echo  L'installation via pip a echoue. C'est normal si aucun wheel
    echo  n'est disponible pour votre version de Python.
    echo.

    REM Verifier si conda est disponible
    where conda >nul 2>&1
    if errorlevel 1 (
        echo  ==============================================================
        echo   INSTALLATION MANUELLE REQUISE POUR libm2k
        echo  ==============================================================
        echo.
        echo   Option 1 - Conda (recommande) :
        echo     1. Installez Miniconda: https://docs.conda.io
        echo     2. Puis executez :
        echo        conda install -c conda-forge libm2k
        echo.
        echo   Option 2 - Wheels GitHub :
        echo     1. Allez sur :
        echo        https://github.com/analogdevicesinc/libm2k/releases
        echo     2. Telechargez le .whl pour votre version Python/OS
        echo     3. Puis : pip install chemin\vers\le\fichier.whl
        echo.
        echo   Option 3 - Installeur Windows (.exe) :
        echo     1. Telechargez le MSI/EXE depuis :
        echo        https://github.com/analogdevicesinc/libm2k/releases
        echo     2. Installez-le (inclut libiio + bindings Python)
        echo.
        echo  ==============================================================
        echo.
    ) else (
        echo  Conda detecte ! Installation via conda-forge...
        conda install -y -c conda-forge libm2k
        if errorlevel 1 (
            echo  ERREUR : L'installation conda a echoue.
        ) else (
            echo  [OK] libm2k installe via conda-forge.
        )
    )
) else (
    echo  [OK] libm2k installe via pip.
)
echo.

REM --- Verification finale ---
echo [6/6] Verification de l'installation...
echo.
python -c "import numpy; print('  [OK] numpy', numpy.__version__)" 2>nul || echo  [ECHEC] numpy non trouve
python -c "from PyQt6.QtWidgets import QApplication; print('  [OK] PyQt6')" 2>nul || echo  [ECHEC] PyQt6 non trouve
python -c "import pyqtgraph; print('  [OK] pyqtgraph', pyqtgraph.__version__)" 2>nul || echo  [ECHEC] pyqtgraph non trouve
python -c "import matplotlib; print('  [OK] matplotlib', matplotlib.__version__)" 2>nul || echo  [ECHEC] matplotlib non trouve
python -c "import libm2k; print('  [OK] libm2k')" 2>nul || echo  [!!] libm2k non trouve - voir les instructions ci-dessus

echo.
echo  ==============================================================
echo   Installation terminee !
echo.
echo   Pour lancer l'oscilloscope :
echo     - Double-cliquez sur "Demarrer_Oscilloscope.bat"
echo     - Ou executez : python main_oscilloscope.py
echo  ==============================================================
echo.
pause
