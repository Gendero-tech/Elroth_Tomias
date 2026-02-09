# Fichier : modules/avatarDesignAgent.py

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Union

from modules.module import Module

logger = logging.getLogger('AvatarDesignAgent')

class AvatarDesignAgent(Module):
    """
    Agent spécialisé dans la génération de spécifications d'avatar (2D/3D) 
    et de commandes complexes pour VTube Studio.
    Délègue la génération de code et de design au LLM (ExpertAgent).
    """
    def __init__(self, signals, modules: Dict[str, Any], enabled: bool = True):
        super().__init__(signals, enabled)
        self.modules = modules
        self.API = self.API(self)
        
        # Dépendances critiques
        self.expert_agent = self.modules.get('expert_agent')
        self.vts = self.modules.get('vtube_studio') 
        
        # Stockage temporaire des spécifications générées
        self.last_design_specification: Optional[Dict[str, Any]] = None
        
        logger.info("🎨 Agent de Design d'Avatar initialisé.")

    async def run(self):
        # Module réactif : pas de boucle continue nécessaire.
        pass

    def _generate_llm_design(self, theme: str) -> str:
        """
        Génère les spécifications détaillées du nouvel accessoire ou avatar via le LLM.
        """
        if not self.expert_agent:
            return "Expert Agent non disponible pour la génération de design."

        # Prompt d'ingénierie pour le design 
        prompt = (
            f"Tu es un designer 2D/3D expert en modélisation VTuber. Crée un document de spécification "
            f"pour un nouvel accessoire VTube Studio pour CLIO basé sur le thème : '{theme}'.\n\n"
            f"Spécifie (en JSON ou Markdown lisible) :\n"
            f"1. Le nom de l'accessoire.\n"
            f"2. Ses dimensions (taille, position X/Y).\n"
            f"3. Le nom du Hotkey VTS pour l'activer/désactiver.\n"
            f"4. Une instruction simple pour générer un script Blender si 3D était nécessaire."
        )
        
        try:
            # Utilise l'appel Copilot/GPT pour la génération structurée et créative
            result = self.expert_agent.API.call_copilot_for_code(prompt)
            return result
        except Exception as e:
            return f"Erreur de génération de design par l'expert LLM: {e}"

    # --- API (Pour les délégations LLM et les commandes de création) ---
    class API:
        def __init__(self, outer: 'AvatarDesignAgent'):
            self.outer = outer

        def conceive_new_accessory(self, theme: str) -> str:
            """
            Déclenche la conception d'un nouvel accessoire d'avatar basé sur un thème.
            """
            logger.info(f"Ordre de conception reçu pour le thème : {theme}")
            
            # 1. Génération de la spécification (Bloquant, doit être exécuté dans un thread)
            design_spec = self.outer._generate_llm_design(theme)
            
            if "Erreur" in design_spec:
                 return design_spec
                 
            # 2. Tentative de conversion en JSON pour le stockage interne
            try:
                # NOTE: Il faudrait ici parser la sortie LLM qui doit être JSON
                self.outer.last_design_specification = {"theme": theme, "spec": design_spec}
                
                # 3. 💡 AMÉLIORATION : Génère une commande VTS pour charger l'accessoire
                hotkey_name = theme.replace(" ", "_").upper()
                
                return f"Spécification de design générée. Le nouvel accessoire a été conçu. " \
                       f"Action suggérée pour le Prompter : Déléguer à VTS pour charger l'item (Hotkeys : {hotkey_name})."
                       
            except Exception as e:
                 return f"Design généré, mais erreur lors du parsing de la spécification: {e}"

        def commission_model_generation(self, spec_details: str) -> str:
            """
            Simule la demande de génération de l'asset 3D ou 2D basé sur la spécification.
            Dans un environnement réel, cela appellerait un service d'art IA (Midjourney/Dall-E).
            """
            if not self.outer.expert_agent:
                 return "Expert Agent non disponible."
                 
            logger.info(f"Demande de commission pour la génération d'un asset : {spec_details[:30]}...")
            
            # 💡 AMÉLIORATION : Déléguer à l'ExpertAgent pour générer un code Blender ou un prompt Midjourney
            generation_prompt = (
                f"Crée un prompt DALL-E/Midjourney ou un script Blender/Python pour générer un accessoire 2D/3D photoréaliste "
                f"basé sur la spécification : {spec_details}. Ton objectif est de produire l'image."
            )
            
            try:
                result = self.outer.expert_agent.API.call_copilot_for_code(generation_prompt)
                return f"L'Agent Expert a généré les instructions de génération d'asset. Résultat : {result[:50]}..."
            except Exception as e:
                return f"Erreur lors de la commission de génération d'asset : {e}"