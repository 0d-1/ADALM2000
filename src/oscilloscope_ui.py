"""
ADALM2000 Laboratory - UI Module
© 2024-2026 Odin De Baerdemaker - Tous droits réservés
"""
import pyqtgraph as pg
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QGroupBox, QDoubleSpinBox, QTabWidget, QCheckBox, 
                             QScrollArea, QComboBox, QSplitter, QToolButton, QMenu, QLineEdit,
                             QTextEdit, QFrame)
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtCore import Qt, QPoint

class OscilloscopeUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("SCODIN - ADALM2000 Pro Station")
        self.resize(1200, 800)
        self.setStyleSheet("background-color: #121212; color: #e0e0e0;")
        
        pg.setConfigOption('background', 'k')
        pg.setConfigOption('foreground', 'd')
        pg.setConfigOptions(useOpenGL=True, antialias=False)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
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
        
        # --- Bouton RECENTRER flottant (apparait quand vue décalée) ---
        self.btn_recenter = QPushButton("🎯 Recentrer", self.plot_widget)
        self.btn_recenter.setFixedSize(110, 32)
        self.btn_recenter.setStyleSheet("""
            QPushButton {
                background-color: rgba(91, 192, 222, 200);
                color: white;
                font-weight: bold;
                font-size: 12px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(91, 192, 222, 255);
            }
        """)
        self.btn_recenter.move(120, 10)
        self.btn_recenter.hide()
        
        # --- Label FPS flottant ---
        self.lbl_fps = QLabel("-- FPS", self.plot_widget)
        self.lbl_fps.setStyleSheet("color: #666; font-size: 10px; background: transparent;")
        self.lbl_fps.setFixedSize(60, 16)
        self.lbl_fps.move(10, 44)
        
        # Flag pour savoir si l'utilisateur a déplacé la vue manuellement
        self._user_panned = False
        
        self.graph_layout.addWidget(self.plot_widget)
        
        # --- Zone Droite : Navigation par Catégories ---
        # Style commun pour les onglets (principal et sous-onglets)
        _tab_style = """
            QTabWidget::pane {
                border: 1px solid #333;
                border-top: none;
                background: #121212;
            }
            QTabBar::tab {
                background: #1a1a2e;
                color: #888;
                padding: 8px 12px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border: 1px solid #333;
                border-bottom: none;
                font-weight: bold;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background: #121212;
                color: #e0e0e0;
                border-bottom: 2px solid #5bc0de;
            }
            QTabBar::tab:hover:!selected {
                background: #252540;
                color: #bbb;
            }
        """
        _sub_tab_style = """
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: transparent;
                color: #666;
                padding: 5px 10px;
                margin-right: 1px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                color: #5bc0de;
                border-bottom: 2px solid #5bc0de;
            }
            QTabBar::tab:hover:!selected {
                color: #aaa;
                border-bottom: 2px solid #444;
            }
        """
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(_tab_style)
        
        # --- Création des pages individuelles ---
        self.tab_osc = QWidget()
        self.tab_gen = QWidget()
        self.tab_custom_gen = QWidget()
        self.tab_spectrum = QWidget()
        self.tab_xy = QWidget()
        self.tab_math = QWidget()
        self.tab_voltmeter = QWidget()
        self.tab_multimeter = QWidget()
        self.tab_logger = QWidget()
        self.tab_ai = QWidget()
        
        # --- Catégorie 1 : Oscilloscope (pas de sous-onglets) ---
        self.tabs.addTab(self.tab_osc, "📡 Oscillo")
        
        # --- Catégorie 2 : Générateurs (3 sous-onglets) ---
        self.sub_tabs_gen = QTabWidget()
        self.sub_tabs_gen.setStyleSheet(_sub_tab_style)
        self.sub_tabs_gen.addTab(self.tab_gen, "Réf W1")
        self.sub_tabs_gen.addTab(self.tab_custom_gen, "W1 / W2")
        self.sub_tabs_gen.addTab(self.tab_ai, "🤖 IA")
        self.tabs.addTab(self.sub_tabs_gen, "⚡ Générateurs")
        
        # --- Catégorie 3 : Analyse (3 sous-onglets) ---
        self.sub_tabs_analysis = QTabWidget()
        self.sub_tabs_analysis.setStyleSheet(_sub_tab_style)
        self.sub_tabs_analysis.addTab(self.tab_spectrum, "Spectre FFT")
        self.sub_tabs_analysis.addTab(self.tab_xy, "Vue XY")
        self.sub_tabs_analysis.addTab(self.tab_math, "Math & Réf")
        self.tabs.addTab(self.sub_tabs_analysis, "📊 Analyse")
        
        # --- Catégorie 4 : Instruments (2 sous-onglets) ---
        self.sub_tabs_instr = QTabWidget()
        self.sub_tabs_instr.setStyleSheet(_sub_tab_style)
        self.sub_tabs_instr.addTab(self.tab_voltmeter, "Voltmètre")
        self.sub_tabs_instr.addTab(self.tab_multimeter, "Multimètre")
        self.tabs.addTab(self.sub_tabs_instr, "🔬 Instruments")
        
        # --- Catégorie 5 : Enregistreur (pas de sous-onglets) ---
        self.tabs.addTab(self.tab_logger, "💾 Enregistreur")
        
        # --- Initialisation de toutes les pages ---
        self.setup_oscilloscope_tab()
        self.setup_generator_tab()
        self.setup_custom_generators_tab()
        self.setup_spectrum_tab()
        self.setup_xy_tab()
        self.setup_math_tab()
        self.setup_voltmeter_tab()
        self.setup_multimeter_tab()
        self.setup_logger_tab()
        self.setup_ai_tab()
        
        self.splitter.addWidget(self.graph_container)
        self.splitter.addWidget(self.tabs)
        
        # Définir la largeur du panneau de droite à 380px
        self.splitter.setSizes([820, 380])
        
        main_layout.addWidget(self.splitter, 1)
        
        # --- Pied de page (Copyright) ---
        self.lbl_copyright = QLabel("© 2024-2026 Odin De Baerdemaker - Tous droits réservés")
        self.lbl_copyright.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_copyright.setStyleSheet("color: #444; font-size: 9px; padding: 2px 10px; background-color: #121212;")
        main_layout.addWidget(self.lbl_copyright, 0)
        
    def get_active_page(self):
        """Retourne le widget de la page réellement visible (résout les sous-onglets)."""
        current = self.tabs.currentWidget()
        if isinstance(current, QTabWidget):
            return current.currentWidget()
        return current
    
    def navigate_to(self, page_widget):
        """Navigue vers une page spécifique, même si elle est dans un sous-onglet."""
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab is page_widget:
                self.tabs.setCurrentIndex(i)
                return
            if isinstance(tab, QTabWidget):
                for j in range(tab.count()):
                    if tab.widget(j) is page_widget:
                        self.tabs.setCurrentIndex(i)
                        tab.setCurrentIndex(j)
                        return

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
        
        # Groupe: Performance et Rendu
        group_perf = QGroupBox("Performance du Rendu")
        layout_perf = QVBoxLayout()
        
        h_quality_row = QHBoxLayout()
        h_quality_row.addWidget(QLabel("Qualité / FPS :"))
        from PyQt6.QtWidgets import QSlider
        self.slider_quality = QSlider(Qt.Orientation.Horizontal)
        self.slider_quality.setRange(1, 5)
        self.slider_quality.setValue(3)
        self.slider_quality.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_quality.setTickInterval(1)
        self.slider_quality.setToolTip("1 = Max FPS (peu de détail) / 5 = Max Qualité (peut être lent)")
        h_quality_row.addWidget(self.slider_quality)
        self.lbl_quality_val = QLabel("3 (Normal)")
        self.lbl_quality_val.setStyleSheet("color: #5bc0de; font-weight: bold; min-width: 80px;")
        h_quality_row.addWidget(self.lbl_quality_val)
        layout_perf.addLayout(h_quality_row)
        
        group_perf.setLayout(layout_perf)
        layout.addWidget(group_perf)
        
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

    def setup_ai_tab(self):
        """Configure l'onglet IA : chat, prévisualisation et contrôles."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(8)
        
        # === GROUPE : Configuration API ===
        group_api = QGroupBox("🔑 Configuration IA")
        group_api.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #5bc0de;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                color: #5bc0de;
            }
        """)
        l_api = QVBoxLayout()
        
        h_api_key = QHBoxLayout()
        h_api_key.addWidget(QLabel("Clé API Groq (gratuite) :"))
        self.txt_api_key = QLineEdit()
        self.txt_api_key.setPlaceholderText("gsk_...")
        self.txt_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_api_key.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a2e;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 6px;
                color: #e0e0e0;
                font-family: 'Consolas', 'Courier New', monospace;
            }
            QLineEdit:focus {
                border-color: #5bc0de;
            }
        """)
        h_api_key.addWidget(self.txt_api_key)
        l_api.addLayout(h_api_key)
        
        lbl_guide = QLabel('<a href="https://console.groq.com/keys" style="color: #5bc0de; font-size: 11px;">➜ Obtenir une clé API gratuite sur console.groq.com</a>')
        lbl_guide.setOpenExternalLinks(True)
        lbl_guide.setAlignment(Qt.AlignmentFlag.AlignRight)
        l_api.addWidget(lbl_guide)
        
        h_duration = QHBoxLayout()
        h_duration.addWidget(QLabel("Durée du signal (s) :"))
        self.spin_ai_duration = QDoubleSpinBox()
        self.spin_ai_duration.setRange(0.001, 1.0)
        self.spin_ai_duration.setDecimals(3)
        self.spin_ai_duration.setValue(0.01)
        self.spin_ai_duration.setSingleStep(0.001)
        self.spin_ai_duration.setSuffix(" s")
        h_duration.addWidget(self.spin_ai_duration)
        l_api.addLayout(h_duration)
        
        group_api.setLayout(l_api)
        layout.addWidget(group_api)
        
        # === ZONE DE CHAT ===
        group_chat = QGroupBox("💬 Conversation")
        group_chat.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                color: #aaa;
            }
        """)
        l_chat = QVBoxLayout()
        
        self.txt_ai_chat = QTextEdit()
        self.txt_ai_chat.setReadOnly(True)
        self.txt_ai_chat.setMinimumHeight(140)
        self.txt_ai_chat.setMaximumHeight(200)
        self.txt_ai_chat.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a1a;
                border: 1px solid #222;
                border-radius: 6px;
                padding: 8px;
                color: #e0e0e0;
                font-size: 12px;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        self.txt_ai_chat.setHtml(
            '<p style="color: #666; font-style: italic;">'
            'Décrivez le signal que vous souhaitez générer...<br>'
            'Exemples : "Sinusoïde 1kHz amplitude 2V", '
            '"Signal carré 500Hz", "Chirp de 100Hz à 5kHz"</p>'
        )
        l_chat.addWidget(self.txt_ai_chat)
        
        # Champ de saisie + bouton envoyer
        h_input = QHBoxLayout()
        self.txt_ai_input = QLineEdit()
        self.txt_ai_input.setPlaceholderText("Décrivez votre signal ici...")
        self.txt_ai_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a2e;
                border: 2px solid #333;
                border-radius: 8px;
                padding: 8px 12px;
                color: #e0e0e0;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #5bc0de;
                background-color: #1e1e3a;
            }
        """)
        h_input.addWidget(self.txt_ai_input, stretch=3)
        
        self.btn_ai_send = QPushButton("⚡ Générer")
        self.btn_ai_send.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5bc0de, stop:1 #3a9fc1);
                color: white;
                font-weight: bold;
                font-size: 13px;
                padding: 8px 16px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6dd0ee, stop:1 #4aafcd);
            }
            QPushButton:pressed {
                background: #2a8faa;
            }
        """)
        h_input.addWidget(self.btn_ai_send)
        l_chat.addLayout(h_input)
        
        self.btn_ai_clear = QPushButton("🗑 Effacer conversation")
        self.btn_ai_clear.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                color: #d9534f;
                border-color: #d9534f;
            }
        """)
        l_chat.addWidget(self.btn_ai_clear)
        
        group_chat.setLayout(l_chat)
        layout.addWidget(group_chat)
        
        # === PRÉVISUALISATION DU SIGNAL ===
        group_preview = QGroupBox("📊 Prévisualisation du Signal")
        group_preview.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #5cb85c;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                color: #5cb85c;
            }
        """)
        l_preview = QVBoxLayout()
        
        h_preview_tools = QHBoxLayout()
        h_preview_tools.addWidget(QLabel("Échelle de temps vue (s) :"))
        self.spin_ai_preview_scale = QDoubleSpinBox()
        self.spin_ai_preview_scale.setRange(0.0001, 10.0)
        self.spin_ai_preview_scale.setDecimals(4)
        self.spin_ai_preview_scale.setValue(0.01)
        self.spin_ai_preview_scale.setSingleStep(0.001)
        # On va l'associer ensuite dans main_oscilloscope
        h_preview_tools.addWidget(self.spin_ai_preview_scale)
        h_preview_tools.addStretch(1)
        l_preview.addLayout(h_preview_tools)
        
        self.ai_preview_plot = pg.PlotWidget()
        self.ai_preview_plot.setMinimumHeight(160)
        self.ai_preview_plot.setMaximumHeight(200)
        self.ai_preview_plot.setLabel('left', 'V')
        self.ai_preview_plot.setLabel('bottom', 's')
        self.ai_preview_plot.showGrid(x=True, y=True, alpha=0.2)
        self.ai_preview_plot.setYRange(-5.5, 5.5)
        self.ai_preview_curve = self.ai_preview_plot.plot(
            pen=pg.mkPen('#5bc0de', width=1.5)
        )
        l_preview.addWidget(self.ai_preview_plot)
        
        # Label code généré (pliable)
        self.lbl_ai_code = QLabel("")
        self.lbl_ai_code.setWordWrap(True)
        self.lbl_ai_code.setStyleSheet("""
            QLabel {
                background-color: #111;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 6px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10px;
                color: #7fdbca;
            }
        """)
        self.lbl_ai_code.setVisible(False)
        l_preview.addWidget(self.lbl_ai_code)
        
        self.btn_ai_show_code = QPushButton("</> Afficher le code")
        self.btn_ai_show_code.setCheckable(True)
        self.btn_ai_show_code.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #7fdbca;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 3px;
                font-size: 11px;
                font-family: monospace;
            }
            QPushButton:hover {
                border-color: #7fdbca;
            }
            QPushButton:checked {
                background-color: #1a2a1a;
                border-color: #7fdbca;
            }
        """)
        self.btn_ai_show_code.clicked.connect(
            lambda checked: self.lbl_ai_code.setVisible(checked)
        )
        l_preview.addWidget(self.btn_ai_show_code)
        
        group_preview.setLayout(l_preview)
        layout.addWidget(group_preview)
        
        # === BOUTONS D'APPLICATION ===
        group_apply = QGroupBox("🎛 Appliquer le Signal")
        group_apply.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #f0ad4e;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                color: #f0ad4e;
            }
        """)
        l_apply = QVBoxLayout()
        
        h_apply_btns = QHBoxLayout()
        
        self.btn_ai_apply_w1 = QPushButton("⚡ Appliquer sur W1")
        self.btn_ai_apply_w1.setEnabled(False)
        self.btn_ai_apply_w1.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f0ad4e, stop:1 #d4952e);
                color: white;
                font-weight: bold;
                font-size: 12px;
                padding: 10px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f5bd6e, stop:1 #e0a540);
            }
            QPushButton:disabled {
                background: #333;
                color: #666;
            }
        """)
        h_apply_btns.addWidget(self.btn_ai_apply_w1)
        
        self.btn_ai_apply_w2 = QPushButton("⚡ Appliquer sur W2")
        self.btn_ai_apply_w2.setEnabled(False)
        self.btn_ai_apply_w2.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5cb85c, stop:1 #449d44);
                color: white;
                font-weight: bold;
                font-size: 12px;
                padding: 10px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6ec86e, stop:1 #55b055);
            }
            QPushButton:disabled {
                background: #333;
                color: #666;
            }
        """)
        h_apply_btns.addWidget(self.btn_ai_apply_w2)
        
        l_apply.addLayout(h_apply_btns)
        
        self.lbl_ai_status = QLabel("En attente d'un signal...")
        self.lbl_ai_status.setStyleSheet("color: #888; font-style: italic; font-size: 11px; padding: 4px;")
        self.lbl_ai_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_apply.addWidget(self.lbl_ai_status)
        
        group_apply.setLayout(l_apply)
        layout.addWidget(group_apply)
        
        layout.addStretch(1)
        scroll_area.setWidget(content_widget)
        
        main_tab_layout = QVBoxLayout(self.tab_ai)
        main_tab_layout.setContentsMargins(0, 0, 0, 0)
        main_tab_layout.addWidget(scroll_area)

    def setup_multimeter_tab(self):
        layout = QVBoxLayout()
        
        style_val = "font-family: 'Consolas', 'Courier New'; font-size: 32px; font-weight: bold; color: #5bc0de; background-color: #111; border: 1px solid #333; border-radius: 8px; padding: 15px;"
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        content = QWidget()
        l_content = QVBoxLayout(content)
        
        # --- Section Ohmmètre ---
        group_ohm = QGroupBox("📏 Mesure de Résistance (Ohmmètre)")
        group_ohm.setStyleSheet("QGroupBox { font-weight: bold; color: #5bc0de; border: 1px solid #5bc0de; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        l_ohm = QVBoxLayout()
        
        self.lbl_ohm_val = QLabel("--- Ω")
        self.lbl_ohm_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_ohm_val.setStyleSheet(style_val)
        l_ohm.addWidget(self.lbl_ohm_val)
        
        # Sélecteur de Gamme
        l_range = QHBoxLayout()
        l_range.addWidget(QLabel("Gamme de mesure :"))
        self.combo_ohm_range = QComboBox()
        self.combo_ohm_range.addItems(["Basse (0 Ω - 5 kΩ)", "Haute (50 kΩ - 10 MΩ)"])
        self.combo_ohm_range.setToolTip("Le mode 'Haute' utilise l'impédance d'entrée de 1 MΩ de l'oscilloscope.")
        l_range.addWidget(self.combo_ohm_range)
        l_ohm.addLayout(l_range)
        
        self.btn_run_ohm = QPushButton("Démarrer l'Ohmmètre")
        self.btn_run_ohm.setCheckable(True)
        self.btn_run_ohm.setStyleSheet("background-color: #333; color: #5bc0de; font-weight: bold; padding: 10px; border: 1px solid #5bc0de;")
        l_ohm.addWidget(self.btn_run_ohm)
        
        # Indicateur de continuité
        self.lbl_continuity = QLabel("Continuité : ---")
        self.lbl_continuity.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_continuity.setStyleSheet("font-weight: bold; padding: 5px; background: #222; border-radius: 4px;")
        l_ohm.addWidget(self.lbl_continuity)
        
        group_ohm.setLayout(l_ohm)
        l_content.addWidget(group_ohm)
        
        # --- Section Voltmètre DC Rapide ---
        group_v = QGroupBox("⚡ Voltmètre DC (Canal 1)")
        l_v = QVBoxLayout()
        self.lbl_multi_v = QLabel("0.000 V")
        self.lbl_multi_v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_multi_v.setStyleSheet(style_val.replace("#5bc0de", "#5cb85c"))
        l_v.addWidget(self.lbl_multi_v)
        group_v.setLayout(l_v)
        l_content.addWidget(group_v)
        
        # --- Guide de Câblage ---
        group_wires = QGroupBox("📌 Instructions de Câblage")
        l_wires = QVBoxLayout()
        self.lbl_ohm_instr = QLabel(
            "<b>Mode Basse Résistance :</b><br>"
            "• <b>W1 (Jaune)</b> et <b>1+ (Orange)</b> sur un côté.<br>"
            "• <b>GND (Noir)</b> sur l'autre côté.<br><br>"
            "<b>Mode Haute Résistance (> 50kΩ) :</b><br>"
            "• <b>W1 (Jaune)</b> sur un côté.<br>"
            "• <b>1+ (Orange)</b> sur l'autre côté.<br>"
            "• <b>1- (Bleu/Blanc)</b> relié au <b>GND (Noir)</b>."
        )
        self.lbl_ohm_instr.setStyleSheet("color: #aaa; font-size: 11px;")
        l_wires.addWidget(self.lbl_ohm_instr)
        group_wires.setLayout(l_wires)
        l_content.addWidget(group_wires)
        
        l_content.addStretch(1)
        scroll_area.setWidget(content)
        l_main = QVBoxLayout(self.tab_multimeter)
        l_main.setContentsMargins(0, 0, 0, 0)
        l_main.addWidget(scroll_area)
