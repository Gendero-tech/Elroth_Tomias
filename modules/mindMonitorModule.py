import asyncio
import logging
from modules.module import Module
from typing import Optional, Dict, Any, List
import time  # Maintenu pour la cohérence, même si non utilisé directement dans la boucle courte

log = logging.getLogger('MindMonitor')

class MindMonitorModule(Module):
    """
    Module passif pour surveiller et exposer l'état de pensée de Clio.
    Il collecte la dernière pensée brute du LLM, l'analyse émotionnelle du Brain,
    la perception visuelle, et les actions VTS. C'est le miroir de la conscience de Clio.
    """
    def __init__(self, signals, modules, enabled=True):
        super().__init__(signals, enabled)
        
        self.modules = modules
        # Assigner les modules principaux
        self.brain_module = self.modules.get('brain')
        self.prompter_module = self.modules.get('prompter')
        self.vision_module = self.modules.get('vision')
        self.vts_module = self.modules.get('vtube_studio') 
        
        # État exposé de la pensée et de la vision
        # 🧠 La pensée LLM brute contient le texte et les tags [EMOTION:...]
        self.last_thought_raw: str = "En attente de la première réponse LLM..."
        self.last_visual_perception: str = "Aucune détection visuelle récente."
        
        # Le Brain Module fournit l'analyse
        self.last_decision: str = "Aucune action prise."
        self.current_emotion: str = "Neutre"
        
        # NOUVEAUX CHAMPS POUR LE DEBUG ÉMOTIONNEL/VTS
        self.last_vts_reaction: str = "Aucune"
        self.vts_hotkeys_pending: List[str] = [] 
        
        self.API = self.API(self)
        log.info("👀 Mind Monitor Module initialisé.")

    async def run(self):
        """Boucle de surveillance simple pour mettre à jour l'état."""
        while not self.signals.terminate:
            
            # Récupération des modules (pour la résilience au cas où ils démarrent plus tard)
            prompter = self.modules.get('prompter')
            brain = self.modules.get('brain')
            vision = self.modules.get('vision')
            vts = self.modules.get('vtube_studio')
            
            # --- 1. Mettre à jour la Pensée LLM (Prompter) ---
            if prompter and hasattr(prompter, 'API') and hasattr(prompter.API, 'get_last_llm_response'):
                # Récupération de la réponse LLM brute
                # Utilise l'opérateur "or" pour conserver l'état précédent si la nouvelle valeur est None (ou vide)
                self.last_thought_raw = prompter.API.get_last_llm_response() or self.last_thought_raw
            
            # --- 2. Mettre à jour la Décision et l'Émotion (Brain) ---
            if brain and hasattr(brain, 'API'):
                brain_api = brain.API
                
                # Récupération de l'émotion actuelle (analysée par le Brain)
                if hasattr(brain_api, 'get_current_emotion'):
                    self.current_emotion = brain_api.get_current_emotion()
                
                # Récupération de la dernière décision prise
                if hasattr(brain_api, 'get_last_decision'):
                    self.last_decision = brain_api.get_last_decision()

            # --- 3. Mettre à jour la Perception Visuelle (Vision) ---
            if vision and hasattr(vision, 'API') and hasattr(vision.API, 'get_last_detection_summary'):
                # Récupération du résumé de détection
                self.last_visual_perception = vision.API.get_last_detection_summary()
                    
            # --- 4. Mettre à jour les Actions VTS (VTube Studio) ---
            if vts and hasattr(vts, 'API'):
                vts_api = vts.API
                
                # Récupération du dernier hotkey exécuté
                if hasattr(vts_api, 'get_last_executed_hotkey'):
                    self.last_vts_reaction = vts_api.get_last_executed_hotkey()
                
                # Récupération de ceux en attente
                if hasattr(vts_api, 'get_pending_hotkeys'):
                    self.vts_hotkeys_pending = vts_api.get_pending_hotkeys()
            
            # Le cœur de la boucle ne fait que dormir pour permettre la lecture des API par d'autres systèmes.
            await asyncio.sleep(0.5) 


    # --- CLASSE API : Pour accéder aux données de surveillance ---
    class API:
        def __init__(self, outer):
            self.outer = outer

        def get_mind_state(self) -> Dict[str, str | List[str]]:
            """
            Retourne les informations de pensée, de vision, d'émotion et de VTS actuelles de Clio.
            """
            # Ces données sont lues directement depuis les attributs du Module, 
            # mis à jour par la boucle run() asynchrone.
            return {
                # LLM BRUT (contient le texte et les tags)
                "🧠 Pensée_LLM_Brute": self.outer.last_thought_raw, 
                
                # ANALYSE PAR LE BRAIN
                "💖 Émotion_Actuelle": self.outer.current_emotion,
                "🧭 Décision_Brain": self.outer.last_decision,
                
                # PERCEPTION/ACTION
                "💡 Perception_Visuelle": self.outer.last_visual_perception,
                "🎭 Dernière_Action_VTS": self.outer.last_vts_reaction,
                "⏳ Hotkeys_En_Attente": self.outer.vts_hotkeys_pending
            }