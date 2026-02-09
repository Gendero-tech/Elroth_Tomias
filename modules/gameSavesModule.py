import os
import shutil
import time # ✅ CORRIGÉ : L'import 'time' est rétabli pour _log_action
import json
import socket
import subprocess
import sys
from typing import Dict, Any, Optional, List, Tuple

# --- CONFIGURATION ET CHEMINS ---

# NOTE VÉRIDIQUE: Ces chemins sont basés sur les disques mentionnés par Ambre
# Le chemin de base pour la recherche inclut désormais G:\
GAME_DRIVES: List[str] = ["G:\\", "E:\\", "C:\\"] # On garde C: et E: pour la recherche, mais on utilise G: comme racine

# ❌ CORRECTION CRITIQUE : Les sauvegardes de Clio sont centralisées sur G:\
CLIO_SAVES_ROOT: str = "G:\\neuro\\Neuro-master\\Clio_GameSaves" 
CONFIG_FILE: str = os.path.join(CLIO_SAVES_ROOT, "game_config.json")

# Chemins de recherche génériques
GENERIC_SCAN_PATHS: List[str] = [
    "Steam\\steamapps\\common",
    "SteamLibrary\\steamapps\\common",
    "EA-Origin",
    "Epic Games",
    "gog",
    "Ubisoft Game Launcher\\games",
    "Users\\derre\\AppData\\Roaming",
    # Chemin spécifique pour le cas de PokemonFusion (à ne pas généraliser)
    "PokemonFusion\\InfiniteFusionFR-6.5.1\\PIFLauncher1.1.2\\PIFLauncher1.1.0\\GameFiles\\InfiniteFusion", 
]

# On s'assure que le dossier racine existe pour la configuration
if not os.path.exists(CLIO_SAVES_ROOT): 
    os.makedirs(CLIO_SAVES_ROOT, exist_ok=True)

# --- FONCTIONS UTILITAIRES ---

def _log_action(message: str):
    """Imprime des messages de log avec horodatage."""
    # Le time.time() est robuste, mais time.strftime est plus lisible dans les logs
    print(f"[{time.strftime('%H:%M:%S')}] [CLIO-SYSTEM] {message}") 
    # (Dans un système réel, on enverrait ceci à un Logger dédié)

def _load_game_config() -> Dict[str, Any]:
    """Charge la configuration JSON."""
    os.makedirs(CLIO_SAVES_ROOT, exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        _log_action(f"Erreur de décodage JSON dans le fichier de config: {CONFIG_FILE}. Retour vide.")
        return {}
    except Exception as e:
        _log_action(f"Erreur lecture config: {e}. Retour vide.")
        return {}

def _save_game_config(config: Dict[str, Any]):
    """Sauvegarde la configuration JSON."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        _log_action(f"Erreur écriture config: {e}")

def _get_game_details(game_name: str) -> Optional[Dict[str, Any]]:
    """
    Récupère la configuration détaillée d'un jeu depuis le fichier.
    Inclut l'install_root s'il a été trouvé.
    """
    config = _load_game_config()
    game_data = config.get(game_name)
    
    if not game_data:
        _log_action(f"Jeu '{game_name}' introuvable dans la configuration.")
        return None
        
    if not game_data.get('install_root'):
        # On retourne quand même les infos connues pour ne pas bloquer l'appelant
        _log_action(f"Chemin d'installation pour '{game_name}' non défini. Lancez scan_for_games().")
    
    return game_data


# --- CONTRÔLE ANIMAZE (OSC) (Inchangé) ---

def _send_osc_idle(active: bool = True):
    """Gestion de l'état d'Animaze via OSC."""
    command = "/idle:1" if not active else "/idle:0" # idle:1 = mode concentration
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(command.encode(), ("127.0.0.1", 9000))
        sock.close()
        state = "IDLE (Concentration)" if not active else "EXPRESSION (Actif)"
        _log_action(f"OSC >> Avatar mis en mode {state}")
    except Exception:
        pass # Silence si Animaze n'est pas là

def send_osc_activate():
    """Rend l'avatar expressif (non idle)."""
    _send_osc_idle(active=True)

def send_osc_idle():
    """Met l'avatar en mode concentré (idle)."""
    _send_osc_idle(active=False)

# --- API PUBLIQUE (Accès pour d'autres modules) ---

def get_game_config_data(game_name: str) -> Optional[Dict[str, Any]]:
    """
    Retourne la configuration complète d'un jeu (executable, search_pattern, 
    save_pattern, install_root).
    Utile pour le BrainModule.
    """
    return _get_game_details(game_name)

# --- SCANNING ET APPRENTISSAGE ---

def add_new_game_to_knowledge(game_name: str, search_pattern: str, executable_name: str, save_pattern_rel: str) -> bool:
    """
    Ajoute un jeu à la mémoire.
    """
    config = _load_game_config()
    clean_name = game_name.strip()
    
    if not clean_name or not search_pattern or not executable_name:
        _log_action("Erreur: Arguments manquants pour l'ajout du jeu.")
        return False

    config[clean_name] = {
        "executable": executable_name,
        "search_pattern": search_pattern,
        "save_pattern": save_pattern_rel, 
        "install_root": None 
    }
    _save_game_config(config)
    _log_action(f"Jeu '{clean_name}' ajouté à la base. Prêt pour le scan.")
    return True

def scan_for_games() -> int:
    """Scanne les disques pour trouver les chemins d'installation."""
    _log_action("Scan des disques en cours...")
    config = _load_game_config()
    found_count = 0
    
    for game_name, game_data in config.items(): 
        # Si le chemin existe déjà et est valide, on passe au suivant
        if game_data.get('install_root') and os.path.exists(game_data['install_root']):
            continue
        
        search_pattern = game_data.get('search_pattern')
        if not search_pattern: continue

        found = False
        for drive in GAME_DRIVES:
            if not os.path.exists(drive): continue
            
            # AMÉLIORATION: L'itération sur GENERIC_SCAN_PATHS est plus propre avec os.path.join
            for pattern in GENERIC_SCAN_PATHS:
                # Filtrage spécifique pour AppData (doit être sur C:)
                # ATTENTION: Cette vérification est basée sur un utilisateur 'derre' dans GENERIC_SCAN_PATHS
                if "AppData" in pattern and drive != "C:\\":
                    continue 
                    
                potential_path = os.path.join(drive, pattern, search_pattern)
                
                # Vérification
                if os.path.isdir(potential_path):
                    config[game_name]['install_root'] = potential_path
                    _log_action(f"TROUVÉ: '{game_name}' détecté dans {potential_path}")
                    found = True
                    found_count += 1
                    break
            if found: break
    
    _save_game_config(config)
    _log_action(f"Fin du scan. {found_count} nouveaux chemins mis à jour.")
    return found_count

# --- CŒUR DU SYSTÈME : GESTIONNAIRE DE SESSION ET SAUVEGARDES ---

def _backup_and_swap_saves(game_name: str, install_root: str, save_rel_path: str) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """
    1. Backup les saves d'Ambre.
    2. Installe les saves de Clio.
    Retourne (succès, backup_path, clio_path, real_path)
    """
    real_save_path: str = os.path.join(install_root, save_rel_path)
    
    # Chemins de stockage Clio
    clio_storage: str = os.path.join(CLIO_SAVES_ROOT, game_name, "Clio_Progress")
    ambre_backup: str = os.path.join(CLIO_SAVES_ROOT, game_name, "Ambre_Backup_Temp")

    # Création des dossiers si inexistants
    os.makedirs(clio_storage, exist_ok=True)
    os.makedirs(ambre_backup, exist_ok=True)

    if not os.path.exists(real_save_path):
        _log_action(f"ATTENTION: Dossier de sauvegarde original introuvable ({real_save_path}). Création d'un nouveau.")
        os.makedirs(real_save_path, exist_ok=True)

    try:
        # ÉTAPE 1 : Sécuriser les données d'Ambre
        if os.path.exists(ambre_backup):
            # Suppression préalable d'un ancien backup temporaire
            shutil.rmtree(ambre_backup) 
            
        # Copie des fichiers actuels (Ambre) vers Backup
        shutil.copytree(real_save_path, ambre_backup)
        _log_action("Sauvegardes d'Ambre sécurisées dans le dossier temporaire.")

        # ÉTAPE 2 : Nettoyer le dossier du jeu (pour éviter les conflits)
        for filename in os.listdir(real_save_path):
            file_path = os.path.join(real_save_path, filename)
            try:
                # Utilisation de os.path.islink pour gérer les liens symboliques
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                _log_action(f"Erreur nettoyage fichier {file_path}: {e}")

        # ÉTAPE 3 : Injecter les sauvegardes de Clio
        # Utilisation de dirs_exist_ok=True est crucial si le dossier Clio est vide/incomplet au premier lancement
        shutil.copytree(clio_storage, real_save_path, dirs_exist_ok=True)
        _log_action("Sauvegardes de Clio injectées. Prête à jouer.")
        
        return True, ambre_backup, clio_storage, real_save_path

    except Exception as e:
        _log_action(f"ERREUR CRITIQUE SWAP: {e}")
        return False, None, None, None

def _restore_saves(real_save_path: str, clio_storage: str, ambre_backup: str):
    """
    1. Sauvegarde la progression de Clio.
    2. Restaure les saves d'Ambre.
    """
    try:
        _log_action("Fin de session. Récupération de la progression de Clio...")
        
        # 1. Sauvegarder la progression de Clio (du jeu vers stockage Clio)
        if os.path.exists(clio_storage):
            # Il faut nettoyer pour garantir que seuls les derniers fichiers sont copiés
            shutil.rmtree(clio_storage) 
        os.makedirs(clio_storage) # Recréer le dossier vide

        # Copie les nouvelles saves de Clio
        shutil.copytree(real_save_path, clio_storage, dirs_exist_ok=True)
        _log_action("Progression de Clio sauvegardée !")

        # 2. Restaurer Ambre
        if os.path.exists(real_save_path):
            # Nettoyer le dossier de jeu avant restauration pour éviter les fichiers résiduels
            shutil.rmtree(real_save_path)
            
        shutil.copytree(ambre_backup, real_save_path)
        _log_action("Environnement restauré pour Ambre. Tout est en ordre.")
        
        # Nettoyage du dossier temporaire
        shutil.rmtree(ambre_backup)

    except Exception as e:
        _log_action(f"ERREUR CRITIQUE RESTAURATION: {e}. Vérifiez manuellement {CLIO_SAVES_ROOT}")


def play_game_as_clio(game_name: str):
    """
    Fonction principale pour lancer une session de jeu complète.
    Gère le swap, le lancement, l'attente et la restauration.
    """
    game_data = _get_game_details(game_name)

    if not game_data or not game_data.get('install_root'):
        _log_action(f"Abandon du lancement: Jeu '{game_name}' non configuré ou chemin d'installation introuvable.")
        return

    install_root: str = game_data['install_root']
    executable: str = game_data['executable']
    save_pattern: str = game_data['save_pattern']
    
    game_exec_path: str = os.path.join(install_root, executable)

    if not os.path.exists(game_exec_path):
        _log_action(f"Erreur: Exécutable introuvable ({game_exec_path})")
        return

    # 1. Swap des sauvegardes
    _log_action(f"Préparation de la session de jeu: {game_name}.")
    success, backup_path, clio_path, real_path = _backup_and_swap_saves(game_name, install_root, save_pattern)
    
    # Vérification et casting car l'étape 4 en a besoin
    if not success or not backup_path or not clio_path or not real_path:
        _log_action("Abandon du lancement pour protéger les données.")
        return

    # 2. Lancement du jeu
    proc: Optional[subprocess.Popen] = None
    try:
        send_osc_idle() # Avatar en mode discret/concentré
        
        _log_action(f"Lancement de {game_name}...")
        # cwd (Current Working Directory) est souvent crucial pour les jeux
        # shell=True est généralement déconseillé pour la sécurité, donc on se fie à Popen avec cwd
        proc = subprocess.Popen([game_exec_path], cwd=install_root, close_fds=True)
        
        _log_action("Jeu lancé. J'attends la fermeture du jeu pour restaurer tes fichiers...")
        
        # 3. ATTENTE ACTIVE (Crucial pour ne pas restaurer trop tôt)
        proc.wait() 
        
        _log_action("Jeu fermé détecté. Fin de session.")

    except Exception as e:
        _log_action(f"Erreur durant l'exécution du jeu: {e}")
    finally:
        # 4. Restauration
        send_osc_activate() # Réveiller l'avatar
        # La vérification de 'success' a été faite plus tôt. Ici, on utilise les chemins trouvés.
        _restore_saves(real_path, clio_path, backup_path) 

# --- EXEMPLE D'UTILISATION (Inchangé) ---

if __name__ == "__main__":
    
    # 1. Définition (A faire une seule fois)
    # add_new_game_to_knowledge("PokemonFusion", "InfiniteFusion", "InfiniteFusion.exe", "SaveFiles")
    
    # 2. Scan (A faire quand on déplace des dossiers)
    # scan_for_games()
    
    # 3. Jouer (La commande magique)
    # play_game_as_clio("PokemonFusion")
    
    # 4. Tester la nouvelle fonction API
    # config = get_game_config_data("PokemonFusion")
    # print(config)
    
    # Exemple pour tester le log :
    # _log_action("Script de gestion de jeu lancé.")
    pass