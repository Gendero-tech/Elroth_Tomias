import cv2
import numpy as np
import os
import time
import pygetwindow as gw
import random
from PIL import ImageGrab

class ClioTrainer:
    def __init__(self):
        # Configuration des profils de jeux
        self.games_config = {
            "Warframe": {"keyword": "Warframe", "interval": 1, "info": "Nidus"},
            "BackpackBattles": {"keyword": "Backpack Battles", "interval": 2, "info": "Pyromancer"}
        }
        self.base_path = "training_data"

    def detect_active_game(self):
        """ Détecte quel jeu est actuellement au premier plan """
        active_window = gw.getActiveWindow()
        if not active_window or not active_window.title:
            return None, None

        title = active_window.title
        for game_id, config in self.games_config.items():
            if config["keyword"].lower() in title.lower():
                return game_id, config
        return None, None

    def collect_frames(self, target_count=1000):
        print("🚀 CLIO VISION : Système d'auto-détection activé.")
        print("💡 J'attends que tu lances Warframe ou Backpack Battles...")
        
        count = 0
        try:
            while count < target_count:
                game_id, config = self.detect_active_game()
                
                if game_id:
                    # Création dynamique du dossier
                    save_path = f"{self.base_path}/{game_id}"
                    if not os.path.exists(save_path):
                        os.makedirs(save_path)

                    # Capture
                    screenshot = ImageGrab.grab()
                    frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                    
                    # Sauvegarde
                    timestamp = int(time.time())
                    file_name = f"{save_path}/frame_{game_id}_{config['info']}_{timestamp}_{count}.jpg"
                    cv2.imwrite(file_name, frame)
                    
                    count += 1
                    print(f"📸 [{count}/{target_count}] Apprentissage sur : {game_id} | Profil : {config['info']}")
                    time.sleep(config["interval"])
                else:
                    print("💤 Aucun jeu supporté détecté au premier plan. En pause...", end="\r")
                    time.sleep(3)

        except KeyboardInterrupt:
            print(f"\n🛑 Session interrompue. {count} images prêtes.")

if __name__ == "__main__":
    trainer = ClioTrainer()
    trainer.collect_frames(target_count=1000)