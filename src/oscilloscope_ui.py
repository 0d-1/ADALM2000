"""
ADALM2000 Laboratory - UI Module
© 2024-2026 Odin De Baerdemaker - Tous droits réservés
"""
import pyqtgraph as pg
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QGroupBox, QDoubleSpinBox, QTabWidget, QCheckBox, 
                             QScrollArea, QComboBox, QSplitter, QToolButton, QMenu)
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtCore import Qt, QPoint

class OscilloscopeUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("SCODIN - ADALM2000 Pro Station")
        self.resize(1200, 800)
        
        pg.setConfigOption('background', 'k')
        pg.setConfigOption('foreground', 'd')
        pg.setConfigOptions(useOpenGL=True, antialias=False)
        
        main_layout = QVBoxLayout(self)
        
        # --- Splitter Principal ---
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- Zone Gauche : Graphique et Outils ---
        self.graph_container = QWidget()
        self.graph_layout = QVBoxLayout(self.graph_container)
        self.graph_layout.setContentsMargins(0,0,0,0)
        
        self.plot_widget = pg.PlotWidget(title="Analyseur de Signaux ADALM2000")
        self.plot_widget.setLabel('left', 'Tension', units='V')
        self.plot_widget.setLabel('bottom', 'Temps', units='s')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Curseurs et ROI (Cachés au départ)
        self.v_cursor1 = pg.InfiniteLine(angle=90, movable=True, pen=pg.mkPen('r', width=2), label="V1", labelOpts={'position':0.1})
        self.v_cursor2 = pg.InfiniteLine(angle=90, movable=True, pen=pg.mkPen('g', width=2), label="V2", labelOpts={'position':0.2})
        self.h_cursor1 = pg.InfiniteLine(angle=0, movable=True, pen=pg.mkPen('y', width=2), label="H1", labelOpts={'position':0.1})
        self.h_cursor2 = pg.InfiniteLine(angle=0, movable=True, pen=pg.mkPen('m', width=2), label="H2", labelOpts={'position':0.2})
        
        self.roi_fft = pg.LinearRegionItem(values=(0.01, 0.02), brush=pg.mkBrush(0, 200, 255, 40))
        
        # Label de mesure flottant
        self.measure_label = pg.TextItem(text="", color=(255, 255, 255), fill=(0, 0, 0, 150))
        
        # --- Bouton d'analyse flottant sur le Plot ---
        self.btn_analyze = QToolButton(self.plot_widget)
        self.btn_analyze.setText("📊 Analyse")
        self.btn_analyze.setFixedSize(100, 30)
        self.btn_analyze.setStyleSheet("background-color: #333; color: #5bc0de; font-weight: bold; border: 1px solid #5bc0de; border-radius: 5px;")
        self.btn_analyze.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        
        self.menu_analyze = QMenu(self.btn_analyze)
        self.action_v_cursors = QAction("📏 Curseurs Temporels (V)", self, checkable=True)
        self.action_h_cursors = QAction("⚡ Curseurs Tension (H)", self, checkable=True)
        self.action_roi_fft = QAction("🔍 FFT de Zone (ROI)", self, checkable=True)
        self.menu_analyze.addActions([self.action_v_cursors, self.action_h_cursors, self.action_roi_fft])
        self.btn_analyze.setMenu(self.menu_analyze)
        self.btn_analyze.move(10, 10)
        
        # Courbes
        self.curve_ideal = self.plot_widget.plot(pen=pg.mkPen('#2ca02c', width=2, style=Qt.PenStyle.DashLine), name="Signal Idéal")
        self.curve = self.plot_widget.plot(pen=pg.mkPen('#1f77b4', width=2), name="Canal 1")
        self.curve_ch2 = self.plot_widget.plot(pen=pg.mkPen('#ff7f0e', width=2), name="Canal 2")
        
        self.curve_ideal.setVisible(False)
        self.plot_widget.addLegend(offset=(10, 40))
        
        self.graph_layout.addWidget(self.plot_widget)
        
        # --- Zone Droite : Onglets ---
        self.tabs = QTabWidget()
        
        self.tab_osc = QWidget()
        self.tab_gen = QWidget()
        self.tab_custom_gen = QWidget()
        self.tab_spectrum = QWidget()
        self.tab_xy = QWidget()
        self.tab_math = QWidget()
        self.tab_voltmeter = QWidget()
        self.tab_logger = QWidget()
        
        self.tabs.addTab(self.tab_osc, "Oscillo")
        self.tabs.addTab(self.tab_gen, "Générateur W1")
        self.tabs.addTab(self.tab_custom_gen, "Générateurs W1/W2")
        self.tabs.addTab(self.tab_spectrum, "Spectre")
        self.tabs.addTab(self.tab_xy, "Vue XY")
        self.tabs.addTab(self.tab_math, "Math & Réf")
        self.tabs.addTab(self.tab_voltmeter, "Voltmètre")
        self.tabs.addTab(self.tab_logger, "Enregistreur")
        
        self.setup_oscilloscope_tab()
        self.setup_generator_tab()
        self.setup_custom_generators_tab()
        self.setup_spectrum_tab()
        self.setup_xy_tab()
        self.setup_math_tab()
        self.setup_voltmeter_tab()
        self.setup_logger_tab()
        
        self.splitter.addWidget(self.graph_container)
        self.splitter.addWidget(self.tabs)
        self.splitter.setStretchFactor(0, 4)
        self.splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(self.splitter)
        
        # --- Pied de page (Copyright) ---
        self.lbl_copyright = QLabel("© 2024-2026 Odin De Baerdemaker - Tous droits réservés")
        self.lbl_copyright.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_copyright.setStyleSheet("color: #666; font-size: 10px; padding-right: 5px; margin-top: 2px;")
        main_layout.addWidget(self.lbl_copyright)
        
    def setup_oscilloscope_tab(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)

        # --- NOUVEAU GROUPE : Connexion Matérielle ---
        group_conn = QGroupBox("Connexion Matérielle")
        layout_conn = QVBoxLayout()
        
        self.lbl_status = QLabel("Statut : En attente...")
        self.lbl_status.setStyleSheet("color: orange; font-weight: bold; font-size: 14px;")
        layout_conn.addWidget(self.lbl_status)
        
        self.btn_reconnect = QPushButton("Rechercher et Connecter")
        self.btn_reconnect.setStyleSheet("background-color: #337ab7; color: white; padding: 5px;")
        layout_conn.addWidget(self.btn_reconnect)
        
        group_conn.setLayout(layout_conn)
        layout.addWidget(group_conn)
        
        # Bouton Run/Stop
        self.btn_run_stop = QPushButton("En cours (Cliquer pour mettre en Pause)")
        self.btn_run_stop.setCheckable(True)
        self.btn_run_stop.setStyleSheet("background-color: #5cb85c; color: white; font-weight: bold; padding: 10px;")
        layout.addWidget(self.btn_run_stop)
        
        # Groupe: Base de temps (Axe X)
        group_time = QGroupBox("Base de Temps (Horizontal)")
        layout_time = QVBoxLayout()
        
        h_time_row = QHBoxLayout()
        h_time_row.addWidget(QLabel("Base de Temps (s/div) :"))
        self.spin_time = QDoubleSpinBox()
        self.spin_time.setRange(0.0001, 60.0)
        self.spin_time.setDecimals(4)
        self.spin_time.setValue(0.5) 
        self.spin_time.setSingleStep(0.05)
        h_time_row.addWidget(self.spin_time)
        layout_time.addLayout(h_time_row)

        h_pos_row = QHBoxLayout()
        h_pos_row.addWidget(QLabel("Position Horiz. (s) :"))
        self.spin_h_pos = QDoubleSpinBox()
        self.spin_h_pos.setRange(-60.0, 60.0)
        self.spin_h_pos.setDecimals(3)
        self.spin_h_pos.setValue(0.0)
        h_pos_row.addWidget(self.spin_h_pos)
        layout_time.addLayout(h_pos_row)

        h_mem_row = QHBoxLayout()
        h_mem_row.addWidget(QLabel("Prof. Mémoire :"))
        self.combo_mem_depth = QComboBox()
        self.combo_mem_depth.addItems(["Auto", "1k", "10k", "100k", "1M"])
        h_mem_row.addWidget(self.combo_mem_depth)
        layout_time.addLayout(h_mem_row)
        
        group_time.setLayout(layout_time)
        layout.addWidget(group_time)
        
        # Groupe: Réglages Canaux (Axe Y)
        group_volt = QGroupBox("Réglages des Canaux (Vertical)")
        layout_volt = QVBoxLayout()
        
        self.btn_autoset = QPushButton("AUTOSET (Calage Auto)")
        self.btn_autoset.setStyleSheet("background-color: #5bc0de; color: white; font-weight: bold; margin-bottom: 5px;")
        layout_volt.addWidget(self.btn_autoset)

        self.chk_auto_y = QCheckBox("Échelle Y Dynamique (Auto)")
        self.chk_auto_y.setChecked(True)
        layout_volt.addWidget(self.chk_auto_y)
        
        # --- Canal 1 ---
        self.chk_ch1 = QCheckBox("Canal 1 (C1)")
        self.chk_ch1.setChecked(True)
        self.chk_ch1.setStyleSheet("color: #1f77b4; font-weight: bold;")
        layout_volt.addWidget(self.chk_ch1)

        grid_ch1 = QHBoxLayout()
        grid_ch1.addWidget(QLabel("V/div :"))
        self.spin_v_div_ch1 = QDoubleSpinBox()
        self.spin_v_div_ch1.setRange(0.01, 10.0)
        self.spin_v_div_ch1.setValue(1.0)
        grid_ch1.addWidget(self.spin_v_div_ch1)
        grid_ch1.addWidget(QLabel("Offs :"))
        self.spin_offset_ch1 = QDoubleSpinBox()
        self.spin_offset_ch1.setRange(-20.0, 20.0)
        self.spin_offset_ch1.setValue(0.0)
        grid_ch1.addWidget(self.spin_offset_ch1)
        layout_volt.addLayout(grid_ch1)

        opts_ch1 = QHBoxLayout()
        self.chk_ac_ch1 = QCheckBox("AC Logiciel")
        opts_ch1.addWidget(self.chk_ac_ch1)
        self.combo_probe_ch1 = QComboBox()
        self.combo_probe_ch1.addItems(["Sonde 1x", "Sonde 10x", "Sonde 100x"])
        opts_ch1.addWidget(self.combo_probe_ch1)
        self.spin_thick_ch1 = QDoubleSpinBox()
        self.spin_thick_ch1.setRange(0.5, 5.0)
        self.spin_thick_ch1.setValue(2.0)
        self.spin_thick_ch1.setPrefix("Ép: ")
        opts_ch1.addWidget(self.spin_thick_ch1)
        layout_volt.addLayout(opts_ch1)

        # --- Canal 2 ---
        self.chk_ch2 = QCheckBox("Canal 2 (C2)")
        self.chk_ch2.setChecked(False)
        self.chk_ch2.setStyleSheet("color: #ff7f0e; font-weight: bold;")
        layout_volt.addWidget(self.chk_ch2)

        grid_ch2 = QHBoxLayout()
        grid_ch2.addWidget(QLabel("V/div :"))
        self.spin_v_div_ch2 = QDoubleSpinBox()
        self.spin_v_div_ch2.setRange(0.01, 10.0)
        self.spin_v_div_ch2.setValue(1.0)
        grid_ch2.addWidget(self.spin_v_div_ch2)
        grid_ch2.addWidget(QLabel("Offs :"))
        self.spin_offset_ch2 = QDoubleSpinBox()
        self.spin_offset_ch2.setRange(-20.0, 20.0)
        self.spin_offset_ch2.setValue(0.0)
        grid_ch2.addWidget(self.spin_offset_ch2)
        layout_volt.addLayout(grid_ch2)

        opts_ch2 = QHBoxLayout()
        self.chk_ac_ch2 = QCheckBox("AC Logiciel")
        opts_ch2.addWidget(self.chk_ac_ch2)
        self.combo_probe_ch2 = QComboBox()
        self.combo_probe_ch2.addItems(["Sonde 1x", "Sonde 10x", "Sonde 100x"])
        opts_ch2.addWidget(self.combo_probe_ch2)
        self.spin_thick_ch2 = QDoubleSpinBox()
        self.spin_thick_ch2.setRange(0.5, 5.0)
        self.spin_thick_ch2.setValue(2.0)
        self.spin_thick_ch2.setPrefix("Ép: ")
        opts_ch2.addWidget(self.spin_thick_ch2)
        layout_volt.addLayout(opts_ch2)

        group_volt.setLayout(layout_volt)
        layout.addWidget(group_volt)
        
        # Groupe: Trigger Logiciel
        group_trig = QGroupBox("Trigger Logiciel (Auto-Calage X)")
        layout_trig = QVBoxLayout()
        
        self.btn_enable_trigger = QPushButton("Activer Trigger (Stabilisation)")
        self.btn_enable_trigger.setCheckable(True)
        self.btn_enable_trigger.setChecked(True)
        self.btn_enable_trigger.setStyleSheet("background-color: #f0ad4e; color: white; font-weight: bold;")
        layout_trig.addWidget(self.btn_enable_trigger)
        
        layout_trig.addWidget(QLabel("Seuil (Montant) :"))
        h_trig_row = QHBoxLayout()
        self.spin_trig_level = QDoubleSpinBox()
        self.spin_trig_level.setRange(-16.0, 16.0)
        self.spin_trig_level.setSingleStep(0.01)
        self.spin_trig_level.setDecimals(3)
        self.spin_trig_level.setSuffix(" V")
        self.spin_trig_level.setValue(0.01) # 10mV
        h_trig_row.addWidget(self.spin_trig_level)
        
        self.spin_hysteresis = QDoubleSpinBox()
        self.spin_hysteresis.setRange(0.0, 1.0)
        self.spin_hysteresis.setDecimals(3)
        self.spin_hysteresis.setValue(0.02)
        self.spin_hysteresis.setPrefix("Hyst: ")
        h_trig_row.addWidget(self.spin_hysteresis)
        layout_trig.addLayout(h_trig_row)
        
        group_trig.setLayout(layout_trig)
        layout.addWidget(group_trig)
        
        # --- GROUPE : EXPORTATION ---
        group_export = QGroupBox("Exportation et Données")
        layout_export = QVBoxLayout()
        
        self.btn_export_csv = QPushButton("Exporter Snapshot CSV")
        self.btn_export_csv.setStyleSheet("background-color: #f0ad4e; color: white; font-weight: bold;")
        layout_export.addWidget(self.btn_export_csv)
        
        self.bg_color = "white"
        self.line_color = "darkgreen"
        
        self.btn_color_bg = QPushButton("Couleur Fond: Blanc")
        self.btn_color_bg.setStyleSheet("background-color: white; color: black; border: 1px solid gray;")
        layout_export.addWidget(self.btn_color_bg)
        
        self.btn_color_line = QPushButton("Couleur Signal: Vert Foncé")
        self.btn_color_line.setStyleSheet("background-color: darkgreen; color: white;")
        layout_export.addWidget(self.btn_color_line)
        
        self.btn_export = QPushButton("Exporter le Graphique")
        self.btn_export.setStyleSheet("background-color: #0275d8; color: white; font-weight: bold; padding: 5px;")
        self.btn_export.setToolTip("Mettez l'oscilloscope en Pause pour exporter")
        layout_export.addWidget(self.btn_export)
        

        group_export.setLayout(layout_export)
        layout.addWidget(group_export)
        
        # Aide au câblage (Pinout)
        group_pinout = QGroupBox("📌 Guide Rapide des Broches")
        layout_pinout = QVBoxLayout()
        lbl_pins = QLabel(
            "<b>Oscilloscope :</b><br>"
            "• Canal 1 : 1+ (Bleu), 1- (Bleu/Blanc)<br>"
            "• Canal 2 : 2+ (Orange), 2- (Orange/Blanc)<br><br>"
            "<b>Générateurs :</b><br>"
            "• Sortie 1 : W1 (Jaune)<br>"
            "• Sortie 2 : W2 (Jaune/Blanc)<br><br>"
            "<i>Note : Reliez toutes les masses au <b>GND</b> (Noir).</i>"
        )
        lbl_pins.setStyleSheet("font-size: 11px; color: #5bc0de;")
        layout_pinout.addWidget(lbl_pins)
        group_pinout.setLayout(layout_pinout)
        layout.addWidget(group_pinout)
        
        layout.addStretch(1)
        scroll_area.setWidget(content_widget)
        
        main_tab_layout = QVBoxLayout(self.tab_osc)
        main_tab_layout.setContentsMargins(0, 0, 0, 0)
        main_tab_layout.addWidget(scroll_area)
        
    def setup_generator_tab(self):
        layout = QVBoxLayout()
        
        group_gen = QGroupBox("Signal de Référence (Pin: W1)")
        l_gen = QVBoxLayout()
        
        lbl_desc = QLabel("L'ADALM2000 génère continuellement<br>des bursts de 40kHz (65% du temps ON).<br>Vous pouvez ajuster le rythme (BPM)<br>et superposer l'allure théorique à l'écran.")
        l_gen.addWidget(lbl_desc)
        
        layout_bpm = QHBoxLayout()
        layout_bpm.addWidget(QLabel("Rythme (BPM) :"))
        self.spin_bpm = QDoubleSpinBox()
        self.spin_bpm.setRange(1.0, 200.0)
        self.spin_bpm.setDecimals(1)
        self.spin_bpm.setValue(60.0)
        self.spin_bpm.setSingleStep(5.0)
        layout_bpm.addWidget(self.spin_bpm)
        l_gen.addLayout(layout_bpm)
        
        self.chk_show_ideal = QCheckBox("Afficher le signal théorique (Pointillés Verts)")
        self.chk_show_ideal.setChecked(False)
        
        self.chk_show_ideal.stateChanged.connect(
            lambda state: self.curve_ideal.setVisible(bool(state))
        )
        l_gen.addWidget(self.chk_show_ideal)
        
        group_gen.setLayout(l_gen)
        layout.addWidget(group_gen)
        
        layout.addStretch(1)
        self.tab_gen.setLayout(layout)

    def setup_custom_generators_tab(self):
        layout = QVBoxLayout()
        
        # --- Canal W1 ---
        group_w1 = QGroupBox("Générateur W1 (Pin: W1)")
        l_w1 = QVBoxLayout()
        
        l_w1.addWidget(QLabel("Type d'onde W1 :"))
        self.combo_w1_type = QComboBox()
        self.combo_w1_type.addItems(["Sinusoïdale", "Carrée", "Triangulaire", "Dents de scie"])
        l_w1.addWidget(self.combo_w1_type)
        
        l_w1.addWidget(QLabel("Fréquence W1 (Hz) :"))
        self.spin_w1_freq = QDoubleSpinBox()
        self.spin_w1_freq.setRange(0.1, 100000.0)
        self.spin_w1_freq.setValue(1000.0)
        self.spin_w1_freq.setSuffix(" Hz")
        l_w1.addWidget(self.spin_w1_freq)
        
        l_w1.addWidget(QLabel("Amplitude W1 (V) :"))
        self.spin_w1_amp = QDoubleSpinBox()
        self.spin_w1_amp.setRange(0.01, 10.0)
        self.spin_w1_amp.setValue(2.0)
        l_w1.addWidget(self.spin_w1_amp)
        
        self.btn_apply_w1 = QPushButton("Appliquer W1")
        self.btn_apply_w1.setStyleSheet("background-color: #5bc0de; color: white; font-weight: bold;")
        l_w1.addWidget(self.btn_apply_w1)
        
        group_w1.setLayout(l_w1)
        layout.addWidget(group_w1)

        # --- Canal W2 ---
        group_w2 = QGroupBox("Générateur W2 (Pin: W2)")
        l_w2 = QVBoxLayout()
        
        l_w2.addWidget(QLabel("Type d'onde W2 :"))
        self.combo_w2_type = QComboBox()
        self.combo_w2_type.addItems(["Sinusoïdale", "Carrée", "Triangulaire", "Dents de scie"])
        l_w2.addWidget(self.combo_w2_type)
        
        l_w2.addWidget(QLabel("Fréquence W2 (Hz) :"))
        self.spin_w2_freq = QDoubleSpinBox()
        self.spin_w2_freq.setRange(0.1, 100000.0)
        self.spin_w2_freq.setValue(5000.0)
        self.spin_w2_freq.setSuffix(" Hz")
        l_w2.addWidget(self.spin_w2_freq)
        
        l_w2.addWidget(QLabel("Amplitude W2 (V) :"))
        self.spin_w2_amp = QDoubleSpinBox()
        self.spin_w2_amp.setRange(0.01, 10.0)
        self.spin_w2_amp.setValue(2.0)
        l_w2.addWidget(self.spin_w2_amp)
        
        self.btn_apply_w2 = QPushButton("Appliquer W2")
        self.btn_apply_w2.setStyleSheet("background-color: #5cb85c; color: white; font-weight: bold;")
        l_w2.addWidget(self.btn_apply_w2)
        
        group_w2.setLayout(l_w2)
        layout.addWidget(group_w2)
        
        layout.addStretch(1)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        content_widget = QWidget()
        content_widget.setLayout(layout)
        scroll_area.setWidget(content_widget)
        
        main_tab_layout = QVBoxLayout(self.tab_custom_gen)
        main_tab_layout.setContentsMargins(0, 0, 0, 0)
        main_tab_layout.addWidget(scroll_area)

    def setup_spectrum_tab(self):
        layout = QVBoxLayout()
        
        self.spectrum_plot = pg.PlotWidget(title="Analyseur de Spectre (FFT)")
        self.spectrum_plot.setLabel('left', 'Magnitude', units='dBV')
        self.spectrum_plot.setLabel('bottom', 'Fréquence', units='Hz')
        self.spectrum_plot.showGrid(x=True, y=True, alpha=0.3)
        self.spectrum_plot.setYRange(-100, 20)
        
        self.curve_spect_ch1 = self.spectrum_plot.plot(pen=pg.mkPen('#1f77b4', width=1.5), name="Spectre CH1")
        self.curve_spect_ch2 = self.spectrum_plot.plot(pen=pg.mkPen('#ff7f0e', width=1.5), name="Spectre CH2")
        
        self.spectrum_plot.addLegend(offset=(10, 10))
        
        layout.addWidget(self.spectrum_plot, stretch=4)
        
        # Options FFT
        group_fft = QGroupBox("Paramètres de l'Analyseur")
        l_fft = QVBoxLayout()
        
        self.chk_show_spect_ch1 = QCheckBox("Spectre CH1 (Pins: 1+, 1-)")
        self.chk_show_spect_ch1.setChecked(True)
        l_fft.addWidget(self.chk_show_spect_ch1)
        
        self.chk_show_spect_ch2 = QCheckBox("Spectre CH2 (Pins: 2+, 2-)")
        self.chk_show_spect_ch2.setChecked(True)
        l_fft.addWidget(self.chk_show_spect_ch2)

        self.chk_log_freq = QCheckBox("Axe fréquence Logarithmique")
        self.chk_log_freq.stateChanged.connect(lambda state: self.spectrum_plot.setLogMode(x=bool(state)))
        l_fft.addWidget(self.chk_log_freq)
        
        group_fft.setLayout(l_fft)
        layout.addWidget(group_fft, stretch=1)
        
        self.tab_spectrum.setLayout(layout)

    def setup_xy_tab(self):
        layout = QVBoxLayout(self.tab_xy)
        self.xy_plot = pg.PlotWidget(title="Vue XY (Lissajous)")
        self.xy_plot.setLabel('left', 'Canal 1', units='V')
        self.xy_plot.setLabel('bottom', 'Canal 2', units='V')
        self.xy_plot.showGrid(x=True, y=True, alpha=0.3)
        self.curve_xy = self.xy_plot.plot(pen=pg.mkPen('w', width=1.5))
        layout.addWidget(self.xy_plot)
        
        group_opts = QGroupBox("Options XY")
        l_opts = QHBoxLayout()
        self.btn_clear_xy = QPushButton("Effacer Trace")
        l_opts.addWidget(self.btn_clear_xy)
        group_opts.setLayout(l_opts)
        layout.addWidget(group_opts)

    def setup_math_tab(self):
        layout = QVBoxLayout(self.tab_math)
        
        group_math = QGroupBox("Canaux Mathématiques")
        l_math = QVBoxLayout()
        self.chk_math_enabled = QCheckBox("Activer Canal Math [C1 + C2]")
        l_math.addWidget(self.chk_math_enabled)
        
        self.combo_math_op = QComboBox()
        self.combo_math_op.addItems(["Addition (C1 + C2)", "Soustraction (C1 - C2)", "Multiplication (C1 * C2)", "Division (C1 / C2)"])
        l_math.addWidget(self.combo_math_op)
        
        self.curve_math = self.plot_widget.plot(pen=pg.mkPen('y', width=2, style=Qt.PenStyle.DashLine), name="Math")
        self.curve_math.setVisible(False)
        self.chk_math_enabled.stateChanged.connect(lambda state: self.curve_math.setVisible(bool(state)))
        
        group_math.setLayout(l_math)
        layout.addWidget(group_math)
        
        group_ref = QGroupBox("Canaux de Référence")
        l_ref = QVBoxLayout()
        self.btn_load_ref = QPushButton("Charger Référence (CSV)")
        l_ref.addWidget(self.btn_load_ref)
        self.curve_ref = self.plot_widget.plot(pen=pg.mkPen('gray', width=1.5), name="Référence")
        self.curve_ref.setVisible(False)
        group_ref.setLayout(l_ref)
        layout.addWidget(group_ref)
        
        layout.addStretch(1)

    def setup_voltmeter_tab(self):
        layout = QVBoxLayout()
        
        # Style pour l'affichage digital
        style_val = "font-family: 'Consolas', 'Courier New'; font-size: 24px; font-weight: bold; color: #1f77b4; background-color: #111; border: 1px solid #333; border-radius: 5px; padding: 10px;"
        style_val2 = style_val.replace("#1f77b4", "#ff7f0e")
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content = QWidget()
        l_content = QVBoxLayout(content)
        
        # --- Options (Calibration) ---
        group_cal = QGroupBox("Calibration et Filtrage")
        l_cal = QVBoxLayout()
        self.btn_auto_zero = QPushButton("Calibrer le Zéro (Auto-Zero)")
        self.btn_auto_zero.setStyleSheet("background-color: #f0ad4e; color: white; font-weight: bold; padding: 10px;")
        self.btn_auto_zero.setToolTip("Reliez les deux Canaux à la masse (GND) avant de cliquer")
        l_cal.addWidget(self.btn_auto_zero)
        
        self.chk_squelch = QCheckBox("Filtre Anti-Bruit (Squelch < 100mV)")
        self.chk_squelch.setChecked(True)
        self.chk_squelch.setToolTip("Force l'affichage à 0.00V si le câble est débranché (bruit flottant)")
        l_cal.addWidget(self.chk_squelch)
        
        group_cal.setLayout(l_cal)
        l_content.addWidget(group_cal)

        # --- Canal 1 ---
        group_ch1 = QGroupBox("Canal 1 (Pins: 1+, 1-)")
        l_ch1 = QVBoxLayout()
        self.lbl_ch1_dc = QLabel("DC: 0.000 V")
        self.lbl_ch1_rms = QLabel("RMS: 0.000 V")
        self.lbl_ch1_vpp = QLabel("Vpp: 0.000 V")
        self.lbl_ch1_freq = QLabel("FREQ: 0 Hz")
        for lbl in [self.lbl_ch1_dc, self.lbl_ch1_rms, self.lbl_ch1_vpp, self.lbl_ch1_freq]:
            lbl.setStyleSheet(style_val)
            l_ch1.addWidget(lbl)
        group_ch1.setLayout(l_ch1)
        l_content.addWidget(group_ch1)

        # --- Canal 2 ---
        group_ch2 = QGroupBox("Canal 2 (Pins: 2+, 2-)")
        l_ch2 = QVBoxLayout()
        self.lbl_ch2_dc = QLabel("DC: 0.000 V")
        self.lbl_ch2_rms = QLabel("RMS: 0.000 V")
        self.lbl_ch2_vpp = QLabel("Vpp: 0.000 V")
        self.lbl_ch2_freq = QLabel("FREQ: 0 Hz")
        for lbl in [self.lbl_ch2_dc, self.lbl_ch2_rms, self.lbl_ch2_vpp, self.lbl_ch2_freq]:
            lbl.setStyleSheet(style_val2)
            l_ch2.addWidget(lbl)
        group_ch2.setLayout(l_ch2)
        l_content.addWidget(group_ch2)
        
        l_content.addStretch(1)
        scroll_area.setWidget(content)
        l_main = QVBoxLayout(self.tab_voltmeter)
        l_main.addWidget(scroll_area)

    def setup_logger_tab(self):
        layout = QVBoxLayout(self.tab_logger)
        
        group_log = QGroupBox("Configuration de l'Enregistreur")
        l_log = QVBoxLayout()
        
        l_log.addWidget(QLabel("Fichier de sortie :"))
        h_file = QHBoxLayout()
        self.txt_log_path = QLabel("Aucun fichier sélectionné")
        self.txt_log_path.setStyleSheet("border: 1px solid gray; padding: 10px; background: #000; color: #5bc0de;")
        h_file.addWidget(self.txt_log_path, stretch=3)
        self.btn_browse_log = QPushButton("Parcourir...")
        h_file.addWidget(self.btn_browse_log, stretch=1)
        l_log.addLayout(h_file)
        
        l_log.addWidget(QLabel("Cadence d'acquisition :"))
        self.combo_log_rate = QComboBox()
        self.combo_log_rate.addItems(["10 Hz (0.1s)", "1 Hz (1s)", "0.1 Hz (10s)"])
        l_log.addWidget(self.combo_log_rate)
        
        self.lbl_log_status = QLabel("Statut : Prêt")
        self.lbl_log_status.setStyleSheet("color: white; font-weight: bold; margin-top: 10px;")
        l_log.addWidget(self.lbl_log_status)

        self.btn_start_log = QPushButton("DÉMARRER L'ENREGISTREMENT")
        self.btn_start_log.setStyleSheet("background-color: #5cb85c; color: white; font-weight: bold; padding: 15px;")
        l_log.addWidget(self.btn_start_log)

        self.btn_stop_log = QPushButton("ARRÊTER L'ENREGISTREMENT")
        self.btn_stop_log.setStyleSheet("background-color: #d9534f; color: white; font-weight: bold; padding: 15px;")
        self.btn_stop_log.setEnabled(False)
        l_log.addWidget(self.btn_stop_log)
        
        group_log.setLayout(l_log)
        layout.addWidget(group_log)
        layout.addStretch(1)
