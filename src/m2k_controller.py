import libm2k
import numpy as np
import time
from PyQt6.QtCore import QObject, pyqtSignal, QThread

class DataAcquisitionThread(QThread):
    # Utilisation de 'object' pour passer les numpy array rapidement sans copies
    data_ready = pyqtSignal(object)

    def __init__(self, ain, samples_to_read):
        super().__init__()
        self.ain = ain
        self.samples_to_read = samples_to_read
        self.running = False

    def run(self):
        self.running = True
        # On fragmente la lecture pour ne pas bloquer le GIL (Python) pendant de longues périodes.
        # Des lectures de 10ms (4000 pour 400kSPS) permettent à l'UI PyQt de s'actualiser sans freeze !
        chunk_size = 4000 
        chunks_ch1 = []
        chunks_ch2 = []
        accumulated = 0
        
        while self.running:
            try:
                # Lecture matérielle bloquante et rapide
                data = self.ain.getSamples(chunk_size)
                
                if data and len(data) > 0 and len(data[0]) > 0:
                    chunks_ch1.append(data[0])
                    # S'il y a un 2e canal activé
                    if len(data) > 1 and len(data[1]) > 0:
                        chunks_ch2.append(data[1])
                    else:
                        chunks_ch2.append(np.zeros(len(data[0]))) # Fallback si pb

                    accumulated += len(data[0])
                    
                    # On émet quand on a nos 0.1s de données
                    if accumulated >= self.samples_to_read:
                        y_data_ch1 = np.concatenate(chunks_ch1)
                        y_data_ch2 = np.concatenate(chunks_ch2)
                        # Retourne un tuple (ch1, ch2)
                        self.data_ready.emit((y_data_ch1, y_data_ch2))
                        chunks_ch1 = []
                        chunks_ch2 = []
                        accumulated = 0
                
                # TRÈS IMPORTANT : Libérer explicitement le GIL pour laisser le thread PyQt dessiner
                time.sleep(0.001)
                
            except Exception as e:
                print("Erreur de lecture dans le thread:", e)
                break
                
    def stop(self):
        self.running = False
        self.wait()

class M2kController(QObject):
    def __init__(self):
        super().__init__()
        self.ctx = None
        self.aout = None
        self.ain = None
        self.sample_rate = 400000
        self.worker_thread = None

    def connect_device(self):
        print("M2kController: Connexion à l'ADALM2000...")
        self.ctx = libm2k.m2kOpen()
        if self.ctx is None:
            raise ConnectionError("Impossible de trouver l'ADALM2000. Fermez Scopy et vérifiez le câble USB.")
        
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
        
    def start_acquisition(self, callback):
        if not self.ctx:
            return

        self.ain.setSampleRate(self.sample_rate)
        self.ain.enableChannel(0, True)
        self.ain.enableChannel(1, True) # Activation Channel 2
        
        # Acquisition d'astuces : on lit des blocs de 0.1s pour Fluidité et Réactivité
        samples_to_read = int(self.sample_rate * 0.1)
        
        self.worker_thread = DataAcquisitionThread(self.ain, samples_to_read)
        self.worker_thread.data_ready.connect(callback)
        self.worker_thread.start()
        print("M2kController: Acquisition démarrée en arrière-plan.")

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
