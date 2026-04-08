import libm2k
import numpy as np
import time

# 1. Connexion à l'ADALM2000
ctx = libm2k.m2kOpen()
if ctx is None:
    print("Erreur : Impossible de trouver l'ADALM2000. Vérifiez le câble USB.")
    exit(1)

print("ADALM2000 connecté. Calibrage en cours...")
ctx.calibrateDAC()

# 2. Configuration du générateur (Canal 0 correspond à W1)
aout = ctx.getAnalogOut()

# Une fréquence de 400 kSPS est parfaite : elle nous donne exactement 
# 10 points par cycle pour une fréquence de 40 kHz.
sample_rate = 400000 
aout.setSampleRate(0, sample_rate)

# 3. Création du signal de base (une boucle d'exactement 1 seconde)
# Fréquence d'échantillonnage de 400 kSPS : 1 seconde = 400 000 points.
print("Génération du signal de 1 seconde en mémoire...")
t = np.linspace(0, 1.0, sample_rate, endpoint=False)
wave = np.zeros(sample_rate)

# L'onde sinusoïdale de 40 kHz est active pendant les 650 premières millisecondes
idx_650ms = int(sample_rate * 0.65)
wave[:idx_650ms] = 0.03 * np.sin(2 * np.pi * 40000 * t[:idx_650ms]) # Amplitude 0.03V

# On charge le signal entier de 1 seconde dans le buffer en mode cyclique
# Le matériel répètera cette séquence 1 seconde en boucle sans intervention de Python
aout.setCyclic(True)
aout.enableChannel(0, True)
aout.push(0, wave)

print("Signal généré par le matériel en boucle.")

# 4. Configuration de l'oscilloscope (Lecture)
import matplotlib.pyplot as plt
import time

ain = ctx.getAnalogIn()
ain.setSampleRate(sample_rate)
ain.enableChannel(0, True)

print("\n--- OSCILLOSCOPE EN DIRECT ---")
print("Ouverture de la fenêtre graphique en mode temps réel...")
print("Fermez la fenêtre ou faites Ctrl+C pour arrêter le programme.")

# Mode interactif de Matplotlib pour animer la courbe sans bloquer
plt.ion()
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
fig.suptitle("Oscilloscope Virtuel en Direct - M2K")

# 4.1. Paramétrage de la Macro Vue
samples_to_read = int(sample_rate * 0.5) # fenêtres de 500ms
t_plot = np.linspace(0, 0.5, samples_to_read, endpoint=False)

line1, = ax1.plot(t_plot, np.zeros(samples_to_read), color="#1f77b4")
ax1.set_xlim(0, 0.5)
ax1.set_title("Vue Globale (Aperçu du cycle 650ms/350ms)")
ax1.set_xlabel("Temps (s)")
ax1.set_ylabel("Tension (V)")
ax1.grid(True)

# 4.2 Paramétrage de la Micro Vue (Autoset X sur le signal 40kHz)
# 1 période = 25µs. On affiche 10 périodes (250µs = 0.00025 s)
zoom_time = 0.00025
zoom_samples = int(sample_rate * zoom_time)
t_zoom = t_plot[:zoom_samples]

line2, = ax2.plot(t_zoom, np.zeros(zoom_samples), color="#ff7f0e", linewidth=2)
ax2.set_xlim(0, zoom_time)
ax2.set_title("Vue Zoom 'Autoset' (10 périodes de 40kHz stabilisées par Trigger-Logiciel)")
ax2.set_xlabel("Temps (s)")
ax2.set_ylabel("Tension (V)")
ax2.grid(True)

plt.tight_layout()
plt.show(block=False)

try:
    while plt.fignum_exists(fig.number):
        # 1. Capture continue d'une demi-seconde
        data = ain.getSamples(samples_to_read)
        y_data = np.array(data[0])
        
        # --- Trigger logiciel pour stabiliser l'image du zoom ---
        # On cherche le moment où le signal dépasse 10mV en montant (Début d'onde)
        trigger_idx = 0
        for i in range(1, len(y_data) - zoom_samples):
            if y_data[i-1] < 0.01 and y_data[i] >= 0.01:
                trigger_idx = i
                break # On coupe au premier front montant trouvé
                
        # 2. Mise à jour des lignes
        line1.set_ydata(y_data)
        line2.set_ydata(y_data[trigger_idx:trigger_idx + zoom_samples])
        
        # 3. Autoset Y dynamique pour les deux graphiques
        min_y = np.min(y_data)
        max_y = np.max(y_data)
        margin = max((max_y - min_y) * 0.15, 0.005) # Marge d'au moins 5mV
        
        ax1.set_ylim(min_y - margin, max_y + margin)
        ax2.set_ylim(min_y - margin, max_y + margin)
        
        # 4. Rafraîchissement graphique
        fig.canvas.draw_idle()
        fig.canvas.flush_events()
        
        time.sleep(0.02) # Petite pause pour laisser respirer le processeur

except KeyboardInterrupt:
    print("\nArrêt demandé par l'utilisateur.")
except Exception as e:
    pass

# Nettoyage
plt.ioff()
aout.enableChannel(0, False)
ain.enableChannel(0, False)
libm2k.contextClose(ctx)
print("Matériel libéré proprement.")