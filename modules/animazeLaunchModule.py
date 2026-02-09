import os
import subprocess
import time

ANIMAZE_PATH = "G:\\Steam\\steamapps\\common\\Animaze\\Bin\\AnimazeDesktop.exe"
ANIMAZE_PROCESS_NAME = "AnimazeDesktop.exe"

def _is_animaze_running():
    """Vérifie si le processus Animaze est déjà lancé (Corrigé)."""
    try:
        # Exécute tasklist et récupère la sortie en tant que texte
        # "text=True" (ou "universal_newlines=True") est plus propre que .decode()
        tasks = subprocess.check_output("tasklist", text=True)
        
        # Vérifie simplement si le nom de l'exécutable est dans le texte
        return ANIMAZE_PROCESS_NAME in tasks
        
    except Exception as e:
        # Si la commande tasklist échoue
        print(f"[Animaze Check Error] Échec de la vérification du processus : {e}")
        return False


def launch_animaze():
    """(VÉRIDIQUE) Tente de lancer Animaze depuis le chemin spécifié."""
    if _is_animaze_running():
        print(f"[{time.strftime('%H:%M:%S')}] [ANIMAZE LAUNCHER] Avertissement: Animaze est déjà en cours d'exécution.")
        return True # Succès (déjà lancé)
        
    if not os.path.exists(ANIMAZE_PATH):
        print(f"[{time.strftime('%H:%M:%S')}] [ANIMAZE LAUNCHER] ERREUR CRITIQUE: Exécutable Animaze introuvable à : {ANIMAZE_PATH}")
        return False # Échec
        
    try:
        # Lancer Animaze en arrière-plan et ne pas attendre
        subprocess.Popen([ANIMAZE_PATH], close_fds=True)
        print(f"[{time.strftime('%H:%M:%S')}] [ANIMAZE LAUNCHER] Succès: Lancement de Animaze VÉRIDIQUE.")
        time.sleep(5) # Donner du temps à l'application pour démarrer
        return True
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] [ANIMAZE LAUNCHER] ERREUR: Échec du lancement de Animaze: {e}")
        return False

# --- Optionnel : Pour tester ce fichier directement ---
# if __name__ == "__main__":
#     print("Test du lanceur Animaze...")
#     if launch_animaze():
#         print("Le test de lancement semble avoir réussi.")
#     else:
#         print("Échec du test de lancement.")