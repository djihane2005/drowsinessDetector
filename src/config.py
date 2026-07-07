import os

class Config:
    # --- Seuils de Détection  ---
    EAR_THRESHOLD           = 0.22
    EAR_CONSEC_FRAMES       = 40   # Nombre d'images pour valider la fermeture
    MAR_THRESHOLD           = 0.65
    MAR_CONSEC_FRAMES       = 30    # Nombre d'images pour valider un bâillement
    
    # --- Couleurs BGR (Interface) ---
    COLOR_SAFE    = (0, 220, 80)    # Vert
    COLOR_WARNING = (0, 165, 255)   # Orange
    COLOR_DANGER  = (0, 0, 220)     # Rouge
    
    # --- Chemins des Fichiers ---
    BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MODEL_PATH = os.path.join(BASE_DIR, "models", "face_landmarker.task")
    CSV_PATH   = os.path.join(BASE_DIR, "rapport_fatigue.csv")
    
    # --- URL du modèle 
    MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"