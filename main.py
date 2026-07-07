import cv2
import customtkinter as ctk
from PIL import Image, ImageTk
import os
import csv
from datetime import datetime
from src.detector import DrowsinessDetector

# Configuration de l'apparence
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class DrowsinessApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Fenêtre principale ---
        self.title("AI Driver Safety System - M1 Informatique")
        self.geometry("1100x700")
        
        # Initialisation du détecteur 
        self.detector = DrowsinessDetector()
        self.video_capture = cv2.VideoCapture(0)
        
        # Variables de statistiques
        self.alert_count = 0
        self.last_status = "NORMAL"
        self.csv_file = "rapport_fatigue.csv"
        self.init_csv()

        # --- Mise en page (Layout) ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Barre Latérale (Sidebar)
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="DASHBOARD", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(pady=30)

        self.status_card = ctk.CTkFrame(self.sidebar, fg_color="#2b2b2b")
        self.status_card.pack(padx=20, pady=10, fill="x")
        
        self.lbl_title_status = ctk.CTkLabel(self.status_card, text="ÉTAT ACTUEL", font=("Roboto", 12))
        self.lbl_title_status.pack(pady=(10, 0))
        
        self.lbl_status = ctk.CTkLabel(self.status_card, text="NORMAL", text_color="#2ecc71", font=("Roboto", 18, "bold"))
        self.lbl_status.pack(pady=10)

        self.lbl_alerts = ctk.CTkLabel(self.sidebar, text=f"Alertes enregistrées : {self.alert_count}", font=("Roboto", 13))
        self.lbl_alerts.pack(pady=20)

        self.btn_quit = ctk.CTkButton(self.sidebar, text="QUITTER", fg_color="#e74c3c", hover_color="#c0392b", command=self.on_closing)
        self.btn_quit.pack(side="bottom", pady=20)

        # 2. Zone Vidéo
        self.video_frame = ctk.CTkFrame(self, fg_color="black")
        self.video_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.video_label = ctk.CTkLabel(self.video_frame, text="")
        self.video_label.pack(expand=True, fill="both")

        # Lancement de la boucle
        self.update_frame()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def init_csv(self):
        """Crée le fichier CSV s'il n'existe pas encore"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Heure", "Type d'Alerte", "Niveau de Risque"])

    def save_to_report(self, status):
        """Enregistre uniquement les changements d'état vers le danger"""
        if "DANGER" in status or "WARNING" in status:
            self.alert_count += 1
            self.lbl_alerts.configure(text=f"Alertes enregistrées : {self.alert_count}")
            
            now = datetime.now()
            with open(self.csv_file, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    now.strftime("%Y-%m-%d"),
                    now.strftime("%H:%M:%S"),
                    status,
                    "HAUT" if "DANGER" in status else "MOYEN"
                ])

    def update_frame(self):
        ret, frame = self.video_capture.read()
        if ret:
            # Appel de ton détecteur 
            processed_frame, info = self.detector.process_frame(frame)
            
            # Récupération des infos
            current_status = info['status']
            current_color_bgr = info['color'] # OpenCV est en BGR
            
            # Conversion BGR vers HEX pour CustomTkinter
            status_color = "#e74c3c" if "DANGER" in current_status else "#f39c12" if "WARNING" in current_status else "#2ecc71"
            
            # Mise à jour de l'UI
            self.lbl_status.configure(text=current_status, text_color=status_color)
            
            # Enregistrement si l'état change vers une alerte
            if current_status != self.last_status:
                self.save_to_report(current_status)
                self.last_status = current_status

            # Transformation de l'image pour l'affichage GUI
            img_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            
            # Redimensionner l'image pour qu'elle tienne dans le cadre
            img_tk = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(800, 500))
            
            self.video_label.configure(image=img_tk)
            self.video_label.image = img_tk

        # Rappeler la fonction toutes les 10ms
        self.after(10, self.update_frame)

    def on_closing(self):
        self.video_capture.release()
        self.destroy()

if __name__ == "__main__":
    app = DrowsinessApp()
    app.mainloop()
