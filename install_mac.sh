#!/bin/bash
# Copyright © 2024-2026 Odin De Baerdemaker - Tous droits réservés
# ====================================================================
#   ADALM2000 Laboratory - Installateur macOS
#   Ce script installe toutes les dépendances nécessaires pour
#   faire tourner l'oscilloscope ADALM2000 sous macOS.
# ====================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo ""
echo -e "${CYAN}${BOLD}"
echo "  ╔══════════════════════════════════════════════════════════════╗"
echo "  ║     ADALM2000 Laboratory - Installation des dépendances    ║"
echo "  ║                      macOS Installer                       ║"
echo "  ╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# --- Se placer dans le répertoire du script ---
cd "$(dirname "$0")"

# --- Fonction utilitaire ---
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}[OK]${NC} $1"
    else
        echo -e "  ${RED}[ECHEC]${NC} $1"
        return 1
    fi
}

# ====================================================================
# ÉTAPE 1 : Vérifier Homebrew
# ====================================================================
echo -e "${BOLD}[1/7] Vérification de Homebrew...${NC}"
if ! command -v brew &> /dev/null; then
    echo -e "  ${YELLOW}Homebrew n'est pas installé. Installation en cours...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Ajouter Homebrew au PATH si nécessaire (Apple Silicon)
    if [ -f "/opt/homebrew/bin/brew" ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    fi
fi
echo -e "  ${GREEN}[OK]${NC} Homebrew est disponible."
echo ""

# ====================================================================
# ÉTAPE 2 : Vérifier Python 3
# ====================================================================
echo -e "${BOLD}[2/7] Vérification de Python 3...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "  ${YELLOW}Python 3 n'est pas installé. Installation via Homebrew...${NC}"
    brew install python@3
fi
PYTHON_VER=$(python3 --version 2>&1)
echo -e "  ${GREEN}[OK]${NC} $PYTHON_VER détecté."
echo ""

# ====================================================================
# ÉTAPE 3 : Mise à jour de pip
# ====================================================================
echo -e "${BOLD}[3/7] Mise à jour de pip...${NC}"
python3 -m pip install --upgrade pip 2>/dev/null || python3 -m ensurepip --upgrade
echo -e "  ${GREEN}[OK]${NC} pip est à jour."
echo ""

# ====================================================================
# ÉTAPE 4 : Installation des dépendances système via Homebrew
# ====================================================================
echo -e "${BOLD}[4/7] Installation des dépendances système (libiio, libusb)...${NC}"
brew install libusb 2>/dev/null || true

# libiio est nécessaire pour libm2k
if ! brew list libiio &> /dev/null; then
    echo -e "  ${YELLOW}Installation de libiio...${NC}"
    brew install libiio 2>/dev/null || {
        echo -e "  ${YELLOW}libiio non disponible via brew, tentative avec conda plus tard...${NC}"
    }
else
    echo -e "  ${GREEN}[OK]${NC} libiio déjà installé."
fi
echo ""

# ====================================================================
# ÉTAPE 5 : Installation des paquets Python (pip)
# ====================================================================
echo -e "${BOLD}[5/7] Installation des paquets Python (numpy, PyQt6, pyqtgraph, matplotlib)...${NC}"
echo ""
python3 -m pip install numpy PyQt6 PyQt6-sip pyqtgraph matplotlib pyopengl
echo ""
echo -e "  ${GREEN}[OK]${NC} Paquets pip installés."
echo ""

# ====================================================================
# ÉTAPE 6 : Installation de libm2k
# ====================================================================
echo -e "${BOLD}[6/7] Installation de libm2k (bibliothèque Analog Devices)...${NC}"
echo ""

LIBM2K_INSTALLED=false

# Méthode 1 : pip
echo -e "  Tentative d'installation via pip..."
if python3 -m pip install libm2k 2>/dev/null; then
    echo -e "  ${GREEN}[OK]${NC} libm2k installé via pip."
    LIBM2K_INSTALLED=true
else
    echo -e "  ${YELLOW}[--]${NC} pip : aucun wheel disponible pour cette configuration."
fi

# Méthode 2 : conda-forge
if [ "$LIBM2K_INSTALLED" = false ]; then
    if command -v conda &> /dev/null; then
        echo -e "  Tentative d'installation via conda-forge..."
        if conda install -y -c conda-forge libm2k 2>/dev/null; then
            echo -e "  ${GREEN}[OK]${NC} libm2k installé via conda-forge."
            LIBM2K_INSTALLED=true
        fi
    fi
fi

# Méthode 3 : Instructions manuelles
if [ "$LIBM2K_INSTALLED" = false ]; then
    echo ""
    echo -e "${YELLOW}${BOLD}"
    echo "  ╔══════════════════════════════════════════════════════════════╗"
    echo "  ║  INSTALLATION MANUELLE REQUISE POUR libm2k                 ║"
    echo "  ╠══════════════════════════════════════════════════════════════╣"
    echo "  ║                                                            ║"
    echo "  ║  Option 1 - Conda (recommandé) :                          ║"
    echo "  ║    1. Installez Miniconda :                                ║"
    echo "  ║       https://docs.conda.io/en/latest/miniconda.html       ║"
    echo "  ║    2. Puis exécutez :                                      ║"
    echo "  ║       conda install -c conda-forge libm2k                  ║"
    echo "  ║                                                            ║"
    echo "  ║  Option 2 - Compilation depuis les sources :               ║"
    echo "  ║    1. brew install cmake libiio libusb                      ║"
    echo "  ║    2. git clone https://github.com/analogdevicesinc/libm2k  ║"
    echo "  ║    3. cd libm2k && mkdir build && cd build                  ║"
    echo "  ║    4. cmake .. -DENABLE_PYTHON=ON                           ║"
    echo "  ║    5. make && sudo make install                              ║"
    echo "  ║                                                            ║"
    echo "  ╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
fi
echo ""

# ====================================================================
# ÉTAPE 7 : Vérification finale
# ====================================================================
echo -e "${BOLD}[7/7] Vérification de l'installation...${NC}"
echo ""

python3 -c "import numpy; print('  ✅ numpy', numpy.__version__)" 2>/dev/null \
    || echo -e "  ${RED}❌ numpy non trouvé${NC}"

python3 -c "from PyQt6.QtWidgets import QApplication; print('  ✅ PyQt6')" 2>/dev/null \
    || echo -e "  ${RED}❌ PyQt6 non trouvé${NC}"

python3 -c "import pyqtgraph; print('  ✅ pyqtgraph', pyqtgraph.__version__)" 2>/dev/null \
    || echo -e "  ${RED}❌ pyqtgraph non trouvé${NC}"

python3 -c "import matplotlib; print('  ✅ matplotlib', matplotlib.__version__)" 2>/dev/null \
    || echo -e "  ${RED}❌ matplotlib non trouvé${NC}"

python3 -c "import libm2k; print('  ✅ libm2k')" 2>/dev/null \
    || echo -e "  ${YELLOW}⚠️  libm2k non trouvé - voir les instructions ci-dessus${NC}"

echo ""
echo -e "${CYAN}${BOLD}"
echo "  ══════════════════════════════════════════════════════════════"
echo "   Installation terminée !"
echo ""
echo "   Pour lancer l'oscilloscope :"
echo "     python3 main_oscilloscope.py"
echo "  ══════════════════════════════════════════════════════════════"
echo -e "${NC}"
echo ""
