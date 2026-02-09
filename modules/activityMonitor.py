# Fichier : modules/activityMonitor.py - VERSION FINALE OPTIMISÉE POUR RÉFLEXES
import os
import psutil
import time
import asyncio
from modules.module import Module
from typing import Dict, List, Any
import logging

logger = logging.getLogger('ActivityMonitor')

# --- CONFIGURATION ---
CHECK_INTERVAL: int = 5 

# Programmes que Clio doit reconnaître pour adapter son comportement
KNOWN_GAMES: Dict[str, str] = {
    "warframe.exe": "warframe",
    "backpack_battles.exe": "backpack",
    "eldenring.exe": "Elden Ring",
    "bg3.exe": "Baldur's Gate 3",
    "genshinimpact.exe": "Genshin Impact",
    "starrail.exe": "Star Rail",
    "league of legends.exe": "League of Legends",
    "steam.exe": "Steam",
    "minecraft.exe": "Minecraft",
    "balatro.exe": "Balatro",
}

KNOWN_MEDIA: Dict[str, str] = {
    "vlc.exe": "VLC",
    "mpv.exe": "MPV Player",
    "netflix.exe": "Netflix",
    "crunchyroll.exe": "Crunchyroll",
    "discord.exe": "Discord",
    "chrome.exe": "Chrome",
    "firefox.exe": "Firefox",
}

class ActivityMonitor(Module):
    def __init__(self, signals, modules: Dict[str, Any] = None, enabled: bool = True):
        super().__init__(signals, enabled)
        self.modules = modules if modules is not None else {}
        self.vision = self.modules.get('vision')
        self.session_manager = self.modules.get('session_manager')
        
        self.current_activity: str = "idle"
        self.microphone_status: str = "libre" 
        self.API = self.API(self) 

    def check_processes_and_window(self) -> str:
        """Détermine l'activité et met à jour le signal de jeu pour les réflexes."""
        if not self.enabled:
             return "idle"
             
        process_names: List[str] = [
            p.info['name'].lower() 
            for p in psutil.process_iter(['name']) 
            if p.info['name'] is not None
        ]
        
        # 1. Priorité aux Jeux (et mise à jour du signal de jeu)
        detected_game_key = "none"
        activity_str = "idle"

        for name in process_names:
            if name in KNOWN_GAMES:
                detected_game_key = KNOWN_GAMES[name]
                activity_str = f"en train de jouer à {detected_game_key}"
                break
        
        # Mise à jour du signal global pour le ReflexEngine et VisionModule
        if self.signals.current_game != detected_game_key:
            self.signals.current_game = detected_game_key
        
        if activity_str != "idle":
            return activity_str

        # 2. Médias / Navigation
        for name in process_names:
            if name in KNOWN_MEDIA:
                return f"en train de regarder {KNOWN_MEDIA[name]}"
        
        return "idle"
        
    def _get_active_window_title(self) -> str:
        """Utilise le module Vision pour obtenir le contexte précis."""
        if self.vision and hasattr(self.vision, 'API'):
            try:
                return self.vision.API.get_active_window_title()
            except Exception:
                return "Erreur lecture titre"
        return "VisionModule indisponible"

    async def run(self):
        logger.info("💡 Moniteur d'activité démarré (Détection de Jeu Active)")
        
        while not self.signals.terminate:
            await asyncio.sleep(CHECK_INTERVAL) 
            
            if not self.enabled:
                continue

            loop = asyncio.get_event_loop()
            new_activity = await loop.run_in_executor(None, self.check_processes_and_window)
            
            if new_activity != self.current_activity:
                window_context = self._get_active_window_title() 
                logger.info(f"💡 Activité : {new_activity} | Jeu : {self.signals.current_game}")
                
                # Nettoyage automatique de la mémoire à court terme lors d'un changement d'activité
                if self.session_manager and hasattr(self.session_manager.API, 'clear_session_context'):
                    self.session_manager.API.clear_session_context()
                
                self.current_activity = new_activity
                self.signals.sio_queue.put(("activity_update", {
                    "activity": new_activity, 
                    "game": self.signals.current_game,
                    "window": window_context
                }))

    class API:
        def __init__(self, outer: 'ActivityMonitor'):
            self.outer = outer
        def get_status(self) -> str:
            return self.outer.current_activity
        def get_window_title(self) -> str:
            return self.outer._get_active_window_title()