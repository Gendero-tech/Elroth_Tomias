# Fichier : modules/controlModule.py - VERSION FINALE OPTIMISÉE POUR RÉFLEXES
import asyncio
import logging
import pyautogui
import pydirectinput
import webbrowser
import platform
import os
import time
from typing import Optional, List, Tuple
from modules.module import Module

log = logging.getLogger('ControlModule')

# SÉCURITÉ : Indispensable pour les jeux 3D comme Warframe
pyautogui.FAILSAFE = False 
pydirectinput.FAILSAFE = False

# Configuration OS
ANIME_PLATFORMS = {
    "Crunchyroll": "https://www.crunchyroll.com/fr/videos/free",
    "Wakanim": "https://www.wakanim.tv/fr/v2/catalogue/list/37/gratuit"
}
NETFLIX_URL = "https://www.netflix.com/fr/"

PROGRAM_COMMANDS = {
    "Discord": ("start discord", "open -a Discord", "discord"),
    "Spotify": ("start spotify", "open -a Spotify", "spotify"),
    "Calculatrice": ("calc", "open -a Calculator", "gnome-calculator"),
    "BlocNotes": ("notepad", "open -a TextEdit", "gedit")
}
CURRENT_OS = platform.system()

class ControlModule(Module):
    def __init__(self, signals, modules, enabled=True):
        super().__init__(signals, enabled)
        self.modules = modules
        self.API = self.API(self)
        
        self.brain_module = self.modules.get("brain")
        self.human_override = False        
        self.clio_has_direct_control = True # Activé par défaut pour les réflexes
        self.control_locked = False          
        self.mouse_input_blocked = False
        
        self._keys_down = set()
        self._mouse_buttons_down = set()
        self._last_command_time = time.time()
        self._input_debounce_ms = 20 # Réduit pour plus de nervosité en jeu

    async def run(self):
        log.info("✋ Module de Contrôle (Mains) prêt pour Warframe & Backpack Battles.")
        while not self.signals.terminate:
            await asyncio.sleep(1)

    def _should_execute(self) -> bool:
        if self.control_locked: return False
        current_time = time.time()
        if (current_time - self._last_command_time) * 1000 < self._input_debounce_ms:
            return False
        self._last_command_time = current_time
        return True

    def _check_direct_control(self) -> bool:
        if not self.clio_has_direct_control and not self.human_override:
            return False
        return True

    # --- MÉTHODES CLAVIER ---
    def type_key(self, key: str):
        if not self._check_direct_control() or not self._should_execute(): return
        try:
            pydirectinput.press(key.lower())
        except:
            pyautogui.press(key.lower())

    def key_down(self, key: str):
        if not self._check_direct_control() or not self._should_execute(): return
        key = key.lower()
        if key not in self._keys_down:
            pydirectinput.keyDown(key)
            self._keys_down.add(key)

    def key_up(self, key: str):
        key = key.lower()
        if key in self._keys_down:
            pydirectinput.keyUp(key)
            self._keys_down.remove(key)

    # --- MÉTHODES SOURIS (Optimisées pour Warframe) ---
    def click_mouse(self, button: str, x=None, y=None):
        if self.mouse_input_blocked or not self._check_direct_control(): return
        try:
            pydirectinput.click(x, y, button=button.lower())
        except:
            pyautogui.click(x, y, button=button.lower())
            
    def move_mouse(self, x: int, y: int, duration=0.1):
        if self.mouse_input_blocked or not self._check_direct_control(): return
        pydirectinput.moveTo(x, y, duration=duration)

    def release_all(self):
        for key in list(self._keys_down): self.key_up(key)
        if not self.mouse_input_blocked:
            for btn in list(self._mouse_buttons_down):
                pydirectinput.mouseUp(button=btn)
            self._mouse_buttons_down.clear()
        log.debug("Mains relâchées.")

    # --- API BRIDGE ---
    class API:
        def __init__(self, outer): self.outer = outer

        def type_key(self, key: str): self.outer.type_key(key)
        def key_down(self, key: str): self.outer.key_down(key)
        def key_up(self, key: str): self.outer.key_up(key)
        def click_mouse(self, button: str, x=None, y=None): self.outer.click_mouse(button, x, y)
        def move_mouse(self, x: int, y: int): self.outer.move_mouse(x, y)
        def release_all(self): self.outer.release_all()

        # Actions Spéciales
        def launch_url(self, url: str): return webbrowser.open(url)
        def open_program(self, name: str):
            cmd = PROGRAM_COMMANDS.get(name)
            if cmd: os.system(cmd[0] if CURRENT_OS == "Windows" else cmd[1])

        def watch_anime(self, platform="Crunchyroll"):
            url = ANIME_PLATFORMS.get(platform, NETFLIX_URL)
            webbrowser.open(url)

        async def execute_sequence(self, sequence: List[Tuple[str, float]]):
            for action, duration in sequence:
                if self.outer.control_locked: break
                self.outer.type_key(action)
                await asyncio.sleep(duration)
            self.outer.release_all()