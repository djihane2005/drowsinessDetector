import cv2
import mediapipe as mp
import numpy as np
from scipy.spatial import distance as dist
from .config import Config
from .utils import speak
import time

class DrowsinessDetector:
    def __init__(self):
        self.cfg = Config()
        # Initialisation du Landmarker de MediaPipe
        from mediapipe.tasks.python import vision
        options = vision.FaceLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=self.cfg.MODEL_PATH),
            running_mode=vision.RunningMode.IMAGE,
            num_faces=1
        )
        self.landmarker = vision.FaceLandmarker.create_from_options(options)
        
        # Compteurs pour filtrer les faux positifs (clignotements rapides)
        self.eye_counter = 0
        self.mouth_counter = 0
        self.last_alert_time = 0  # Timestamp pour gérer le délai entre deux alertes vocales

    def calculate_ear(self, pts):
        """Calcule l'Eye Aspect Ratio (EAR) pour détecter la fermeture des yeux."""
        v1 = dist.euclidean(pts[1], pts[5])
        v2 = dist.euclidean(pts[2], pts[4])
        h = dist.euclidean(pts[0], pts[3])
        return (v1 + v2) / (2.0 * h + 1e-6)

    def process_frame(self, frame):
        h, w, _ = frame.shape
        # 1. Prétraitement de l'image
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        result = self.landmarker.detect(mp_image)
        
        # Valeurs par défaut
        status, color = "NORMAL", self.cfg.COLOR_SAFE
        head_ratio = 0.0
        ear = 0.30  # Valeur neutre (yeux ouverts)
        mar = 0.10  # Valeur neutre (bouche fermée)
        now = time.time()

        if result.face_landmarks:
            landmarks = result.face_landmarks[0]
            # Fonction utilitaire pour convertir les points normalisés en pixels
            def get_pt(idx): return np.array([landmarks[idx].x * w, landmarks[idx].y * h])

            # --- A. CALCUL DES RATIOS ---

            # 1. YEUX (Points spécifiques MediaPipe pour l'EAR)
            left_eye = [get_pt(i) for i in [362, 385, 387, 263, 373, 380]]
            right_eye = [get_pt(i) for i in [33, 160, 158, 133, 153, 144]]
            ear = (self.calculate_ear(left_eye) + self.calculate_ear(right_eye)) / 2.0

            # 2. BOUCHE (Mouth Aspect Ratio - MAR pour le bâillement)
            m_top, m_bottom = get_pt(13), get_pt(14)
            m_left, m_right = get_pt(78), get_pt(308)
            mar = dist.euclidean(m_top, m_bottom) / (dist.euclidean(m_left, m_right) + 1e-6)

            # 3. TÊTE (Inclinaison verticale)
            eye_mid_y = (get_pt(159)[1] + get_pt(386)[1]) / 2.0
            nose_tip_y = get_pt(1)[1]
            face_height = dist.euclidean(get_pt(10), get_pt(152))
            head_ratio = (nose_tip_y - eye_mid_y) / face_height

            # --- B. LOGIQUE DE DÉTECTION (Multi-niveaux) ---

            # PRIORITÉ 1 : SOMMEIL (YEUX FERMÉS)
            if ear < self.cfg.EAR_THRESHOLD:
                self.eye_counter += 1
                if self.eye_counter >= self.cfg.EAR_CONSEC_FRAMES:
                    status, color = "DANGER : SOMMEIL", self.cfg.COLOR_DANGER
                    if now - self.last_alert_time > 4:
                        speak("Attention ! Réveillez-vous")
                        self.last_alert_time = now
            else:
                self.eye_counter = 0

                # PRIORITÉ 2 : TÊTE BASSE (Si les yeux sont ouverts mais la tête tombe)
                if head_ratio > 0.30: 
                    status, color = "DANGER : TETE BASSE", self.cfg.COLOR_DANGER
                    if now - self.last_alert_time > 4:
                        speak("Redressez la tête")
                        self.last_alert_time = now
                
                # PRIORITÉ 3 : BÂILLEMENT (Signe de fatigue légère)
                elif mar > self.cfg.MAR_THRESHOLD:
                    self.mouth_counter += 1
                    if self.mouth_counter >= self.cfg.MAR_CONSEC_FRAMES:
                        status, color = "WARNING : BAILLEMENT", self.cfg.COLOR_WARNING
                        # On peut ajouter un son de bip léger ici si nécessaire
                else:
                    self.mouth_counter = 0

        # --- C. AFFICHAGE DES INFOS (DEBUG) ---
        # Affichage des ratios en temps réel sur l'écran
        cv2.putText(frame, f"EAR: {round(ear, 2)}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"MAR: {round(mar, 2)}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Head: {round(head_ratio, 2)}", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return frame, {"status": status, "color": color}