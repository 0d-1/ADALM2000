@echo off
REM ====================================================================
REM   ADALM2000 Laboratory - Rendre les bibliothèques portables
REM   Ce script télécharge toutes les bibliothèques directement 
REM   dans le dossier "libs", pour ne plus avoir à les installer.
REM ====================================================================

cd /d "%~dp0"
echo Téléchargement des bibliothèques dans le dossier "libs"...
echo Cela peut prendre quelques minutes.

python -m pip install -t libs PyQt6 pyqtgraph numpy groq python-dotenv

echo.
echo Terminé ! Vous pouvez désormais partager ce dossier. 
echo Les utilisateurs n'auront plus besoin d'installer ces bibliothèques.
pause
