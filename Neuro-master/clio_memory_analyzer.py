import os
import random

class ClioMemoryAnalyzer:
    def __init__(self, game_name):
        self.game_name = game_name
        self.memory_path = f"training_data/{game_name}"
        
    def scan_memory(self):
        """ Vérifie ce que Clio a en mémoire """
        if not os.path.exists(self.memory_path):
            print(f"❌ Erreur : Le dossier {self.memory_path} n'existe pas encore.")
            return

        all_files = [f for f in os.listdir(self.memory_path) if f.endswith('.jpg')]
        print(f"--- 🧠 ANALYSE DE LA MÉMOIRE : {self.game_name} ---")
        print(f"📊 Nombre total d'images capturées : {len(all_files)}")
        
        if len(all_files) > 0:
            # Analyse des tags (si présents dans le nom du fichier)
            tags = {}
            for f in all_files:
                parts = f.split('_')
                if len(parts) > 2:
                    tag = parts[2] # Récupère l'info (ex: Nidus ou Pyromancer)
                    tags[tag] = tags.get(tag, 0) + 1
            
            print(f"🏷️ Répartition des profils détectés :")
            for t, count in tags.items():
                print(f"   - {t} : {count} images")
            
            # Simulation d'un souvenir aléatoire
            random_shot = random.choice(all_files)
            print(f"✨ Souvenir aléatoire sélectionné : {random_shot}")
        
        print("--- FIN DE L'ANALYSE ---")

if __name__ == "__main__":
    # On lance l'analyse pour le dossier de ton choix
    analyzer = ClioMemoryAnalyzer("BackpackBattles")
    analyzer.scan_memory()