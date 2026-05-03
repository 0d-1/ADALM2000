# -*- mode: python ; coding: utf-8 -*-
# ====================================================================
#   ADALM2000 Laboratory - Fichier de Configuration PyInstaller (ARM64)
#   © 2024-2026 Odin De Baerdemaker - Tous droits réservés
#
#   CE FICHIER CIBLE L'ARCHITECTURE ARM64 (Windows on ARM)
#   Il doit être exécuté NATIVEMENT sur une machine ARM64.
# ====================================================================

import os
import sys

block_cipher = None

# Chemin racine du projet
PROJECT_ROOT = os.path.abspath('.')
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')

a = Analysis(
    [os.path.join(SRC_DIR, 'main_oscilloscope.py')],
    pathex=[SRC_DIR],
    binaries=[],
    datas=[
        # Inclure l'icône de l'application
        (os.path.join(SRC_DIR, 'icon', 'viking_logo.png'), 'icon'),
        # Inclure le fichier d'exemple de configuration
        (os.path.join(SRC_DIR, 'config.json.example'), '.'),
        # Inclure l'installateur du driver libm2k
        # NOTE : Remplacer par le setup ARM64 si Analog Devices en publie un
        (os.path.join(PROJECT_ROOT, 'libm2k-0.9.0-setup.exe'), '.'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        'pyqtgraph',
        'pyqtgraph.exporters',
        'pyqtgraph.opengl',
        'numpy',
        'numpy.core',
        'numpy.fft',
        'csv',
        'json',
        'ctypes',
        'math',
        're',
        'urllib',
        'urllib.request',
        'traceback',
        # Modules locaux
        'oscilloscope_ui',
        'm2k_controller',
        'ai_signal_generator',
        'libm2k',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'PIL',
        'pandas',
        'IPython',
        'notebook',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ADALM2000_Oscilloscope_ARM64',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Pas de console noire visible
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',          # <-- Cible explicite ARM64
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(SRC_DIR, 'icon', 'viking_logo.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ADALM2000_Oscilloscope_ARM64',   # Dossier de sortie séparé
)
