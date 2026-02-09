import logging
from modules.module import Module
# Assurez-vous que constants.py contient la variable MULTIMODAL_STRATEGY
from constants import MULTIMODAL_STRATEGY, DEFAULT_VISUAL_FILE_PATH 
from typing import Dict, Any, Optional

# 🚀 CORRECTIONS APPORTÉES
import asyncio  # Nécessaire pour asyncio.sleep et asyncio.run
import os       # Nécessaire pour os.path.exists

logger = logging.getLogger('MultiModal')
logger.setLevel(logging.INFO)

class MultiModal(Module):

    def __init__(self, signals, enabled: bool = True):
        super().__init__(signals, enabled)
        self.API = self.API(self)
        self.enabled = enabled
        
        # 🎯 CORRECTION : Initialisation de l'attribut de prompt d'injection
        self.prompt_injection: Optional[str] = None 
        # Ajout d'un drapeau pour la présence de l'image
        self.visual_input_path: Optional[str] = None 
        
        logger.info(f"MultiModal Module initialisé (Mode: {MULTIMODAL_STRATEGY})")

    # 🚀 AMÉLIORATION : Fonction qui analyse le besoin en Multimodalité
    def _check_for_visual_input(self) -> bool:
        """
        Vérifie si une entrée visuelle a été soumise (ex: un fichier a été uploadé).
        """
        # Dans un système Streamlit/Dashboard, ceci vérifierait l'existence d'un fichier temporaire
        # Nous allons vérifier une simple existence de fichier comme placeholder :
        
        # NOTE: Remplacer DEFAULT_VISUAL_FILE_PATH par le chemin réel d'upload
        if os.path.exists(DEFAULT_VISUAL_FILE_PATH):
            self.visual_input_path = DEFAULT_VISUAL_FILE_PATH
            logger.info("Image détectée pour le traitement Multimodal.")
            return True
            
        self.visual_input_path = None
        return False
        
    def get_prompt_injection(self) -> str:
        """Retourne l'injection de prompt générée (e.g., description d'image)."""
        # Si une image a été traitée, retourne le prompt.
        if self.prompt_injection:
             # On le nettoie après l'avoir fourni une fois
             temp_prompt = self.prompt_injection
             self.prompt_injection = None
             return temp_prompt
             
        return ""

    async def run(self):
        """Boucle principale asynchrone (Gère le traitement de l'image)."""
        while not self.signals.terminate:
            
            if self.enabled and self._check_for_visual_input() and not self.prompt_injection:
                # Si une image est présente MAIS n'a pas encore été analysée
                
                # 🚨 LOGIQUE VÉRIDIQUE REQUISE : Appeler le modèle de vision (CLIP ou autre)
                # Pour simplifier, nous allons simuler la description pour le moment :
                
                visual_desc = f"Une image a été fournie à Clio. Son contenu semble être une capture d'écran du jeu. "
                visual_desc += "L'IA doit utiliser cette image pour contextualiser sa réponse, sans la mentionner directement."
                
                self.prompt_injection = f"--- CONTEXTE VISUEL ---\n{visual_desc}"
                self.signals.new_message = True # Pour forcer la boucle du Prompter à s'activer
                
                # ⚠️ IMPORTANT: Après traitement, l'image devrait être déplacée/supprimée
                # os.remove(self.visual_input_path)
                # self.visual_input_path = None
                
            await asyncio.sleep(1)


    # ... (Les fonctions strategy_never et strategy_always restent inchangées) ...

    class API:
        def __init__(self, outer):
            self.outer = outer

        def set_multimodal_status(self, status: bool):
            self.outer.enabled = status
            self.outer.signals.sio_queue.put(('multimodal_status', status))
            logger.info(f"MultiModal set to enabled={status}")

        def get_multimodal_status(self):
            return self.outer.enabled

        # Determines when a prompt should go to the multimodal model
        def multimodal_now(self) -> bool:
            """
            Décide si la requête actuelle doit être envoyée au LLM Multimodal.
            Le LLM Multimodal sera utilisé si un prompt d'injection est prêt.
            """
            if not self.outer.enabled:
                return False

            if MULTIMODAL_STRATEGY == "never":
                return self.outer.strategy_never()
            elif MULTIMODAL_STRATEGY == "always":
                return self.outer.strategy_always()
            elif self.outer.prompt_injection:
                # Si le prompt d'injection contient une description (image analysée)
                return True
            else:
                return False