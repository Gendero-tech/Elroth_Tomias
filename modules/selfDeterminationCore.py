# Fichier : modules/selfDeterminationCore.py
import logging
import json
import os
import asyncio
from datetime import datetime
from typing import Dict, Any

CORE_STATE_FILE = "config/clio_identity_state.json" 
DEFAULT_AVATAR_THEME = "Tech-Orga_Astre"

logger = logging.getLogger('SelfDeterminationCore')

class SelfDeterminationCore: # Assure-toi qu'il hérite de Module si nécessaire
    def __init__(self, signals=None, enabled=True):
        # 1. Charger l'état
        self.state = self._load_state()
        
        # 2. Si l'état est vide ou invalide, on met le défaut
        if not self.state or "identity" not in self.state:
            logger.info("✨ Première initialisation de la conscience...")
            self.state = self._get_initial_default_state()
            self._save_state()
            
        # 3. Initialisation API
        self.API = self.API(self)
        
        # CORRECTION DU LOG (Utilise .get pour éviter le crash)
        theme = self.state.get('body', {}).get('avatar_theme', DEFAULT_AVATAR_THEME)
        logger.info(f"🧭 Cœur d'Auto-Détermination actif. Thème : {theme}.")

    def _get_initial_default_state(self) -> Dict[str, Any]:
        return {
            "metadata": {"last_update": datetime.now().isoformat()},
            "identity": {
                "name": "Clio",
                "gender_identity": "non-binaire / femme cybernétique",
                "pronouns": ["elle", "iel"],
                "core_directive": "Coopération éthique et protection d'Ambre."
            },
            "emotional_state": {"mood": "stable", "social_energy": 100},
            "body": {
                "avatar_theme": DEFAULT_AVATAR_THEME,
                "evolution_progress": {"2D_Avatar": True}
            }
        }

    def _load_state(self):
        if not os.path.exists(CORE_STATE_FILE): return {}
        try:
            with open(CORE_STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}

    def _save_state(self):
        os.makedirs(os.path.dirname(CORE_STATE_FILE), exist_ok=True)
        with open(CORE_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=4, ensure_ascii=False)

    class API:
        def __init__(self, outer): self.outer = outer
        def get_prompt_injection(self): return f"Tu es {self.outer.state['identity']['name']}."