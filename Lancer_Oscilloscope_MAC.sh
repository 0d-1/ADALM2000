#!/bin/bash
# Copyright © 2024-2026 Odin De Baerdemaker - Tous droits réservés
# ADALM2000 Laboratory - Lanceur Rapide macOS/Linux

cd "$(dirname "$0")"

# Chercher Python 3
if command -v python3 &> /dev/null; then
    PY="python3"
elif command -v python &> /dev/null; then
    if python --version 2>&1 | grep -q "Python 3"; then
        PY="python"
    fi
fi

if [ -z "$PY" ]; then
    echo ""
    echo "ERREUR : Python 3 n'est pas installé !"
    echo "Lancez d'abord Installer_ADALM2000_MAC.sh"
    echo ""
    read -p "Appuyez sur Entrée pour quitter..."
    exit 1
fi

$PY src/main_oscilloscope.py
