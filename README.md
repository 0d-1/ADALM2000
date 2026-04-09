# ADALM2000 Laboratory

Une application d'oscilloscope professionnelle et performante pour le module d'acquisition **Analog Devices ADALM2000**, développée en Python avec **PyQt6** et **pyqtgraph**.

Ce logiciel vise à remplacer l'utilisation de scripts basiques par une interface graphique complète, fluide (30+ FPS) et riche en fonctionnalités, se rapprochant des outils professionnels de laboratoire.

## ✨ Fonctionnalités Principales

*   **Oscilloscope Temps Réel** : Visualisation fluide sur 2 canaux (CH1, CH2) avec ajustement du gain, de l'offset, et de la base de temps.
*   **Contrôle Avancé des Sondes** : Support des sondes x1, x10, x100, couplage AC logiciel, et calibrage automatique du Zéro (DC Offset compensation).
*   **Déclenchement (Trigger)** : Trigger logiciel avec hystérésis paramétrable pour stabiliser les signaux périodiques.
*   **Générateur de Signaux (AWG)** : Contrôle des deux sorties analogiques (W1, W2) pour générer des signaux sinus, carrés, triangles, ou des impulsions personnalisées (ex: signaux à base de BPM).
*   **🤖 Génération assistée par IA** : Discutez avec une intelligence artificielle (Groq / Llama 3.3) pour décrire n'importe quel signal complexe en langage naturel, le prévisualiser et l'appliquer directement sur le matériel.
*   **Analyseur de Spectre (FFT)** : Calcul et affichage en temps réel de la transformée de Fourier, y compris sur des régions ciblées du graphe (ROI - *Region of Interest*).
*   **Outils de Mesure** :
    *   Curseurs Verticaux (Temps/Fréquence) et Horizontaux (Tension) pour des mesures précises sur le graphe.
    *   Voltmètre intégré avec calcul de DC, RMS, Vpp et estimation de la fréquence. Fonction de "Squelch" pour filtrer le bruit lorsque les sondes sont débranchées.
*   **Analyse Avancée** : Vue XY (Lissajous) et fonctions Mathématiques (CH1+CH2, CH1-CH2, CH1*CH2).
*   **Exportation & Enregistrement** :
    *   Exportation du graphique en image PNG haute résolution avec personnalisation du titre, des axes et des couleurs.
    *   Enregistrement continu des données (Data Logger) au format CSV pour des analyses de longue durée (ex: charge d'une batterie).
    *   Sauvegarde de "Snapshots" (capture des données actuelles à l'écran) en CSV et chargement de signaux de référence.

## 🛠️ Prérequis

*   Un module **ADALM2000** branché en USB.
*   **Python 3.9** ou supérieur installé sur votre ordinateur.
    *   *Important (Windows)* : Cochez bien la case **"Add Python to PATH"** lors de l'installation de Python.

## 📥 Installation

Des scripts d'installation automatisés sont fournis pour simplifier le processus et installer toutes les dépendances requises (`numpy`, `PyQt6`, `pyqtgraph`, `matplotlib`, `libm2k`).

### Sur Windows
1. Double-cliquez sur le fichier `install_windows.bat`.
2. Le script vérifiera votre version de Python et installera toutes les bibliothèques.
3. *Note sur `libm2k`* : Si l'installation automatique échoue, le script vous donnera les instructions pour installer la librairie manuellement via conda-forge ou l'installateur officiel d'Analog Devices.

### Sur macOS / Linux
1. Ouvrez un terminal.
2. Naviguez vers le dossier du projet.
3. Exécutez le script d'installation :
   ```bash
   bash install_mac.sh
   # ou
   chmod +x install_mac.sh && ./install_mac.sh
   ```

## 🚀 Démarrage

Une fois l'installation terminée, vous pouvez lancer l'application facilement :

### Sur Windows
Double-cliquez sur le raccourci **`Démarrer_Oscilloscope(WIN).bat`**.

### Sur macOS
Double-cliquez sur **`Démarrer_Oscilloscope(MAC).sh`** (ou lancez-le dans le terminal).

### En ligne de commande (Tous OS)
```bash
python src/main_oscilloscope.py
```

## 📖 Guide Rapide de l'Interface

L'interface est divisée en plusieurs panneaux et onglets :

1.  **Panneau de Contrôle Latéral (Gauche)** :
    *   **Contrôle Acquisition** : Démarrer/Mettre en pause l'acquisition en temps réel. Le bouton "Auto-Set" tente d'ajuster automatiquement les réglages pour visualiser le signal actuel.
    *   **Échelle de Temps** : Modifiez la base de temps globale (X) du graphique.
    *   **Réglages CH1 / CH2** : Activez ou désactivez les canaux. Ajustez les V/Div (échelle verticale), l'Offset (position), et l'épaisseur du trait.
2.  **Zone Graphique (Centre)** : Affiche les signaux. Faites clic droit -> "Analyse Graphe" pour ajouter des curseurs de mesure.
3.  **Panneau d'Onglets (Droite)** :
    *   **Générateurs** : Configurez les signaux de sortie pour W1 et W2.
    *   **🤖 IA** : Décrivez un signal en langage naturel et l'IA (Groq / Llama 3.3) le programmera pour vous. Clé API gratuite requise ([console.groq.com](https://console.groq.com/keys)).
    *   **Spectre (FFT)** : Activez la vue fréquentielle.
    *   **XY (Lissajous)** : Affiche CH1 en fonction de CH2.
    *   **Math** : Appliquez des opérations entre CH1 et CH2.
    *   **Voltmètre** : Retrouvez les mesures numériques détaillées.
    *   **Data Logger** : Enregistrez en continu dans un fichier CSV.
    *   **Export/Data** : Exportez le graphe en PNG qualité impression, ou sauvegardez les données brutes.

## ⚠️ Dépannage Fréquent

**"libm2k non trouvé" ou "ModuleNotFoundError: No module named 'libm2k'"**
La librairie `libm2k` d'Analog Devices est parfois complexe à installer via pip selon votre OS et version de Python.
*   **Solution recommandée** : Utilisez Miniconda et installez-la via `conda install -c conda-forge libm2k`.
*   **Alternative Windows** : Téléchargez l'installateur `.exe` depuis le [Github officiel d'Analog Devices](https://github.com/analogdevicesinc/libm2k/releases).

**L'application se fige ou manque de fluidité**
*   Assurez-vous de ne pas avoir une échelle de temps trop grande combinée à des calculs FFT complexes.
*   Désactivez les onglets XY ou Math s'ils ne sont pas utilisés.

**Les mesures du voltmètre bougent beaucoup alors que rien n'est branché ("Bruit")**

---
© 2024-2026 **Odin De Baerdemaker** - Tous droits réservés.
