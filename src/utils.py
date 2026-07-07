
import csv
import os
import threading
import pyttsx3
from datetime import datetime
import time

# Un verrou pour empêcher plusieurs voix de se lancer en même temps
voice_lock = threading.Lock()

def _say_task(message):
    # Si le verrou est déjà pris par une autre alerte, on ignore celle-ci
    if not voice_lock.locked():
        with voice_lock:
            try:
                engine = pyttsx3.init()
                engine.setProperty('rate', 160)
                engine.say(message)
                engine.runAndWait()
                engine.stop()
            except Exception as e:
                print(f"Erreur Audio : {e}")

def speak(message):
    """Lance la voix dans un thread séparé avec protection."""
    t = threading.Thread(target=_say_task, args=(message,), daemon=True)
    t.start()

def log_to_csv(path, event, score):
    """Enregistre les événements dans un fichier CSV pour les statistiques."""
    file_exists = os.path.isfile(path)
    with open(path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Heure", "Evenement", "Valeur"])
        writer.writerow([datetime.now().strftime("%H:%M:%S"), event, round(score, 3)])
