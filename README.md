# 🔬 ADALM2000 Laboratory - L'Oscilloscope Augmenté par l'IA

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![UI Framework](https://img.shields.io/badge/UI-PyQt6-blueviolet)](https://www.riverbankcomputing.com/software/pyqt/)
[![AI Powered](https://img.shields.io/badge/AI-Groq%20%2F%20Llama%203.3-orange)](https://groq.com/)

Une plateforme d'instrumentation professionnelle pour le module **Analog Devices ADALM2000**, propulsée par l'intelligence artificielle pour une expérience de laboratoire révolutionnaire.

---

## 🤖 L'Intelligence Artificielle au Cœur du Signal

Contrairement aux outils traditionnels, **ADALM2000 Laboratory** intègre un assistant de signal intelligent basé sur les derniers modèles de langage (**Llama 3.3 via Groq**).

*   **Pilotage en Langage Naturel** : Plus besoin de formules complexes ou de scripts manuels. "Génère une sinusoïde de 1kHz avec une amplitude de 2V" suffit pour configurer votre matériel.
*   **Prototypage de Signaux Complexes** : Demandez des signaux sophistiqués (Chirps, modulations, bruit rose, impulsions physiologiques) et l'IA écrit le code NumPy optimal en temps réel.
*   **Prévisualisation IA** : Visualisez instantanément la réponse théorique générée par l'IA avant de l'envoyer physiquement sur les sorties W1/W2.
*   **Correction Itérative** : Discutez avec l'IA pour affiner votre signal ("Ajoute un peu de bruit", "Augmente la fréquence de 20%").

---

## ✨ Fonctionnalités Principales

### 📊 Analyses de Précision
*   **Oscilloscope Temps Réel** : Visualisation fluide sur 2 canaux (CH1, CH2) à 30+ FPS avec réglages de gain et offset.
*   **Analyseur de Spectre (FFT)** : Transformée de Fourier rapide avec fenêtre de Hann et support des régions d'intérêt (ROI).
*   **Voltmètre Intelligent** : Mesures DC, RMS, Vpp et fréquence avec filtre "Squelch" anti-bruit.
*   **Analyse de Lissajous (XY)** : Mode XY pour l'étude des déphasages et des composants.

### ⚙️ Contrôle Avancé
*   **Générateur de Signaux (AWG)** : Deux sorties indépendantes (W1, W2) avec pré-réglages pro et mode personnalisé.
*   **Trigger Logiciel Expert** : Stabilisation parfaite des signaux grâce au trigger avec hystérésis paramétrable.
*   **Outils de Mesure** : Curseurs verticaux (Temps/Freq) et horizontaux (Tension) pour une précision chirurgicale.

### 💾 Gestion des Données
*   **Data Logger** : Enregistrement continu longue durée (CSV) pour le monitoring.
*   **Exportation Haute Qualité** : Capturez vos résultats en PNG haute résolution pour vos rapports et publications.
*   **Snapshots & Références** : Sauvegardez un état instantané ou chargez un signal de référence pour comparaison.

---

## 🚀 Démarrage Rapide

### 1️⃣ Installation Automatique (Windows)
Double-cliquez sur **`Installer_ADALM2000.bat`**. 
L'installeur gère l'installation de Python, des drivers `libm2k` et des dépendances (`numpy`, `PyQt6`, `pyqtgraph`).

### 2️⃣ Utilisation de l'IA
1. Rendez-vous dans l'onglet **🤖 IA**.
2. Entrez votre clé API gratuite [Groq](https://console.groq.com/keys).
3. Décrivez votre besoin : *"Génère un signal ECG simulé à 60 BPM"* ou *"Simule une décharge de condensateur"*.

---

## 🛠️ Configuration Technique

*   **Matériel** : Analog Devices ADALM2000.
*   **Logiciel** : Python 3.9+, PyQt6, Pyqtgraph, Libm2k.
*   **AI Backend** : API Groq (Modèles Llama 3.3, 3.1).

---

## ⚠️ Dépannage
Si la librairie `libm2k` pose problème lors de l'installation manuelle, privilégiez l'installeur automatique ou utilisez **Conda** :
```bash
conda install -c conda-forge libm2k
```

---
---
© 2024-2026 **Odin De Baerdemaker** - L'innovation au service de l'électronique.
