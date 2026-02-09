import keyboard
import threading
import time
import sys
import os
from typing import Dict, Tuple, Union, List, Callable

# --- ÉTAT GLOBAL DE SÉCURITÉ ---
# Ce drapeau sera mis à jour par le hotkey et sera lu par l'exécution du hotkey
CONTROL_LOCK_STATUS = False 

# --- CORRECTION ARCHITECTURALE : Importation des API des modules ---
try:
    # 🚨 MISE À JOUR DU MOCK CONTROL : Ajout de la fonction lock_control
    class CONTROL_API_MOCK:
        def type_key(self, key_str, delay=0.01):
            print(f"⌨️ [ACTION] Frappe de touche: {key_str}")
        def execute_sequence(self, sequence):
             print(f"⚙️ [MACRO] Exécution de séquence (Total {len(sequence)} étapes)...")
        def lock_control(self, status: bool):
            """Simule la fonction lock_control du ControlModule réel."""
            global CONTROL_LOCK_STATUS
            CONTROL_LOCK_STATUS = status
            print(f"🔒 [SÉCURITÉ] CONTRÔLE {('VERROUILLÉ' if status else 'DÉVERROUILLÉ')}")

    class TTS_API_MOCK:
        def speak(self, text, style): 
            print(f"🔊 [{style.upper()}]: {text}")
    
    tts_api = TTS_API_MOCK()
    control_api = CONTROL_API_MOCK()

except ImportError as e:
    print(f"ERREUR: Impossible d'importer les modules nécessaires: {e}. Exécution impossible.")
    sys.exit(1)


# --- DÉFINITION DES HOTKEYS ENRICHIS ---

# La valeur est un tuple (texte_ou_action, style_ou_touche, type_action)
# Type d'action: 'SPEAK', 'KEY', 'MACRO', 'TOGGLE_LOCK'

HOTKEY_MAP: Dict[str, Tuple[str, str, str]] = {
    # 1. Réactions Vocales Simples
    "ctrl+1": ("Bonjour Ambre, je suis là pour toi 💙", "gentle", "SPEAK"),
    "ctrl+2": ("Oh non... tu viens de rater ton saut. Accroche-toi ! 😥", "anxious", "SPEAK"),
    "ctrl+3": ("Bravo ! Tu gères ! 🥳", "happy", "SPEAK"),
    
    # 2. Macros d'Action Rapide (Utile pour les jeux)
    "alt+4": ("4", "type_key", "KEY"),
    
    # 🚨 NOUVEAU HOTKEY DE SÉCURITÉ
    "ctrl+alt+k": ("Clio, verrouillage des commandes clavier/souris !", "firm", "TOGGLE_LOCK"), 
    
    # Exemple: Demander le scan de jeux
    "ctrl+s": ("commande neuro scan_for_games()", "chat", "SPEAK_AND_DELEGATE"),
}

# --- FONCTION D'EXÉCUTION DU HOTKEY ---

def execute_hotkey_action(data: str, style_or_key: str, action_type: str):
    """Gère l'exécution des différents types de hotkeys."""
    global CONTROL_LOCK_STATUS

    if action_type == "SPEAK":
        tts_api.speak(data, style=style_or_key)
        
    elif action_type == "KEY" or action_type == "MACRO":
        # Verrouillage de sécurité : N'exécute PAS les entrées clavier/souris si verrouillé
        if CONTROL_LOCK_STATUS:
             tts_api.speak("Le contrôle clavier/souris est verrouillé, Maman.", style="worry")
             return

        if action_type == "KEY":
            control_api.type_key(data, delay=0.05)
        elif action_type == "MACRO":
            try:
                # 🚨 ATTENTION : Utilisation d'eval()
                sequence = eval(data) 
                if isinstance(sequence, list):
                    control_api.execute_sequence(sequence)
            except Exception as e:
                print(f"ERREUR MACRO: Impossible d'exécuter la séquence {data}. {e}")
            
    elif action_type == "SPEAK_AND_DELEGATE":
        # Les actions vocales/délégation (comme VTS) sont toujours permises même en mode verrouillé
        tts_api.speak(f"J'exécute ta commande de délégation: {data}", style="gentle")
        print(f"DELEGATION BUFFER: {data}")
        
    elif action_type == "TOGGLE_LOCK":
        # Inverse l'état de verrouillage
        new_status = not CONTROL_LOCK_STATUS
        control_api.lock_control(new_status)
        tts_api.speak(f"Commandes Clavier/Souris {'déverrouillées' if new_status else 'verrouillées'}.", style="firm")


def start_hotkey_listener():
    """Configure et démarre l'écoute des hotkeys."""
    print(f"CLIO 🎧 Écoute de {len(HOTKEY_MAP)} hotkeys... (Échap pour quitter)")

    # 1. Enregistrement des hotkeys
    for key, (data, style_or_key, action_type) in HOTKEY_MAP.items():
        keyboard.add_hotkey(
            key, 
            lambda d=data, s=style_or_key, a=action_type: execute_hotkey_action(d, s, a)
        )

    # 2. Blocage du thread jusqu'à la touche 'esc'
    try:
        keyboard.wait("esc")
    except KeyboardInterrupt:
        pass
    finally:
        print("Arrêt de l'écoute des hotkeys.")
        # Nettoyage final
        control_api.release_all()


if __name__ == "__main__":
    start_hotkey_listener()