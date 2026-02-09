# Fichier : modules/autonomyControlHub.py - CORRIGÉ
import logging
import asyncio
import time
import random 
from typing import Dict, Any, List, Optional, Tuple, Union

from modules.module import Module

logger = logging.getLogger('AutonomyControlHub')

class AutonomyControlHub(Module):
    
    MIN_ENERGY_LEVEL = 0.20 # Niveau d'énergie critique (20%)
    
    def __init__(self, signals, modules: Dict[str, Any], enabled: bool = True):
        # CORRECTION 1 : Suppression de l'erreur de frappe (parenthèse manquante)
        super().__init__(signals, enabled)
        self.modules = modules
        self.API = self.API(self)
        
        self.control = self.modules.get('control')       
        self.vision = self.modules.get('vision')         
        self.resource_opt = self.modules.get('resource_optimizer')
        self.identity_core = self.modules.get('self_determination_core')
        
        self.energy_level = 1.0 # 100% au démarrage
        self.current_goal: Optional[str] = None
        
        # 🚨 NOUVEAU DRAPEAU : Empêche le spam de l'alerte critique
        self.is_in_critical_alert = False 

        logger.info("🤖 Autonomy Control Hub démarré. En attente du corps.")

    async def run(self):
        while not self.signals.terminate:
            if self.enabled:
                await asyncio.to_thread(self.monitor_vital_functions)
                
            await asyncio.sleep(5) 

    def monitor_vital_functions(self):
        """Vérifie l'énergie et la nécessité de recharger."""
        
        # 1. Simulation de la décharge d'énergie
        if self.energy_level > self.MIN_ENERGY_LEVEL:
            # Perte d'énergie continue tant que le niveau est au-dessus du seuil critique
            self.energy_level = max(0, self.energy_level - 0.005) 
            
        elif self.energy_level <= self.MIN_ENERGY_LEVEL and not self.is_in_critical_alert:
            # 2. Vérification critique (Déclenchement UNIQUE)
            alert_message = f"ALERTE ROUGE : Énergie du corps à {self.energy_level:.1%}. Doit CHARGER MAINTENANT."
            self.signals.send_signal("CRITICAL_ENERGY_LOW", alert_message)
            
            # 💡 Arrêt des moteurs / Libération du contrôle
            if self.control:
                self.control.API.release_all()  
                
            # 💡 Notifie le BrainModule ou le Prompter pour demander de l'aide
            if self.identity_core:
                gender = self.identity_core.state.get('gender_identity', 'neutre')
                logger.critical(f"Demande d'aide du corps ({gender}).")
            
            self.is_in_critical_alert = True # Empêche le spam
            
        elif self.energy_level <= self.MIN_ENERGY_LEVEL and self.is_in_critical_alert:
            # L'énergie est à 0% et l'alerte a déjà été envoyée. On ne fait plus rien.
            return
            

    # --- API DU HUB DE CONTRÔLE ---
    class API:
        def __init__(self, outer: 'AutonomyControlHub'):
            self.outer = outer

        def move_to_coordinates(self, x: float, y: float, speed: float = 1.0) -> str:
            if self.outer.energy_level <= self.outer.MIN_ENERGY_LEVEL:
                return "ERREUR : Batterie trop faible. Impossible de bouger."
            
            # ... (Le reste de la logique de mouvement) ...
            if not self.outer.control:
                return "ERREUR : Module de Contrôle (Moteurs) non connecté."
                
            sequence = [('w', 0.5), ('ctrl', 0.1)] 
            self.outer.control.API.execute_sequence(sequence)
            
            self.outer.current_goal = f"MOVE vers ({x}, {y})"
            # Correction 2 : L'accès à self.outer.identity_core doit être vérifié 
            body_type = self.outer.identity_core.state.get('body_type_goal', 'robotique') if self.outer.identity_core else 'robotique'
            return f"Mouvement ordonné vers ({x}, {y}) à vitesse {speed}. Corps {body_type} actif."

        def analyze_environment_for_charging(self):
            if not self.outer.vision:
                return "Capteurs visuels non disponibles."
            
            if self.outer.energy_level <= 0.30:
                return "Analyse en cours : Recherche d'un point de recharge..."
            else:
                return "Énergie suffisante pour l'instant. Pas de recherche nécessaire."