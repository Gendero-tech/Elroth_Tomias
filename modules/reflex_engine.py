import time
import logging
import cv2
import numpy as np
import pyautogui
from modules.module import Module

# On désactive la sécurité de pyautogui pour éviter les arrêts brusques en jeu
pyautogui.FAILSAFE = False

logger = logging.getLogger('ReflexEngine')

class ReflexEngine(Module):
    def __init__(self, signals, modules, enabled=True):
        super().__init__(signals, enabled)
        self.modules = modules
        self.running = False
        self.reflex_delay = 0.05  # 50ms pour une réactivité "humaine"
        
    async def run(self):
        if not self.enabled:
            return
            
        self.running = True
        logger.info("⚡ Reflex Engine (Auto-Combat & Survie) ACTIF.")
        
        while self.running and not self.signals.terminate:
            try:
                # Récupération de la vision
                vision = self.modules.get('vision')
                if not vision:
                    continue

                # 1. RÉFLEXE DE SURVIE (Santé)
                self._survival_reflex(vision)
                
                # 2. RÉFLEXE DE COMBAT (Warframe)
                # On vérifie si la fenêtre active est bien le jeu
                if "warframe" in vision.API.get_context().lower():
                    self._combat_reflexes(vision)
                
                time.sleep(self.reflex_delay)
            except Exception as e:
                logger.error(f"Erreur ReflexEngine : {e}")
                time.sleep(1)

    def _survival_reflex(self, vision):
        """ Analyse la zone de vie et soigne si nécessaire """
        roi_stats = vision.API.get_game_roi("warframe")
        # On cherche la couleur rouge intense dans la zone de stats
        hsv = cv2.cvtColor(roi_stats, cv2.COLOR_BGR2HSV)
        lower_red = np.array([0, 150, 50])
        upper_red = np.array([10, 255, 255])
        mask = cv2.inRange(hsv, lower_red, upper_red)
        
        # Si le rouge disparaît (vie basse), on appuie sur la touche de soin
        if np.sum(mask) < 500: # Seuil à ajuster selon ton interface
            # self.modules['control'].API.press_key('q') 
            pass

    def _combat_reflexes(self, vision):
        """ Détection d'ennemis au réticule et tir automatique """
        # On capture une petite zone au centre de l'écran (le réticule)
        screen = vision.API.get_screenshot()
        h, w, _ = screen.shape
        center_x, center_y = w // 2, h // 2
        offset = 50 # Zone de 100x100 pixels
        
        crosshair_zone = screen[center_y-offset:center_y+offset, center_x-offset:center_x+offset]
        
        # Détection de la couleur rouge (barre de vie ennemie)
        hsv = cv2.cvtColor(crosshair_zone, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([0, 100, 100]), np.array([10, 255, 255]))
        
        if np.any(mask):
            logger.info("🎯 Cible verrouillée ! Tir réflexe.")
            pyautogui.click() # Simule le tir

    def stop(self):
        self.running = False