try:
    import libm2k
    LIBM2K_AVAILABLE = True
except Exception as e:
    libm2k = None
    LIBM2K_AVAILABLE = False
    print(f"M2kController: Erreur d'importation de libm2k : {e}")
import numpy as np
import time
from PyQt6.QtCore import QObject, pyqtSignal, QThread

class DataAcquisitionThread(QThread):
    connection_lost = pyqtSignal()

    def __init__(self, ain, samples_to_read, callback):
        super().__init__()
        self.ain = ain
        self.samples_to_read = samples_to_read
        self.callback = callback
        self.running = False

    def run(self):
        self.running = True
        # On fragmente la lecture pour ne pas bloquer le GIL (Python) pendant de longues périodes.
        # Des lectures de 10ms (4000 pour 400kSPS) permettent à l'UI PyQt de s'actualiser sans freeze !
        chunk_size = 4000 
        chunks_ch1 = []
        chunks_ch2 = []
        accumulated = 0
        consecutive_errors = 0
        MAX_CONSECUTIVE_ERRORS = 5
        
        while self.running:
            try:
                # Lecture matérielle bloquante et rapide
                data = self.ain.getSamples(chunk_size)
                
                if data and len(data) > 0 and len(data[0]) > 0:
                    ch1_data = np.asarray(data[0], dtype=np.float64)
                    # Clamp des valeurs extrêmes (protection contre les spikes matériels)
                    np.clip(ch1_data, -25.0, 25.0, out=ch1_data)
                    chunks_ch1.append(ch1_data)
                    
                    # S'il y a un 2e canal activé
                    if len(data) > 1 and len(data[1]) > 0:
                        ch2_data = np.asarray(data[1], dtype=np.float64)
                        np.clip(ch2_data, -25.0, 25.0, out=ch2_data)
                        chunks_ch2.append(ch2_data)
                    else:
                        chunks_ch2.append(np.zeros(len(data[0]))) # Fallback si pb

                    accumulated += len(data[0])
                    
                    # On émet quand on a nos 0.1s de données
                    if accumulated >= self.samples_to_read:
                        y_data_ch1 = np.concatenate(chunks_ch1)
                        y_data_ch2 = np.concatenate(chunks_ch2)
                        # Appel du callback direct plutôt que d'émettre un signal Qt
                        self.callback((y_data_ch1, y_data_ch2))
                        chunks_ch1 = []
                        chunks_ch2 = []
                        accumulated = 0
                
                # TRÈS IMPORTANT : Libérer explicitement le GIL pour laisser le thread PyQt dessiner
                time.sleep(0.001)
                
            except Exception as e:
                print(f"FATAL: Erreur de lecture matérielle, appareil déconnecté ? ({e})")
                self.connection_lost.emit()
                break
                
    def stop(self):
        self.running = False
        self.wait()

class M2kController(QObject):
    connection_lost = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.ctx = None
        self.aout = None
        self.ain = None
        self.sample_rate = 400000
        self.worker_thread = None

    def connect_device(self):
        if not LIBM2K_AVAILABLE:
            raise ConnectionError(
                "Le driver ADALM2000 (libm2k) n'est pas installé.\n"
                "Lancez l'installateur 'libm2k-0.9.0-setup.exe' puis redémarrez l'application."
            )
        print("M2kController: Connexion à l'ADALM2000...")
        self.ctx = libm2k.m2kOpen()
        if self.ctx is None:
            raise ConnectionError("Impossible de trouver l'ADALM2000. Fermez Scopy et vérifiez le câble USB.")
            
        # Timeout de 1 seconde pour éviter les freezes si l'appareil plante ou disparaît du bus USB suite à un pic de tension
        self.ctx.setTimeout(1000)
        
        self.ctx.calibrateDAC()
        self.ctx.calibrateADC()

        self.aout = self.ctx.getAnalogOut()
        self.ain = self.ctx.getAnalogIn()
        print("M2kController: Appareil connecté et calibré.")

    def generate_base_signal(self, bpm=60.0):
        if not self.ctx:
            return
            
        period_s = 60.0 / bpm
        print(f"M2kController: Génération du signal 40kHz à {bpm} BPM (T={period_s:.3f}s)...")
        self.aout.setSampleRate(0, self.sample_rate)
        
        samples_period = int(self.sample_rate * period_s)
        t = np.linspace(0, period_s, samples_period, endpoint=False)
        wave = np.zeros(samples_period)
        
        idx_on = int(samples_period * 0.65)
        wave[:idx_on] = 0.03 * np.sin(2 * np.pi * 40000 * t[:idx_on])
        
        self.aout.setCyclic(True)
        self.aout.enableChannel(0, True)
        self.aout.push(0, wave)

    def generate_custom_waveform(self, channel, wave_type_idx, frequency, amplitude, offset, duty_cycle=50.0):
        if not self.ctx:
            return
            
        print(f"M2kController: Génération d'onde type {wave_type_idx} sur W{channel+1} à {frequency}Hz...")
        self.aout.setSampleRate(channel, self.sample_rate)
        
        # Pour une boucle fluide, on essaie d'avoir un nombre entier de cycles
        # On se limite à un buffer de 1s max (400,000 points)
        if frequency >= 1.0:
            period_samples = self.sample_rate / frequency
            # On prend un nombre de périodes pour s'approcher de 0.1s ou au moins 1 période
            num_periods = max(1, int(0.1 * frequency))
            total_samples = int(period_samples * num_periods)
        else:
            # Très basse fréquence, on prend juste une période
            total_samples = int(self.sample_rate / frequency)
            
        # Limite haute pour éviter d'exploser la RAM (ex: 2M points)
        total_samples = min(total_samples, 2000000)
        
        t = np.linspace(0, total_samples / self.sample_rate, total_samples, endpoint=False)
        wave = np.zeros(total_samples)
        
        amp_half = amplitude / 2.0
        
        if wave_type_idx == 0: # Sinusoïdale
            wave = amp_half * np.sin(2 * np.pi * frequency * t) + offset
        elif wave_type_idx == 1: # Carrée
            # Utilisation du rapport cyclique (duty cycle)
            wave = np.where((t * frequency) % 1.0 < (duty_cycle / 100.0), amp_half, -amp_half) + offset
        elif wave_type_idx == 2: # Triangulaire
            wave = amp_half * (2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1) + offset
        elif wave_type_idx == 3: # Dents de scie
            wave = amp_half * (2 * (t * frequency - np.floor(t * frequency))) - amp_half + offset
            
        self.aout.setCyclic(True)
        self.aout.enableChannel(channel, True)
        self.aout.push(channel, wave)

    def push_raw_waveform(self, channel, wave_array):
        """Envoie un tableau numpy brut sur la sortie W1 (channel=0) ou W2 (channel=1)."""
        if not self.ctx:
            raise ConnectionError("ADALM2000 non connecté. Impossible d'envoyer le signal.")
        
        self.aout.setSampleRate(channel, self.sample_rate)
        self.aout.setCyclic(True)
        self.aout.enableChannel(channel, True)
        self.aout.push(channel, wave_array)
        print(f"M2kController: Signal IA poussé sur W{channel+1} ({len(wave_array)} échantillons)")
        
    def start_acquisition(self, callback):
        if not self.ctx:
            return

        actual_rate = self.ain.setSampleRate(self.sample_rate)
        if actual_rate and actual_rate != self.sample_rate:
            print(f"M2kController: ATTENTION - Fréquence d'échantillonnage demandée: {self.sample_rate}, obtenue: {actual_rate}")
            self.sample_rate = int(actual_rate)
        self.ain.enableChannel(0, True)
        self.ain.enableChannel(1, True) # Activation Channel 2
        
        # Acquisition d'astuces : on lit des blocs de ~33ms pour 30 FPS réels
        samples_to_read = int(self.sample_rate / 30)
        
        self.worker_thread = DataAcquisitionThread(self.ain, samples_to_read, callback)
        self.worker_thread.connection_lost.connect(self.connection_lost.emit)
        self.worker_thread.start()
        print(f"M2kController: Acquisition démarrée en arrière-plan ({self.sample_rate} SPS effectifs).")

    def disconnect_device(self):
        if self.worker_thread:
            self.worker_thread.stop()
            self.worker_thread = None
            
        try:
            if self.aout:
                self.aout.enableChannel(0, False)
            if self.ain:
                self.ain.enableChannel(0, False)
                self.ain.enableChannel(1, False)
        except Exception as e:
            print("Avertissement lors de la désactivation des canaux:", e)

        try:
            if self.ctx:
                libm2k.contextClose(self.ctx)
        except Exception as e:
            print("Avertissement lors de la fermeture du contexte:", e)

        self.ctx = None
        self.aout = None
        self.ain = None
        print("M2kController: Déconnecté proprement.")
