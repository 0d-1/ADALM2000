"""
ADALM2000 Laboratory - Oscilloscope Application
© 2024-2026 Odin De Baerdemaker - Tous droits réservés
"""
import sys
import os
import time
import json
import ctypes
import subprocess
import csv
import urllib.request
import webbrowser
import threading
import zipfile
import shutil
import tempfile
from datetime import datetime
import numpy as np
from PyQt6.QtWidgets import (QApplication, QColorDialog, QFileDialog, QSplashScreen, QProgressBar, 
                             QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox, QMainWindow, QLabel)
from PyQt6.QtGui import QIcon, QPixmap, QFont
from PyQt6.QtCore import Qt, QTimer, QMetaObject, Q_ARG, QObject, pyqtSignal, pyqtSlot
import pyqtgraph as pg
import pyqtgraph.exporters
from oscilloscope_ui import OscilloscopeUI
from m2k_controller import M2kController, LIBM2K_AVAILABLE
from ai_signal_generator import AISignalGenerator

# --- Support Exécutable Autonome (PyInstaller) ---
if getattr(sys, 'frozen', False):
    _BASE_DIR = sys._MEIPASS
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    libs_path = os.path.abspath(os.path.join(_BASE_DIR, '..', 'libs'))
    if os.path.exists(libs_path):
        sys.path.insert(0, libs_path)
# -------------------------------------------------

class ExportSettingsDialog(QDialog):
    def __init__(self, parent=None, current_title="", current_x="", current_y=""):
        super().__init__(parent)
        self.setWindowTitle("Paramètres d'Exportation PNG")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        self.title_edit = QLineEdit(current_title)
        self.x_label_edit = QLineEdit(current_x)
        self.y_label_edit = QLineEdit(current_y)
        
        form_layout.addRow("Titre du graphique :", self.title_edit)
        form_layout.addRow("Nom de l'axe X (Horizontal) :", self.x_label_edit)
        form_layout.addRow("Nom de l'axe Y (Vertical) :", self.y_label_edit)
        
        layout.addLayout(form_layout)
        
        # Bouton OK/Annuler
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def get_values(self):
        return {
            "title": self.title_edit.text(),
            "x_label": self.x_label_edit.text(),
            "y_label": self.y_label_edit.text()
        }

class OscilloscopeApp(QObject):
    VERSION = "1.3.2"
    UPDATE_URL = "https://voie-du-savoir.go.yj.fr/scodin/version.txt"
    DOWNLOAD_URL = "https://voie-du-savoir.go.yj.fr/scodin/ADALM2000_Oscilloscope.zip"

    def __init__(self):
        super().__init__()
        self.app = QApplication.instance() or QApplication(sys.argv)
        
        # --- App Icon Logic ---
        # Utilise _BASE_DIR qui gère automatiquement le mode .exe et le mode script
        self._script_dir = _BASE_DIR
        self.config_file = os.path.join(self._script_dir, "config.json")
        icon_path = self.load_icon_path()
        if icon_path and os.path.exists(icon_path):
            self.app.setWindowIcon(QIcon(icon_path))
        
        # Windows taskbar pin identity separation
        try:
            myappid = 'm2k.oscilloscope.v2'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

        # --- Splash Screen ---
        splash_pix = QPixmap(500, 350)
        splash_pix.fill(Qt.GlobalColor.black) # Plus moderne en noir
        
        # On peut imaginer un logo ici plus tard, pour l'instant text pro
        splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
        
        # Ajout d'une barre de progression personnalisée sur le Splash
        self.splash_progress = QProgressBar(splash)
        self.splash_progress.setGeometry(50, 280, 400, 25)
        self.splash_progress.setRange(0, 100)
        self.splash_progress.setValue(0)
        self.splash_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #5bc0de;
                border-radius: 5px;
                text-align: center;
                color: white;
                background-color: #222;
            }
            QProgressBar::chunk {
                background-color: #5bc0de;
                width: 20px;
            }
        """)
        
        splash.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        splash.showMessage(f"\n\n\nADALM2000 Laboratory (v{self.VERSION})\nChargement des modules...", Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, Qt.GlobalColor.white)
        splash.show()
        self.app.processEvents()

        self.ui = OscilloscopeUI()
        self.ui.setWindowTitle(f"SCODIN - ADALM2000 Pro Station [v{self.VERSION}]")
        self.controller = M2kController()
        self.sample_rate = self.controller.sample_rate
        
        self.is_running = True
        
        # --- Data Logger State ---
        self.log_file = None
        self.csv_writer = None
        self.is_logging = False
        self.last_log_time = 0
        self.log_interval = 0.1 # 10Hz par défaut
        self.total_time = 60.0 # 60 secondes max
        self.buffer_size = int(self.sample_rate * self.total_time)
        self.y_history_ch1 = np.zeros(self.buffer_size, dtype=np.float32) # float32 pour l'économie de RAM
        self.y_history_ch2 = np.zeros(self.buffer_size, dtype=np.float32)
        self.ptr = 0 # Pointeur du buffer circulaire
        self.frame_count = 0 
        
        # Calibration matérielle
        self.auto_zero_ch1 = 0.0
        self.auto_zero_ch2 = 0.0
        
        # Pre-allocation de l'onde globale
        self.t_master = np.linspace(0, self.total_time, self.buffer_size, endpoint=False)
        self.y_ideal_master = np.zeros(self.buffer_size, dtype=np.float32)
        
        self.zoom_time = self.ui.spin_time.value()
        self.zoom_samples = int(self.sample_rate * self.zoom_time)
        
        # --- Qualité de rendu (downsample) ---
        self._quality_map = {1: 10000, 2: 50000, 3: 200000, 4: 500000, 5: 1000000}
        self._max_render_points = self._quality_map[3]
        
        # --- FPS Counter ---
        self._fps_timer = 0
        self._fps_frame_count = 0
        self._last_fps_time = time.time()
        
        self.update_pens() # Init des pinceaux

        # --- IA Signal Generator ---
        self.ai_generator = AISignalGenerator()
        self.ai_current_signal = None  # Signal numpy en prévisualisation
        self._load_ai_api_key()  # Charger la clé API depuis config.json

        from PyQt6.QtCore import QTimer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(33) # ~30 FPS
        
        # Connexions UI
        self.ui.btn_run_stop.clicked.connect(self.toggle_run)
        self.ui.chk_auto_y.stateChanged.connect(self.update_y_range)
        self.ui.spin_bpm.valueChanged.connect(self.change_bpm)
        self.ui.btn_auto_zero.clicked.connect(self.run_auto_zero)
        
        # Connexions Exportation
        self.ui.btn_color_bg.clicked.connect(self.choose_bg_color)
        self.ui.btn_color_line.clicked.connect(self.choose_line_color)
        self.ui.btn_export.clicked.connect(self.export_graph)
        self.ui.btn_export_csv.clicked.connect(self.export_snapshot_csv)
        self.ui.btn_reconnect.clicked.connect(lambda: self.attempt_connection(silent=False))
        self.ui.btn_apply_w1.clicked.connect(lambda: self.apply_custom_signal(0))
        self.ui.btn_apply_w2.clicked.connect(lambda: self.apply_custom_signal(1))
        self.ui.btn_browse_log.clicked.connect(self.browse_log_file)
        self.ui.btn_start_log.clicked.connect(self.start_logging)
        self.ui.btn_stop_log.clicked.connect(self.stop_logging)
        self.ui.btn_autoset.clicked.connect(self.run_autoset)
        self.ui.btn_load_ref.clicked.connect(self.load_reference_file)
        self.ui.btn_clear_xy.clicked.connect(lambda: self.ui.curve_xy.setData([], []))
        self.ui.btn_run_ohm.clicked.connect(self.toggle_ohmmeter)
        self.ui.combo_ohm_range.currentIndexChanged.connect(self.update_ohmmeter_instructions)
        
        # Connexions Analyse Graphe
        self.ui.action_v_cursors.triggered.connect(self.toggle_v_cursors)
        self.ui.action_h_cursors.triggered.connect(self.toggle_h_cursors)
        self.ui.action_roi_fft.triggered.connect(self.toggle_roi_fft)
        
        # Connexions IA
        self.ui.btn_ai_send.clicked.connect(self.on_ai_send)
        self.ui.txt_ai_input.returnPressed.connect(self.on_ai_send)
        self.ui.btn_ai_clear.clicked.connect(self.on_ai_clear)
        self.ui.btn_ai_apply_w1.clicked.connect(lambda: self.on_ai_apply(0))
        self.ui.btn_ai_apply_w2.clicked.connect(lambda: self.on_ai_apply(1))
        self.ui.txt_api_key.editingFinished.connect(self.on_ai_api_key_changed)
        self.ui.spin_ai_preview_scale.valueChanged.connect(self.update_ai_preview_scale)
        
        # Signaux de mouvement des curseurs
        self.ui.v_cursor1.sigPositionChanged.connect(self.update_cursors_measure)
        self.ui.v_cursor2.sigPositionChanged.connect(self.update_cursors_measure)
        self.ui.h_cursor1.sigPositionChanged.connect(self.update_cursors_measure)
        self.ui.h_cursor2.sigPositionChanged.connect(self.update_cursors_measure)

        # Connexions Échelles et Visualisation
        self.ui.spin_time.valueChanged.connect(self.change_timebase)
        self.ui.spin_v_div_ch1.valueChanged.connect(self.update_y_range)
        self.ui.spin_v_div_ch2.valueChanged.connect(self.update_y_range)
        self.ui.spin_offset_ch1.valueChanged.connect(lambda: self.update_plot())
        self.ui.spin_offset_ch2.valueChanged.connect(lambda: self.update_plot())
        self.ui.spin_h_pos.valueChanged.connect(lambda: self.update_plot())
        self.ui.spin_thick_ch1.valueChanged.connect(self.update_pens)
        self.ui.spin_thick_ch2.valueChanged.connect(self.update_pens)
        
        # Connexions Navigation Graphe
        self.ui.btn_recenter.clicked.connect(self.recenter_view)
        self.ui.slider_quality.valueChanged.connect(self.on_quality_changed)
        # Détecter le pan/zoom manuel de l'utilisateur sur le graphique
        self.ui.plot_widget.sigRangeChanged.connect(self._on_user_range_changed)
        self._ignore_range_signal = False  # Pour éviter les boucles
        
        # Initialisation du signal idéal
        self.update_ideal_signal(self.ui.spin_bpm.value())
        
        # Démarrage du délai de 5s et tentative de connexion matérielle
        self.run_splash_loop(splash)
        
        # Vérification des mises à jour (en arrière-plan)
        threading.Thread(target=self.check_for_updates, daemon=True).start()
        
    def run_splash_loop(self, splash):
        steps = 100
        for i in range(steps):
            val = i + 1
            self.splash_progress.setValue(val)
            
            if val == 10: splash.showMessage(f"\n\n\nADALM2000 Laboratory (v{self.VERSION})\nInitialisation du contrôleur USB...", Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, Qt.GlobalColor.white)
            if val == 40: splash.showMessage(f"\n\n\nADALM2000 Laboratory (v{self.VERSION})\nTentative de communication matérielle...", Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, Qt.GlobalColor.white)
            if val == 70: splash.showMessage(f"\n\n\nADALM2000 Laboratory (v{self.VERSION})\nAnalyseur de Spectre & FFT...", Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, Qt.GlobalColor.white)
            if val == 90: splash.showMessage(f"\n\n\nADALM2000 Laboratory (v{self.VERSION})\nDémarrage de l'interface graphique...", Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, Qt.GlobalColor.white)
            
            # Au milieu de la barre, on essaie vraiment la connexion
            if val == 50:
                self.attempt_connection(silent=True)
                
            self.app.processEvents()
            time.sleep(5.0 / steps)
            
        self.ui.show()
        splash.finish(self.ui)

    def run(self):
        """Lance la boucle principale de l'application."""
        sys.exit(self.app.exec())

    def apply_custom_signal(self, channel):
        if channel == 0:
            wave_idx = self.ui.combo_w1_type.currentIndex()
            freq = self.ui.spin_w1_freq.value()
            amp = self.ui.spin_w1_amp.value()
        else:
            wave_idx = self.ui.combo_w2_type.currentIndex()
            freq = self.ui.spin_w2_freq.value()
            amp = self.ui.spin_w2_amp.value()
            
        offs = 0.0
        duty = 50.0
        self.controller.generate_custom_waveform(channel, wave_idx, freq, amp, offs, duty)

    def toggle_v_cursors(self, state):
        if state:
            self.ui.plot_widget.addItem(self.ui.v_cursor1)
            self.ui.plot_widget.addItem(self.ui.v_cursor2)
            self.ui.plot_widget.addItem(self.ui.measure_label)
        else:
            self.ui.plot_widget.removeItem(self.ui.v_cursor1)
            self.ui.plot_widget.removeItem(self.ui.v_cursor2)
            if not self.ui.action_h_cursors.isChecked():
                self.ui.plot_widget.removeItem(self.ui.measure_label)
        self.update_cursors_measure()

    def toggle_h_cursors(self, state):
        if state:
            self.ui.plot_widget.addItem(self.ui.h_cursor1)
            self.ui.plot_widget.addItem(self.ui.h_cursor2)
            self.ui.plot_widget.addItem(self.ui.measure_label)
        else:
            self.ui.plot_widget.removeItem(self.ui.h_cursor1)
            self.ui.plot_widget.removeItem(self.ui.h_cursor2)
            if not self.ui.action_v_cursors.isChecked():
                self.ui.plot_widget.removeItem(self.ui.measure_label)
        self.update_cursors_measure()

    def toggle_roi_fft(self, state):
        if state:
            self.ui.plot_widget.addItem(self.ui.roi_fft)
            self.ui.navigate_to(self.ui.tab_spectrum) # Naviguer vers Spectre FFT
        else:
            self.ui.plot_widget.removeItem(self.ui.roi_fft)

    def update_cursors_measure(self):
        text = ""
        if self.ui.action_v_cursors.isChecked():
            t1 = self.ui.v_cursor1.value()
            t2 = self.ui.v_cursor2.value()
            dt = abs(t2 - t1)
            freq = 1.0 / dt if dt > 0 else 0
            text += f"ΔT: {dt*1000:.2f} ms\nFreq: {freq/1000:.2f} kHz\n"
        if self.ui.action_h_cursors.isChecked():
            v1 = self.ui.h_cursor1.value()
            v2 = self.ui.h_cursor2.value()
            dv = abs(v2 - v1)
            text += f"ΔV: {dv:.3f} V"
        self.ui.measure_label.setText(text)
        vb = self.ui.plot_widget.getViewBox()
        range_x = vb.viewRange()[0]
        range_y = vb.viewRange()[1]
        # Position du label en haut à gauche de la vue
        self.ui.measure_label.setPos(range_x[0] + (range_x[1]-range_x[0])*0.05, range_y[1] * 0.9)

    def attempt_connection(self, silent=True):
        if not silent:
            self.ui.lbl_status.setText("Statut : Recherche en cours...")
            self.ui.lbl_status.setStyleSheet("color: orange; font-weight: bold; font-size: 14px;")
            self.app.processEvents()
            
        try:
            self.controller.disconnect_device() # Cleanup au cas où on reconnecte à chaud
            self.controller.connect_device()
            self.controller.generate_base_signal(self.ui.spin_bpm.value())
            self.controller.start_acquisition(self.on_new_data)
            
            self.ui.lbl_status.setText("Statut : Connecté (En ligne)")
            self.ui.lbl_status.setStyleSheet("color: #5cb85c; font-weight: bold; font-size: 14px;")
            print("Connexion réussie !")
        except Exception as e:
            msg = str(e) if silent else f"Échec: {e}"
            print(f"Avertissement de connexion : {msg}")
            self.ui.lbl_status.setText("Statut : Déconnecté (Hors ligne)")
            self.ui.lbl_status.setStyleSheet("color: #d9534f; font-weight: bold; font-size: 14px;")
            
    def load_icon_path(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    raw_path = config.get("icon_path", "")
                    if raw_path:
                        # Resolve relative paths from the script's directory
                        return os.path.normpath(os.path.join(self._script_dir, raw_path))
        except:
            pass
        return ""

            
    def change_bpm(self, bpm):
        self.update_ideal_signal(bpm)
        self.controller.generate_base_signal(bpm)
        
    def update_ideal_signal(self, bpm):
        self.y_ideal_master.fill(0)
        period_s = 60.0 / bpm
        samples_period = int(self.sample_rate * period_s)
        idx_on = int(samples_period * 0.65)
        
        # Construction d'un motif complet
        t_pattern = np.linspace(0, period_s, samples_period, endpoint=False)
        pattern = np.zeros(samples_period, dtype=np.float32)
        pattern[:idx_on] = 0.03 * np.sin(2 * np.pi * 40000 * t_pattern[:idx_on])
        
        # Remplissage de l'historique complet pour affichage de la courbe idéale
        num_periods = int(np.ceil(self.buffer_size / samples_period))
        for i in range(num_periods):
            start = i * samples_period
            end = start + samples_period
            if end > self.buffer_size:
                self.y_ideal_master[start:self.buffer_size] = pattern[:self.buffer_size - start]
            else:
                self.y_ideal_master[start:end] = pattern

    def change_timebase(self, value):
        self.zoom_time = value
        self.zoom_samples = int(self.sample_rate * self.zoom_time)
        self.zoom_samples = min(self.zoom_samples, self.buffer_size)
        
        # Recentrer automatiquement le graphe quand on change l'échelle via le panneau
        self.ui._user_panned = False
        self.ui.btn_recenter.hide()
        self._apply_auto_range()
        self.update_plot()
    
    def _apply_auto_range(self):
        """Applique le cadrage automatique du graphe (X et Y)."""
        self._ignore_range_signal = True
        self.ui.plot_widget.setXRange(0, self.zoom_time, padding=0)
        self.update_y_range()
        self._ignore_range_signal = False
    
    def _on_user_range_changed(self):
        """Détecté quand l'utilisateur pan/zoom manuellement sur le graphique."""
        if self._ignore_range_signal:
            return
        if not self.ui._user_panned:
            self.ui._user_panned = True
            self.ui.btn_recenter.show()
    
    def recenter_view(self):
        """Remet la vue centrée et ajustée automatiquement."""
        self.ui._user_panned = False
        self.ui.btn_recenter.hide()
        self._apply_auto_range()
    
    def on_quality_changed(self, value):
        """Met à jour le nombre max de points de rendu selon le slider."""
        self._max_render_points = self._quality_map.get(value, 200000)
        labels = {1: "1 (Perf++)", 2: "2 (Rapide)", 3: "3 (Normal)", 4: "4 (Détail)", 5: "5 (Max)"}
        self.ui.lbl_quality_val.setText(labels.get(value, str(value)))

    def update_y_range(self):
        if not self.ui.chk_auto_y.isChecked():
            v1 = self.ui.spin_v_div_ch1.value() * 4 # 8 divisions totales (approx)
            v2 = self.ui.spin_v_div_ch2.value() * 4
            v_max = max(v1, v2)
            self._ignore_range_signal = True
            self.ui.plot_widget.setYRange(-v_max, v_max)
            self._ignore_range_signal = False
            # Recentrer si on change via le panneau
            if not self.ui._user_panned:
                self.ui.btn_recenter.hide()

    def change_voltage(self, value):
        # Cette méthode est gardée pour compatibilité si appelée ailleurs
        self.update_y_range()

    def update_pens(self):
        w1 = self.ui.spin_thick_ch1.value()
        w2 = self.ui.spin_thick_ch2.value()
        self.ui.curve.setPen(pg.mkPen('#1f77b4', width=w1))
        self.ui.curve_ch2.setPen(pg.mkPen('#ff7f0e', width=w2))

    def run_auto_zero(self):
        """Calibrage automatique du 0V pour compenser le DC Offset de l'ADALM2000"""
        lookback = int(self.sample_rate * 0.1) # 100ms de données pour moyenner
        ch1, ch2 = self.get_latest_data(lookback)
        if len(ch1) > 0 and len(ch2) > 0:
            self.auto_zero_ch1 = -float(np.mean(ch1))
            self.auto_zero_ch2 = -float(np.mean(ch2))
            print(f"Auto-Zero appliqué: CH1={self.auto_zero_ch1:.4f}V, CH2={self.auto_zero_ch2:.4f}V")
            self.ui.lbl_status.setText(f"Statut : Zéro Calibré (C1={self.auto_zero_ch1*1000:.0f}mV, C2={self.auto_zero_ch2*1000:.0f}mV)")
            self.ui.lbl_status.setStyleSheet("color: #5bc0de; font-weight: bold; font-size: 14px;")

    def run_autoset(self):
        """Algorithme d'ajustement automatique des échelles"""
        lookback = int(self.sample_rate * 0.1) # 100ms de données
        ch1, ch2 = self.get_latest_data(lookback)
        
        # Canal 1
        if self.ui.chk_ch1.isChecked():
            vpp1 = np.ptp(ch1)
            if vpp1 > 0.05:
                vdiv = vpp1 / 4.0
                self.ui.spin_v_div_ch1.setValue(vdiv)
                self.ui.spin_offset_ch1.setValue(-np.mean(ch1))
                
                # Temps : estimer la fréquence
                zero_cross = np.where(np.diff(np.sign(ch1 - np.mean(ch1))))[0]
                if len(zero_cross) > 2:
                    period = 2 * (zero_cross[-1] - zero_cross[0]) / (len(zero_cross) - 1)
                    freq = self.sample_rate / period
                    # On veut voir ~2-4 périodes
                    new_time = 4.0 / freq if freq > 0 else 0.5
                    self.ui.spin_time.setValue(min(1.0, max(0.0002, new_time)))

        self.ui.chk_auto_y.setChecked(False)
        self.update_y_range()

    def load_reference_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self.ui, "Charger Référence", "", "CSV Files (*.csv)")
        if file_path:
            try:
                data = np.genfromtxt(file_path, delimiter=',', skip_header=1)
                if data.ndim == 2 and data.shape[1] >= 2:
                    # On suppose Col 0 = Temps, Col 1 = Tension
                    self.ui.curve_ref.setData(data[:, 0], data[:, 1])
                    self.ui.curve_ref.setVisible(True)
            except Exception as e:
                print(f"Erreur chargement réf: {e}")

    def export_snapshot_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(self.ui, "Exporter Snapshot", "snapshot.csv", "CSV Files (*.csv)")
        if file_path:
            # Récupérer les données affichées actuellement
            lookback = self.zoom_samples
            ch1, ch2 = self.get_latest_data(lookback)
            t = np.linspace(0, self.zoom_time, len(ch1), endpoint=False)
            
            try:
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Time", "CH1", "CH2"])
                    for i in range(len(t)):
                        writer.writerow([f"{t[i]:.6f}", f"{ch1[i]:.4f}", f"{ch2[i]:.4f}"])
                print(f"Snapshot exporté: {file_path}")
            except Exception as e:
                print(f"Erreur export CSV: {e}")

    def toggle_run(self, checked):
        if checked:
            self.is_running = False
            self.ui.btn_run_stop.setText("En Pause (Cliquer pour Reprendre)")
            self.ui.btn_run_stop.setStyleSheet("background-color: #d9534f; color: white; font-weight: bold; padding: 10px;")
        else:
            self.is_running = True
            self.ui.btn_run_stop.setText("En cours (Cliquer pour mettre en Pause)")
            self.ui.btn_run_stop.setStyleSheet("background-color: #5cb85c; color: white; font-weight: bold; padding: 10px;")

    def on_new_data(self, new_data):
        if not self.is_running:
            return

        # Écriture instantanée dans le buffer O(1)
        y_ch1, y_ch2 = new_data
        n = len(y_ch1)
        if n == 0:
            return
            
        end_ptr = self.ptr + n
        if end_ptr <= self.buffer_size:
            self.y_history_ch1[self.ptr:end_ptr] = y_ch1
            self.y_history_ch2[self.ptr:end_ptr] = y_ch2
        else:
            overflow = end_ptr - self.buffer_size
            self.y_history_ch1[self.ptr:] = y_ch1[:-overflow]
            self.y_history_ch1[:overflow] = y_ch1[-overflow:]
            
            self.y_history_ch2[self.ptr:] = y_ch2[:-overflow]
            self.y_history_ch2[:overflow] = y_ch2[-overflow:]
            
        self.ptr = (self.ptr + n) % self.buffer_size
        # ATTENTION: On ne déclenche plus update_plot ici pour éviter le freeze.

    def get_latest_data(self, nb_samples):
        if self.ptr >= nb_samples:
            return (self.y_history_ch1[self.ptr - nb_samples : self.ptr],
                    self.y_history_ch2[self.ptr - nb_samples : self.ptr])
        else:
            p1 = self.buffer_size - (nb_samples - self.ptr)
            return (np.concatenate((self.y_history_ch1[p1:], self.y_history_ch1[:self.ptr])),
                    np.concatenate((self.y_history_ch2[p1:], self.y_history_ch2[:self.ptr])))

    def fast_downsample(self, y_arr, max_points=None):
        """Downsampling adapté au slider qualité et à l'échelle visible."""
        if max_points is None:
            max_points = self._max_render_points
        
        if len(y_arr) <= max_points:
            return y_arr
            
        factor = len(y_arr) // (max_points // 2)
        length = (len(y_arr) // factor) * factor
        y_view = y_arr[:length].reshape(-1, factor)
        
        y_min = y_view.min(axis=1)
        y_max = y_view.max(axis=1)
        
        env = np.empty(y_min.size * 2, dtype=y_arr.dtype)
        env[0::2] = y_min
        env[1::2] = y_max
        return env

    def update_plot(self):
        if not self.is_running:
            return
        
        # --- Compteur FPS ---
        self._fps_frame_count += 1
        now = time.time()
        elapsed = now - self._last_fps_time
        if elapsed >= 1.0:
            fps = self._fps_frame_count / elapsed
            self.ui.lbl_fps.setText(f"{fps:.0f} FPS")
            self._fps_frame_count = 0
            self._last_fps_time = now
            
        # Pousser la vue
        lookback_samples = min(self.buffer_size, self.zoom_samples + int(self.sample_rate * 0.1))
        recent_ch1, recent_ch2 = self.get_latest_data(lookback_samples)
        
        start_idx = len(recent_ch1) - self.zoom_samples
        
        self.frame_count += 1
        
        # Trigger avec Hystérésis Vectorisé (beaucoup plus rapide !)
        if self.ui.btn_enable_trigger.isChecked() and self.zoom_time < 0.1:
            threshold = self.ui.spin_trig_level.value()
            hyst = self.ui.spin_hysteresis.value()
            low_thresh = threshold - hyst
            
            # Recherche ultra-rapide avec NumPy
            # On cherche i tel que recent_ch1[i-1] < low_thresh et recent_ch1[i] >= threshold
            condition = (recent_ch1[:-1] < low_thresh) & (recent_ch1[1:] >= threshold)
            indices = np.where(condition)[0]
            
            if indices.size > 0:
                # On prend le premier front montant trouvé
                start_idx = indices[0] + 1
        
        # Application du décalage horizontal (Horizontal Position)
        h_offset_samples = int(self.ui.spin_h_pos.value() * self.sample_rate)
        start_idx = max(0, min(len(recent_ch1) - self.zoom_samples, start_idx + h_offset_samples))

        # Application des Offsets et Gains (Sondes)
        probe1 = [1, 10, 100][self.ui.combo_probe_ch1.currentIndex()]
        probe2 = [1, 10, 100][self.ui.combo_probe_ch2.currentIndex()]
        
        raw_display_ch1 = (recent_ch1[start_idx : start_idx + self.zoom_samples] + self.auto_zero_ch1) * probe1
        raw_display_ch2 = (recent_ch2[start_idx : start_idx + self.zoom_samples] + self.auto_zero_ch2) * probe2

        # Couplage AC Logiciel
        if self.ui.chk_ac_ch1.isChecked():
            raw_display_ch1 = raw_display_ch1 - np.mean(raw_display_ch1)
        if self.ui.chk_ac_ch2.isChecked():
            raw_display_ch2 = raw_display_ch2 - np.mean(raw_display_ch2)

        y_display_ch1 = raw_display_ch1 + self.ui.spin_offset_ch1.value()
        y_display_ch2 = raw_display_ch2 + self.ui.spin_offset_ch2.value()
        
        if self.ui.chk_ch1.isChecked():
            y_display_opt_ch1 = self.fast_downsample(y_display_ch1)
            t_display_opt_1 = np.linspace(0, self.zoom_time, len(y_display_opt_ch1), endpoint=False)
            self.ui.curve.setData(t_display_opt_1, y_display_opt_ch1)
            
        if self.ui.chk_ch2.isChecked():
            y_display_opt_ch2 = self.fast_downsample(y_display_ch2)
            t_display_opt_2 = np.linspace(0, self.zoom_time, len(y_display_opt_ch2), endpoint=False)
            self.ui.curve_ch2.setData(t_display_opt_2, y_display_opt_ch2)
        
        # --- Auto-fit si pas en mode navigation libre ---
        if not self.ui._user_panned:
            self._ignore_range_signal = True
            self.ui.plot_widget.setXRange(0, self.zoom_time, padding=0)
            self._ignore_range_signal = False
        
        # Mise à jour de l'analyseur de spectre (Toutes les 10 frames si onglet actif)
        if self.ui.get_active_page() is self.ui.tab_spectrum: # Onglet Spectre
            if self.frame_count % 10 == 0:
                if self.ui.action_roi_fft.isChecked():
                    region = self.ui.roi_fft.getRegion()
                    t_start, t_end = region
                    idx_start = int((t_start / self.zoom_time) * len(y_display_ch1))
                    idx_end = int((t_end / self.zoom_time) * len(y_display_ch1))
                    idx_start = max(0, min(len(y_display_ch1)-10, idx_start))
                    idx_end = max(idx_start+10, min(len(y_display_ch1), idx_end))
                    self.update_spectrum(y_display_ch1[idx_start:idx_end], y_display_ch2[idx_start:idx_end])
                else:
                    self.update_spectrum(y_display_ch1, y_display_ch2)
        
        # Mise à jour du Voltmètre (Toutes les 6 frames si onglet actif)
        if self.ui.get_active_page() is self.ui.tab_voltmeter: # Onglet Voltmeter
            if self.frame_count % 6 == 0:
                self.update_voltmeter(y_display_ch1, y_display_ch2)
        
        # Mise à jour du Multimètre (Toutes les 6 frames si onglet actif)
        if self.ui.get_active_page() is self.ui.tab_multimeter: # Onglet Multimètre
            if self.frame_count % 6 == 0:
                self.update_multimeter(y_display_ch1)
        
        # Mise à jour de la Vue XY
        if self.ui.get_active_page() is self.ui.tab_xy: # Onglet XY
            # On prend moins de points pour la vue XY pour éviter les lags (ex: 2000 points max)
            skip = max(1, len(y_display_ch1) // 2000)
            self.ui.curve_xy.setData(y_display_ch1[::skip], y_display_ch2[::skip])

        # Mise à jour des Math (Uniquement si onglet spécifique actif ou visibles sur le plot principal)
        if self.ui.get_active_page() is self.ui.tab_math: # Onglet Math
            if self.ui.chk_math_enabled.isChecked():
                op = self.ui.combo_math_op.currentIndex()
                if op == 0: math_data = y_display_ch1 + y_display_ch2
                elif op == 1: math_data = y_display_ch1 - y_display_ch2
                elif op == 2: math_data = y_display_ch1 * y_display_ch2
                elif op == 3: math_data = y_display_ch1 / (y_display_ch2 + 1e-9)
                
                t_math = np.linspace(0, self.zoom_time, len(math_data), endpoint=False)
                self.ui.curve_math.setData(t_math, math_data)
        elif self.ui.chk_math_enabled.isChecked():
             # Optionnel : On peut aussi calculer si déjà visible même sur l'onglet Oscilloscope
             pass
        
        # Enregistrement de données si actif
        if self.is_logging:
            self.process_logging(y_display_ch1, y_display_ch2)

        # Générateur idéal
        if self.ui.chk_show_ideal.isChecked():
            # Signal idéal basé sur CH1 uniquement pour l'instant
            ideal_display = self.y_ideal_master[start_idx : start_idx + self.zoom_samples]
            ideal_display_opt = self.fast_downsample(ideal_display)
            t_display_opt_ideal = np.linspace(0, self.zoom_time, len(ideal_display_opt), endpoint=False)
            self.ui.curve_ideal.setData(t_display_opt_ideal, ideal_display_opt)

    def update_voltmeter(self, ch1, ch2):
        # On ne vérifie pas l'index ici car déjà fait dans update_plot
            
        def get_stats(data):
            if len(data) < 2: return 0, 0, 0, 0
            dc = np.mean(data)
            rms = np.sqrt(np.mean(data**2))
            vpp = np.ptp(data)
            
            # Filtre Anti-Bruit (Squelch)
            if self.ui.chk_squelch.isChecked():
                # Si le Vpp est petit (< 120mV) ça indique du bruit plutôt qu'un vrai signal.
                # On masque ce bruit parasite quand les broches sont flottantes.
                if vpp < 0.12 and abs(dc) < 0.05:
                    return 0.0, 0.0, 0.0, 0
            
            # Estimation fréquence simple (passages par zéro)
            zero_crossings = np.where(np.diff(np.sign(data - dc)))[0]
            if len(zero_crossings) > 2:
                period = 2 * (zero_crossings[-1] - zero_crossings[0]) / (len(zero_crossings) - 1)
                freq = self.sample_rate / period
            else:
                freq = 0
            return dc, rms, vpp, freq

        d1, r1, p1, f1 = get_stats(ch1)
        self.ui.lbl_ch1_dc.setText(f"DC: {d1:.3f} V")
        self.ui.lbl_ch1_rms.setText(f"RMS: {r1:.3f} V")
        self.ui.lbl_ch1_vpp.setText(f"Vpp: {p1:.3f} V")
        self.ui.lbl_ch1_freq.setText(f"FREQ: {int(f1)} Hz")

        d2, r2, p2, f2 = get_stats(ch2)
        self.ui.lbl_ch2_dc.setText(f"DC: {d2:.3f} V")
        self.ui.lbl_ch2_rms.setText(f"RMS: {r2:.3f} V")
        self.ui.lbl_ch2_vpp.setText(f"Vpp: {p2:.3f} V")
        self.ui.lbl_ch2_freq.setText(f"FREQ: {int(f2)} Hz")

    def toggle_ohmmeter(self, checked):
        if checked:
            # Activer W1 à 1.0V DC pour la mesure
            self.controller.generate_custom_waveform(0, 0, 1000, 0, 1.0) # Type 0 (Sin), Amp 0, Offset 1.0 = DC
            self.ui.btn_run_ohm.setText("Ohmmètre ACTIF (Cliquer pour Arrêter)")
            self.ui.btn_run_ohm.setStyleSheet("background-color: #5cb85c; color: white; font-weight: bold; padding: 10px;")
        else:
            # Désactiver W1 (ou remettre signal de base)
            self.controller.generate_base_signal(self.ui.spin_bpm.value())
            self.ui.btn_run_ohm.setText("Démarrer l'Ohmmètre")
            self.ui.btn_run_ohm.setStyleSheet("background-color: #333; color: #5bc0de; font-weight: bold; padding: 10px; border: 1px solid #5bc0de;")
            self.ui.lbl_ohm_val.setText("--- Ω")

    def update_multimeter(self, ch1):
        v_dc = np.mean(ch1)
        self.ui.lbl_multi_v.setText(f"{v_dc:.3f} V")
        
        if self.ui.btn_run_ohm.isChecked():
            v_source = 1.0
            
            if self.ui.combo_ohm_range.currentIndex() == 0: # Basse Résistance (Source 50 Ω)
                r_source = 50.0
                denominator = v_source - v_dc
                if denominator < 0.001:
                    res = float('inf')
                else:
                    res = (max(0, v_dc) * r_source) / denominator
            else: # Haute Résistance (Scope Input 1 MΩ)
                r_scope = 1000000.0
                # Rx = R_scope * (V_src / V_mes - 1)
                v_mes = max(0.0001, v_dc)
                res = r_scope * (v_source / v_mes - 1)
            
            if res > 10000000: # 10 MΩ max pour l'affichage
                self.ui.lbl_ohm_val.setText("O.L (Inf)")
                self.ui.lbl_continuity.setText("Continuité : OUVERT")
                self.ui.lbl_continuity.setStyleSheet("color: #d9534f; font-weight: bold;")
            elif res >= 1000000:
                self.ui.lbl_ohm_val.setText(f"{res/1000000:.2f} MΩ")
                self.ui.lbl_continuity.setText("Continuité : OUVERT")
                self.ui.lbl_continuity.setStyleSheet("color: #d9534f; font-weight: bold;")
            elif res >= 1000:
                self.ui.lbl_ohm_val.setText(f"{res/1000:.2f} kΩ")
                self.ui.lbl_continuity.setText("Continuité : OUVERT")
                self.ui.lbl_continuity.setStyleSheet("color: #d9534f; font-weight: bold;")
            else:
                self.ui.lbl_ohm_val.setText(f"{max(0, res):.1f} Ω")
                # Seuil de continuité à 50 ohms
                if res < 50:
                    self.ui.lbl_continuity.setText("Continuité : OK (BIP)")
                    self.ui.lbl_continuity.setStyleSheet("color: #5cb85c; font-weight: bold; background: #1a3a1a;")
                else:
                    self.ui.lbl_continuity.setText("Continuité : OUVERT")
                    self.ui.lbl_continuity.setStyleSheet("color: #d9534f; font-weight: bold;")

    def check_for_updates(self):
        """Vérifie si une nouvelle version est disponible sur le serveur."""
        try:
            # On attend que l'application soit totalement lancée (après le splash screen de 5s)
            time.sleep(7)
            
            # Utilisation d'un User-Agent pour éviter les blocages serveurs
            req = urllib.request.Request(self.UPDATE_URL, headers={'User-Agent': 'Mozilla/5.0'})
            
            # Certains certificats SSL sur des hébergements gratuits peuvent poser problème
            import ssl
            context = ssl._create_unverified_context()
            
            with urllib.request.urlopen(req, timeout=10, context=context) as response:
                raw_data = response.read().decode('utf-8').strip()
                # On ne garde que les chiffres et les points (enlève d'éventuels caractères BOM ou cachés)
                online_version = "".join(c for c in raw_data if c.isdigit() or c == '.')
                
                print(f"DEBUG MAJ : Locale='{self.VERSION}', Serveur='{online_version}'")
                
                # Comparaison numérique (ex: [1, 3, 1] > [1, 3, 0])
                try:
                    v_online = [int(x) for x in online_version.split('.') if x]
                    v_local = [int(x) for x in self.VERSION.split('.') if x]
                    
                    if v_online > v_local:
                        print("MAJ : Nouvelle version détectée sur le serveur !")
                        # Appel thread-safe via invokeMethod sur soi-même (maintenant que c'est un QObject)
                        QMetaObject.invokeMethod(self, "show_update_popup", 
                                               Qt.ConnectionType.QueuedConnection,
                                               Q_ARG(str, online_version))
                    else:
                        print("MAJ : Le logiciel est à jour.")
                except Exception as ve:
                    print(f"Erreur format version: {ve} (Data raw: '{raw_data}')")
                    
        except Exception as e:
            print(f"Update check failed: {e}")

    @pyqtSlot(str)
    def show_update_popup(self, new_version):
        """Affiche la boîte de dialogue de mise à jour."""
        msg = QMessageBox(self.ui)
        msg.setWindowTitle("✨ Mise à jour disponible")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(f"<h3>Une nouvelle version est disponible !</h3>")
        msg.setInformativeText(
            f"Version actuelle : <b>{self.VERSION}</b><br>"
            f"Nouvelle version : <b style='color: #5cb85c;'>{new_version}</b><br><br>"
            "Voulez-vous télécharger la mise à jour maintenant ?"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        
        # Style de la popup pour coller à l'UI
        msg.setStyleSheet("""
            QMessageBox { background-color: #121212; color: white; }
            QLabel { color: #e0e0e0; }
            QPushButton { background-color: #333; color: white; padding: 6px 15px; border-radius: 4px; }
            QPushButton:hover { background-color: #444; }
        """)

        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.start_automated_update()

    def start_automated_update(self):
        """Lance le processus de téléchargement et d'installation automatique."""
        self.progress = QProgressBar()
        self.progress_dialog = QDialog(self.ui)
        self.progress_dialog.setWindowTitle("Installation de la mise à jour")
        self.progress_dialog.setFixedWidth(400)
        
        layout = QVBoxLayout(self.progress_dialog)
        layout.addWidget(QLabel("Téléchargement de la nouvelle version en cours..."))
        self.progress_label = QLabel("0%")
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress)
        
        self.progress_dialog.show()
        
        # Thread pour le téléchargement
        threading.Thread(target=self._download_update_thread, daemon=True).start()

    def _download_update_thread(self):
        try:
            temp_dir = tempfile.gettempdir()
            zip_path = os.path.join(temp_dir, "ADALM2000_update.zip")
            
            import ssl
            context = ssl._create_unverified_context()
            
            req = urllib.request.Request(self.DOWNLOAD_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=context) as response:
                total_size = int(response.info().get('Content-Length', 0))
                downloaded = 0
                block_size = 8192
                
                with open(zip_path, 'wb') as f:
                    while True:
                        buffer = response.read(block_size)
                        if not buffer:
                            break
                        downloaded += len(buffer)
                        f.write(buffer)
                        
                        if total_size > 0:
                            percent = int(downloaded * 100 / total_size)
                            QMetaObject.invokeMethod(self, "_update_download_progress",
                                                   Qt.ConnectionType.QueuedConnection,
                                                   Q_ARG(int, percent))
            
            QMetaObject.invokeMethod(self, "_finalize_update",
                                   Qt.ConnectionType.QueuedConnection,
                                   Q_ARG(str, zip_path))
        except Exception as e:
            print(f"Erreur téléchargement : {e}")
            QMetaObject.invokeMethod(self, "_on_update_error",
                                   Qt.ConnectionType.QueuedConnection,
                                   Q_ARG(str, str(e)))

    @pyqtSlot(int)
    def _update_download_progress(self, percent):
        if hasattr(self, 'progress'):
            self.progress.setValue(min(percent, 100))
            self.progress_label.setText(f"{percent}%")

    @pyqtSlot(str)
    def _on_update_error(self, error_msg):
        self.progress_dialog.close()
        QMessageBox.critical(self.ui, "Erreur de mise à jour", f"Le téléchargement a échoué :\n{error_msg}")

    @pyqtSlot(str)
    def _finalize_update(self, zip_path):
        """Extrait la mise à jour et lance le script de remplacement."""
        try:
            self.progress_label.setText("Extraction et préparation...")
            self.progress.setRange(0, 0) # Mode indéterminé
            
            app_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
            extract_dir = os.path.join(tempfile.gettempdir(), "ADALM2000_extracted")
            
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            os.makedirs(extract_dir)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Déterminer le nom de l'exécutable
            exe_name = os.path.basename(sys.executable)
            
            # Créer un script batch pour effectuer le remplacement après la fermeture
            batch_path = os.path.join(tempfile.gettempdir(), "update_script.bat")
            
            # Script batch intelligent : 
            # 1. Attend que l'app se ferme
            # 2. Copie les fichiers (en gérant les sous-dossiers si présents dans le zip)
            # 3. Relance l'app
            # 4. S'auto-supprime
            
            # On vérifie si le zip contient un dossier racine (souvent le cas)
            source_path = extract_dir
            contents = os.listdir(extract_dir)
            if len(contents) == 1 and os.path.isdir(os.path.join(extract_dir, contents[0])):
                source_path = os.path.join(extract_dir, contents[0])

            with open(batch_path, "w", encoding="cp1252") as f:
                f.write("@echo off\n")
                f.write("echo Mise a jour en cours, veuillez patienter...\n")
                f.write("timeout /t 2 /nobreak > nul\n")
                # /S /E /Y /I pour copier récursivement et écraser
                f.write(f'xcopy /s /e /y /i "{source_path}\\*" "{app_dir}\\"\n')
                f.write(f'start "" "{os.path.join(app_dir, exe_name)}"\n')
                f.write(f'del "{batch_path}"\n')
            
            # Lancer le batch et quitter
            subprocess.Popen(["cmd.exe", "/c", batch_path], shell=True)
            self.app.quit()
            
        except Exception as e:
            self._on_update_error(str(e))

    def update_ohmmeter_instructions(self, index):
        # On ne change pas le texte ici pour éviter de tout réécrire, 
        # mais on pourrait mettre en gras la partie active
        pass

    def browse_log_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self.ui, "Enregistrer les données", "mesures_adalm.csv", "CSV Files (*.csv)")
        if file_path:
            self.ui.txt_log_path.setText(file_path)

    def start_logging(self):
        path = self.ui.txt_log_path.text()
        if path == "Aucun fichier sélectionné":
            return
            
        try:
            self.log_file = open(path, 'w', newline='')
            self.csv_writer = csv.writer(self.log_file)
            self.csv_writer.writerow(["Timestamp", "CH1_V", "CH2_V"])
            
            rate_idx = self.ui.combo_log_rate.currentIndex()
            self.log_interval = [0.1, 1.0, 10.0][rate_idx]
            
            self.is_logging = True
            self.ui.btn_start_log.setEnabled(False)
            self.ui.btn_stop_log.setEnabled(True)
            self.ui.lbl_log_status.setText("Statut : ENREGISTREMENT EN COURS...")
            self.ui.lbl_log_status.setStyleSheet("color: #5cb85c; font-weight: bold;")
        except Exception as e:
            print(f"Erreur Logger: {e}")

    def stop_logging(self):
        self.is_logging = False
        if self.log_file:
            self.log_file.close()
            self.log_file = None
        self.ui.btn_start_log.setEnabled(True)
        self.ui.btn_stop_log.setEnabled(False)
        self.ui.lbl_log_status.setText("Statut : Prêt (Enregistrement terminé)")
        self.ui.lbl_log_status.setStyleSheet("color: white; font-weight: bold;")

    def process_logging(self, ch1, ch2):
        now = time.time()
        if now - self.last_log_time >= self.log_interval:
            self.last_log_time = now
            # On log la moyenne sur la fenêtre actuelle pour être stable
            v1 = np.mean(ch1)
            v2 = np.mean(ch2)
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.csv_writer.writerow([ts, f"{v1:.4f}", f"{v2:.4f}"])
            self.log_file.flush() # Force l'écriture sur disque

    def update_spectrum(self, ch1_raw, ch2_raw):
        # On ne calcule que si l'onglet est visible pour économiser du CPU
        if self.ui.get_active_page() is not self.ui.tab_spectrum: # Onglet spectre
            return
            
        # On utilise une fenêtre de données fixe pour la FFT (ex: 8192 points ou zoom actuel)
        # Pour une meilleure résolution, on prend le maximum de points visibles
        n = len(ch1_raw)
        if n < 64: return
        
        # Fenêtrage (Hann) pour réduire les lobes secondaires
        window = np.hanning(n)
        freqs = np.fft.rfftfreq(n, 1/self.sample_rate)
        
        if self.ui.chk_show_spect_ch1.isChecked():
            # FFT CH1
            fft_ch1 = np.fft.rfft((ch1_raw - np.mean(ch1_raw)) * window)
            mag_ch1 = 20 * np.log10(np.abs(fft_ch1) * 2 / np.sum(window) + 1e-9)
            self.ui.curve_spect_ch1.setData(freqs, mag_ch1)
            self.ui.curve_spect_ch1.setVisible(True)
        else:
            self.ui.curve_spect_ch1.setVisible(False)
            
        if self.ui.chk_show_spect_ch2.isChecked():
            # FFT CH2
            fft_ch2 = np.fft.rfft((ch2_raw - np.mean(ch2_raw)) * window)
            mag_ch2 = 20 * np.log10(np.abs(fft_ch2) * 2 / np.sum(window) + 1e-9)
            self.ui.curve_spect_ch2.setData(freqs, mag_ch2)
            self.ui.curve_spect_ch2.setVisible(True)
        else:
            self.ui.curve_spect_ch2.setVisible(False)

    def choose_bg_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.ui.bg_color = color.name()
            # Ajustement texte Noir ou Blanc selon la couleur de fond
            text_col = 'black' if color.lightnessF() > 0.5 else 'white'
            self.ui.btn_color_bg.setStyleSheet(f"background-color: {self.ui.bg_color}; color: {text_col}; border: 1px solid gray;")

    def choose_line_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.ui.line_color = color.name()
            text_col = 'black' if color.lightnessF() > 0.5 else 'white'
            self.ui.btn_color_line.setStyleSheet(f"background-color: {self.ui.line_color}; color: {text_col}; border: 1px solid gray;")

    def export_graph(self):
        if self.is_running:
            QMessageBox.warning(self.ui, "Attention", "Veuillez mettre la simulation en pause avant d'exporter le graphique.")
            return

        # 0. Demander les titres et noms d'axes via une boîte de dialogue
        # Récupérer les labels actuels (en enlevant potentiellement du HTML)
        current_title = "Analyseur de Signaux ADALM2000"
        current_x = "Temps"
        current_y = "Tension"
        
        dialog = ExportSettingsDialog(self.ui, current_title, current_x, current_y)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
            
        settings = dialog.get_values()
        
        # Demander l'emplacement 
        file_path, _ = QFileDialog.getSaveFileName(self.ui, "Exporter le graphique", "capture_oscilloscope.png", "Images PNG (*.png)")
        if not file_path:
            return
            
        # 1. Sauvegarder couleurs et textes actuels
        old_curve_pen = self.ui.curve.opts['pen']
        old_title = self.ui.plot_widget.plotItem.titleLabel.text
        
        # Pour les axes, on récupère texte et unités
        old_labels = {}
        for axis_name in ['left', 'bottom']:
            axis = self.ui.plot_widget.getAxis(axis_name)
            old_labels[axis_name] = (axis.labelText, axis.labelUnits)

        # 2. Appliquer les réglages demandés
        self.ui.plot_widget.setBackground(self.ui.bg_color)
        self.ui.curve.setPen(pg.mkPen(color=self.ui.line_color, width=2))
        
        # Appliquer les nouveaux titres/axes
        self.ui.plot_widget.setTitle(settings['title'])
        self.ui.plot_widget.setLabel('bottom', settings['x_label'], units='s')
        self.ui.plot_widget.setLabel('left', settings['y_label'], units='V')
        
        # Ajustement des axes si le fond choisi est clair 
        orig_axes_pen = {}
        for axis_name in ['left', 'bottom']:
            axis = self.ui.plot_widget.getAxis(axis_name)
            orig_axes_pen[axis_name] = (axis.pen(), axis.textPen())
            
            # On met une grille/texte foncé si bg blanc
            if self.ui.bg_color in ['white', '#ffffff']:
                axis.setPen('k')
                axis.setTextPen('k')
        
        self.app.processEvents() # Forcer le re-rendu visuel PyQt avant l'export
        
        # 3. Exporter l'image !
        try:
            # On exporte directement le plotItem (la vue rectangulaire pure du graphe)
            exporter = pyqtgraph.exporters.ImageExporter(self.ui.plot_widget.plotItem)
            # Paramètres de rendu (Haute résolution)
            exporter.parameters()['width'] = 1920
            exporter.export(file_path)
            print(f"Graphique exporté sur : {file_path}")
        except Exception as e:
            print("Erreur d'exportation :", e)
            
        # 4. Rétablir le thème sombre d'origine et les anciens textes
        self.ui.plot_widget.setBackground('k')
        self.ui.curve.setPen(old_curve_pen)
        self.ui.plot_widget.setTitle(old_title)
        for axis_name, label_info in old_labels.items():
            self.ui.plot_widget.setLabel(axis_name, label_info[0], units=label_info[1])
            
        for axis_name, pens in orig_axes_pen.items():
            axis = self.ui.plot_widget.getAxis(axis_name)
            axis.setPen(pens[0])
            axis.setTextPen(pens[1])


    def run(self):
        self.change_timebase(self.ui.spin_time.value())
        self.update_y_range()
        
        exit_code = self.app.exec()
        
        # Cleanup final
        if self.is_logging:
            self.stop_logging()
            
        self.controller.disconnect_device()
        sys.exit(exit_code)

    # ======================================================================
    # === LOGIQUE ONGLET IA ================================================
    # ======================================================================

    def _load_ai_api_key(self):
        """Charge la clé API depuis config.json et la pré-remplit dans l'interface."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    key = config.get("groq_api_key", "")
                    if key:
                        self.ai_generator.set_api_key(key)
                        self.ui.txt_api_key.setText(key)
        except Exception:
            pass

    def on_ai_api_key_changed(self):
        """Sauvegarde la clé API dans config.json quand l'utilisateur la modifie."""
        key = self.ui.txt_api_key.text().strip()
        self.ai_generator.set_api_key(key)
        
        # Sauvegarder dans config.json
        try:
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config = json.load(f)
            config["groq_api_key"] = key
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde clé API : {e}")

    def on_ai_send(self):
        """Envoie le prompt utilisateur à l'IA et affiche le résultat."""
        prompt = self.ui.txt_ai_input.text().strip()
        if not prompt:
            return
        
        # Afficher le message utilisateur dans le chat
        self._ai_append_chat("user", prompt)
        self.ui.txt_ai_input.clear()
        
        # Désactiver le bouton pendant le traitement
        self.ui.btn_ai_send.setEnabled(False)
        self.ui.btn_ai_send.setText("⏳ Analyse...")
        self.ui.lbl_ai_status.setText("Envoi de la requête à l'IA...")
        self.ui.lbl_ai_status.setStyleSheet("color: #5bc0de; font-style: italic; font-size: 11px; padding: 4px;")
        self.app.processEvents()
        
        # Appel IA (bloquant — dans un thread serait mieux mais simple pour l'instant)
        duration = self.ui.spin_ai_duration.value()
        sample_rate = self.controller.sample_rate
        
        result = self.ai_generator.generate_signal(prompt, sample_rate, duration)
        
        # Réactiver le bouton
        self.ui.btn_ai_send.setEnabled(True)
        self.ui.btn_ai_send.setText("⚡ Générer")
        
        if result['success']:
            # Afficher la réponse IA
            self._ai_append_chat("ai", result['explanation'])
            
            # Mettre à jour le code affiché
            self.ui.lbl_ai_code.setText(result['code'])
            
            # Stocker le signal et mettre à jour la prévisualisation
            self.ai_current_signal = result['signal']
            n = len(self.ai_current_signal)
            
            # Récupération de la durée calculée automatiquement par l'IA
            duration = result.get('duration', duration)
            
            # Mise à jour du paramètre Durée du signal (pour info à l'utilisateur)
            self.ui.spin_ai_duration.blockSignals(True)
            self.ui.spin_ai_duration.setValue(duration)
            self.ui.spin_ai_duration.blockSignals(False)
            
            # Mise à jour de l'échelle de vue
            self.ui.spin_ai_preview_scale.blockSignals(True)
            self.ui.spin_ai_preview_scale.setValue(duration)
            self.ui.spin_ai_preview_scale.blockSignals(False)
            
            self.update_ai_preview_scale()
            
            # Auto-range Y
            y_max = max(abs(self.ai_current_signal.min()), abs(self.ai_current_signal.max()), 0.1)
            self.ui.ai_preview_plot.setYRange(-y_max * 1.1, y_max * 1.1)
            
            # Activer les boutons d'application
            self.ui.btn_ai_apply_w1.setEnabled(True)
            self.ui.btn_ai_apply_w2.setEnabled(True)
            self.ui.lbl_ai_status.setText(f"✅ Signal généré ({n} échantillons, {duration*1000:.1f} ms)")
            self.ui.lbl_ai_status.setStyleSheet("color: #5cb85c; font-style: normal; font-size: 11px; padding: 4px;")
        else:
            # Afficher l'erreur
            self._ai_append_chat("error", result['error'])
            
            # S'il y a du code et une erreur d'exécution, montrer le code
            if result['code']:
                self.ui.lbl_ai_code.setText(result['code'])
            
            self.ui.lbl_ai_status.setText("❌ Erreur de génération")
            self.ui.lbl_ai_status.setStyleSheet("color: #d9534f; font-style: normal; font-size: 11px; padding: 4px;")

    def on_ai_clear(self):
        """Efface l'historique de conversation et réinitialise l'onglet IA."""
        self.ai_generator.clear_history()
        self.ai_current_signal = None
        self.ui.txt_ai_chat.setHtml(
            '<p style="color: #666; font-style: italic;">'
            'Décrivez le signal que vous souhaitez générer...<br>'
            'Exemples : "Sinusoïde 1kHz amplitude 2V", '
            '"Signal carré 500Hz", "Chirp de 100Hz à 5kHz"</p>'
        )
        self.ui.ai_preview_curve.setData([], [])
        self.ui.lbl_ai_code.setText("")
        self.ui.btn_ai_apply_w1.setEnabled(False)
        self.ui.btn_ai_apply_w2.setEnabled(False)
        self.ui.lbl_ai_status.setText("En attente d'un signal...")
        self.ui.lbl_ai_status.setStyleSheet("color: #888; font-style: italic; font-size: 11px; padding: 4px;")

    def update_ai_preview_scale(self):
        if self.ai_current_signal is None:
            return
            
        scale = self.ui.spin_ai_preview_scale.value()
        duration = self.ui.spin_ai_duration.value()
        n = len(self.ai_current_signal)
        
        n_view = int((scale / duration) * n)
        if n_view <= 0: return
        
        # Le signal généré par l'IA sera joué de manière cyclique. 
        # On répète donc le tableau si la vue est plus grande que la durée initiale du burst.
        if n_view > n:
            repeats = int(np.ceil(n_view / n))
            sig_view = np.tile(self.ai_current_signal, repeats)[:n_view]
        else:
            sig_view = self.ai_current_signal[:n_view]
            
        max_display = 4000
        if len(sig_view) > max_display:
            sig_view_opt = self.fast_downsample(sig_view, max_display)
            t_view_opt = np.linspace(0, scale, len(sig_view_opt), endpoint=False)
            self.ui.ai_preview_curve.setData(t_view_opt, sig_view_opt)
        else:
            t_view = np.linspace(0, scale, n_view, endpoint=False)
            self.ui.ai_preview_curve.setData(t_view, sig_view)
            
        self.ui.ai_preview_plot.setXRange(0, scale, padding=0)

    def on_ai_apply(self, channel):
        """Envoie le signal IA prévisualisé sur W1 (channel=0) ou W2 (channel=1)."""
        if self.ai_current_signal is None:
            return
        
        try:
            self.controller.push_raw_waveform(channel, self.ai_current_signal)
            ch_name = "W1" if channel == 0 else "W2"
            self.ui.lbl_ai_status.setText(f"✅ Signal appliqué sur {ch_name} !")
            self.ui.lbl_ai_status.setStyleSheet("color: #5cb85c; font-weight: bold; font-size: 11px; padding: 4px;")
            self._ai_append_chat("system", f"Signal envoyé sur la sortie {ch_name}.")
        except Exception as e:
            self.ui.lbl_ai_status.setText(f"❌ Erreur : {str(e)[:60]}")
            self.ui.lbl_ai_status.setStyleSheet("color: #d9534f; font-size: 11px; padding: 4px;")
            self._ai_append_chat("error", f"Impossible d'envoyer le signal : {e}")

    def _ai_append_chat(self, role, text):
        """Ajoute un message au chat IA avec mise en forme HTML."""
        html = self.ui.txt_ai_chat.toHtml()
        
        # Retirer le message d'accueil initial si encore présent
        if 'Décrivez le signal que vous souhaitez' in html and role == 'user':
            html = ''
        
        if role == "user":
            bubble = (
                f'<div style="margin: 6px 0; padding: 8px 12px; '
                f'background-color: #1a2a4a; border-radius: 10px; '
                f'border-left: 3px solid #5bc0de;">'
                f'<b style="color: #5bc0de;">🧑 Vous :</b><br>'
                f'<span style="color: #e0e0e0;">{text}</span></div>'
            )
        elif role == "ai":
            bubble = (
                f'<div style="margin: 6px 0; padding: 8px 12px; '
                f'background-color: #1a2a1a; border-radius: 10px; '
                f'border-left: 3px solid #5cb85c;">'
                f'<b style="color: #5cb85c;">🤖 IA :</b><br>'
                f'<span style="color: #c0e0c0;">{text}</span></div>'
            )
        elif role == "system":
            bubble = (
                f'<div style="margin: 4px 0; padding: 6px 10px; '
                f'border-left: 3px solid #f0ad4e;">'
                f'<span style="color: #f0ad4e; font-size: 11px;">⚙️ {text}</span></div>'
            )
        elif role == "error":
            bubble = (
                f'<div style="margin: 6px 0; padding: 8px 12px; '
                f'background-color: #2a1a1a; border-radius: 10px; '
                f'border-left: 3px solid #d9534f;">'
                f'<b style="color: #d9534f;">⚠️ Erreur :</b><br>'
                f'<span style="color: #ff9999;">{text}</span></div>'
            )
        else:
            bubble = f'<p>{text}</p>'
        
        self.ui.txt_ai_chat.append(bubble)
        
        # Auto-scroll vers le bas
        scrollbar = self.ui.txt_ai_chat.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

def _check_and_install_libm2k():
    """Vérifie si libm2k est installé, propose l'installation automatique sinon."""
    if LIBM2K_AVAILABLE:
        return True
    
    # Trouver l'installateur embarqué
    installer_name = "libm2k-0.9.0-setup.exe"
    search_paths = [
        os.path.join(_BASE_DIR, installer_name),
        os.path.join(_BASE_DIR, '..', installer_name),
        os.path.join(os.path.dirname(_BASE_DIR), installer_name),
    ]
    installer_path = None
    for p in search_paths:
        if os.path.exists(p):
            installer_path = os.path.abspath(p)
            break
    
    # Créer une mini-app Qt juste pour le dialogue
    temp_app = QApplication.instance() or QApplication(sys.argv)
    
    if installer_path:
        reply = QMessageBox.question(
            None,
            "Driver ADALM2000 manquant",
            "Le driver ADALM2000 (libm2k) n'est pas encore installé.\n\n"
            "Voulez-vous lancer l'installation maintenant ?\n"
            "(Cela ne prend qu'une minute)\n\n"
            "L'oscilloscope se lancera ensuite normalement.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                subprocess.Popen([installer_path], shell=True)
                QMessageBox.information(
                    None,
                    "Installation en cours",
                    "L'installateur du driver a été lancé.\n\n"
                    "Suivez les étapes de l'installateur, puis\n"
                    "relancez l'oscilloscope une fois terminé."
                )
                sys.exit(0)
            except Exception as e:
                QMessageBox.warning(None, "Erreur", f"Impossible de lancer l'installateur :\n{e}")
    else:
        QMessageBox.warning(
            None,
            "Driver ADALM2000 manquant",
            "Le driver ADALM2000 (libm2k) n'est pas installé et\n"
            "l'installateur n'a pas été trouvé dans le dossier.\n\n"
            "Téléchargez-le depuis :\n"
            "https://github.com/analogdevicesinc/libm2k/releases\n\n"
            "L'application peut démarrer, mais la connexion\n"
            "à l'ADALM2000 ne fonctionnera pas."
        )
    return False


if __name__ == '__main__':
    _check_and_install_libm2k()
    app = OscilloscopeApp()
    app.run()
