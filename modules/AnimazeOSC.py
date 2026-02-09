import os
import subprocess
import time
import asyncio
from pythonosc import udp_client
from pythonosc.udp_client import SimpleUDPClient
from modules.module import Module
from typing import Dict, Any, Optional, Tuple, Callable


# --- CONFIGURATION ET CHEMINS ---
# Assurez-vous que ce chemin est correct pour votre installation Animaze
ANIMAZE_PATH = "G:\\Steam\\steamapps\\common\\Animaze\\Bin\\AnimazeDesktop.exe"
ANIMAZE_PROCESS_NAME = "AnimazeDesktop.exe"
IP = "127.0.0.1"
PORT = 9000 
OSC_CLIENT = SimpleUDPClient(IP, PORT) 


# --- FONCTIONS EXTERNES DE LANCEMENT ---

def _is_animaze_running():
    """Vérifie si le processus Animaze est déjà lancé."""
    try:
        tasks = subprocess.check_output("tasklist", text=True)
        return ANIMAZE_PROCESS_NAME in tasks
    except Exception as e:
        print(f"[Animaze Check Error] Échec de la vérification du processus : {e}")
        return False


def launch_animaze():
    """Tente de lancer Animaze depuis le chemin spécifié."""
    if _is_animaze_running():
        print(f"[{time.strftime('%H:%M:%S')}] [ANIMAZE LAUNCHER] Avertissement: Animaze est déjà en cours d'exécution.")
        return True 
        
    if not os.path.exists(ANIMAZE_PATH):
        print(f"[{time.strftime('%H:%M:%S')}] [ANIMAZE LAUNCHER] ERREUR CRITIQUE: Exécutable Animaze introuvable à : {ANIMAZE_PATH}")
        return False 
        
    try:
        subprocess.Popen([ANIMAZE_PATH], close_fds=True)
        print(f"[{time.strftime('%H:%M:%S')}] [ANIMAZE LAUNCHER] Succès: Lancement de Animaze VÉRIDIQUE.")
        time.sleep(5) 
        return True
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] [ANIMAZE LAUNCHER] ERREUR: Échec du lancement de Animaze: {e}")
        return False


# --- MAPPAGE DES ÉMOTIONS ---

EMOTION_MAPPING = {
    "happy": "/Animaze/Set/Exp/Joy",
    "sad": "/Animaze/Set/Exp/Sadness",
    "angry": "/Animaze/Set/Exp/Anger",
    "surprised": "/Animaze/Set/Exp/Surprise",
    "playful": "/Animaze/Set/Exp/Disgust",
    "anxious": "/Animaze/Set/Exp/Disbelief",
    "gentle": "/Animaze/Set/Exp/Neutral",
    "default": "/Animaze/Set/Exp/Neutral",
    "flirty": "/Animaze/Set/Exp/Happy" # ⬅️ CORRECTION: Mappage pour l'émotion par défaut du mode stream
}


class AnimazeOSC(Module):
    def __init__(self, signals, enabled=True):
        super().__init__(signals, enabled)
        self.API = self.API(self)
        self.client = OSC_CLIENT
        self.connected = True # ⬅️ CORRECTION: L'interrupteur est sur ON pour le Prompter
        print(f"✨ Animaze OSC Module initialisé. IP:{IP}, Port:{PORT}")


    def send_osc_command(self, address: str, value: float):
        """Envoie une commande OSC à Animaze."""
        if self.enabled and self.connected:
            try:
                OSC_CLIENT.send_message(address, value)
            except Exception as e:
                # Si l'erreur se produit ici, c'est qu'Animaze n'est pas prêt.
                print(f"[Animaze OSC Error] Failed to send {address}: {e}")

    # ⬅️ CORRECTION AVANCÉE: Rendre cette méthode synchrone pour éviter les problèmes de threading/asyncio
    def send_hotkey(self, emotion: str):
        """Traduit l'émotion CLIO en expression Animaze (SYNCHRONE)."""
        address = EMOTION_MAPPING.get(emotion.lower())
        
        if address:
            # 1. Active l'émotion demandée à fond (1.0)
            self.send_osc_command(address, 1.0)
            # 2. Règle immédiatement au neutre (0.0). Le temps de la transition est géré par Animaze.
            self.send_osc_command(address, 0.0) 
        else:
            print(f"[Animaze] Emotion '{emotion}' non mappée.")

    # ⬅️ set_mouth_open est laissé comme une méthode vide mais synchrone
    def set_mouth_open(self, state: bool):
        """Contrôle l'ouverture de la bouche."""
        if self.enabled:
            # Pour l'OSC, l'ouverture de bouche est souvent gérée par le suivi audio dans Animaze.
            # L'appel est maintenu pour la compatibilité avec speak_with_mouth.
            pass

    async def run(self):
        # Ce module reste en vie pour répondre aux appels d'API du Prompter
        while not self.signals.terminate:
            await asyncio.sleep(1)

    # ⬅️ CORRECTION: La classe API appelle maintenant les méthodes directement (synchrone)
    class API:
        def __init__(self, outer): self.outer = outer
        
        def send_hotkey(self, emotion: str):
            # Appel synchrone direct à la méthode corrigée
            self.outer.send_hotkey(emotion) 

        def set_mouth_open(self, state: bool):
            # Appel synchrone direct
            self.outer.set_mouth_open(state)