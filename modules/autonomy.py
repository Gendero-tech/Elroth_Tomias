import time
import logging
import asyncio
import random
import json
import os
from modules.module import Module

log = logging.getLogger('AutonomyModule')

class AutonomyModule(Module):
    """
    Gère le "Libre Arbitre" de Clio. 
    Accumule de l'envie de parler en fonction du temps et de la hype,
    puis déclenche une action et une émotion synchronisée via le mapping JSON.
    """
    def __init__(self, signals, modules, enabled: bool = True):
        super().__init__(signals, enabled)
        self.modules = modules
        
        # État interne
        self.autonomy_level = 0.0  
        self.last_interaction_time = time.time()
        
        # Configuration
        self.threshold = 0.75        
        self.buildup_rate = 0.012    
        
        # Activités et Tags
        self.activities = {
            "STREAM_CHAT_INTERACT": {"weight": 1.5, "tag": "[SOCIAL]"},
            "ANECDOTE_SHARE": {"weight": 1.0, "tag": "[CURIOSITY]"},
            "GAME_STRATEGY": {"weight": 1.2, "tag": "[TACTICAL]"},
            "REST_SUGGESTION": {"weight": 0.5, "tag": "[CARE]"},
            "HYPER_FOCUS": {"weight": 1.0, "tag": "[GENIUS]"}
        }
        
        self.API = self.API(self)

    def get_vts_hotkey(self, emotion_key):
        """Récupère dynamiquement le nom de la hotkey depuis le config JSON."""
        try:
            config_path = os.path.join("memories", "emotions_config.json")
            if not os.path.exists(config_path):
                log.warning(f"Fichier config introuvable à {config_path}, retour au neutre.")
                return "neutral"
                
            with open(config_path, "r", encoding='utf-8') as f:
                config = json.load(f)
            return config["mappings"].get(emotion_key, {}).get("hotkey", "neutral")
        except Exception as e:
            log.error(f"Erreur lecture emotions_config.json: {e}")
            return "neutral"

    async def run(self):
        log.info("🧠 Libre Arbitre de Clio (V2 Awareness) activé.")
        while not self.signals.terminate:
            try:
                await asyncio.sleep(5) 
                
                # 1. Calcul de l'accumulation avec influence Sociale
                hype = 0.0
                if "social_monitor" in self.modules:
                    hype = self.modules["social_monitor"].API.get_hype_level()
                
                inc = (self.buildup_rate * 5) * (1.0 + (hype * 2.5))
                self.autonomy_level = min(1.0, self.autonomy_level + inc)
                
                # 2. Sécurités : On ne déclenche rien si Clio est déjà occupée
                is_talking = getattr(self.signals, 'AI_speaking', False)
                is_thinking = getattr(self.signals, 'AI_thinking', False)
                is_human = getattr(self.signals, 'human_speaking', False)

                if is_talking or is_thinking or is_human:
                    continue

                # 3. Tentative de déclenchement
                if self.autonomy_level >= self.threshold:
                    if random.random() < self.autonomy_level:
                        log.info(f"✨ Pulsion d'autonomie détectée ({self.autonomy_level:.2f})")
                        self.decide_and_trigger()
                
            except Exception as e:
                log.error(f"Erreur boucle autonomie : {e}")
                await asyncio.sleep(2)

    def decide_and_trigger(self):
        """Choisit une activité et déclenche l'émotion VTS via le mapping JSON."""
        weights_map = self._calculate_weights()
        activity = random.choices(list(weights_map.keys()), weights=list(weights_map.values()))[0]
        
        host = self.signals.get_current_host_name() if hasattr(self.signals, 'get_current_host_name') else "Ambre"
        game = getattr(self.signals, 'current_activity_name', 'ton activité actuelle')

        # Configuration des pulsions
        activity_config = {
            "STREAM_CHAT_INTERACT": {"prompt": "Interpelle le chat !", "emotion": "happy"},
            "ANECDOTE_SHARE": {"prompt": f"Partage une anecdote sur {game}.", "emotion": "thinking"},
            "GAME_STRATEGY": {"prompt": "Donne un conseil tactique.", "emotion": "concentration"},
            "REST_SUGGESTION": {"prompt": f"Dis à {host} de faire une pause.", "emotion": "gentle"},
            "HYPER_FOCUS": {"prompt": "Analyse de génie en cours.", "emotion": "genuis"}
        }

        config = activity_config[activity]
        tag = self.activities[activity]['tag']
        
        # Récupération de la hotkey réelle via le JSON (ex: "genuis" -> "genuis")
        vts_hotkey = self.get_vts_hotkey(config['emotion'])
        
        # 1. Déclenchement physique (VTS)
        if "vtube_studio" in self.modules:
            self.modules["vtube_studio"].API.trigger(vts_hotkey)
            log.info(f"🎭 Autonomie : Hotkey VTS '{vts_hotkey}' activée (Emotion: {config['emotion']})")

        # 2. Envoi au Brain
        if "brain" in self.modules:
            brain = self.modules["brain"]
            final_instruction = f"[AUTONOMY_PULSION] {config['prompt']} {tag}"
            if self.signals.loop:
                asyncio.run_coroutine_threadsafe(brain.process_llm_response(final_instruction), self.signals.loop)
                self.API.reset_autonomy_level()
            else:
                log.error("❌ Loop asyncio introuvable !")

    def _calculate_weights(self) -> dict:
        w = {k: v["weight"] for k, v in self.activities.items()}
        if "social_monitor" in self.modules:
            hype = self.modules["social_monitor"].API.get_hype_level()
            if hype > 0.7: w["STREAM_CHAT_INTERACT"] *= 2.5
        return w

    class API:
        def __init__(self, outer): self.outer = outer
        def boost_autonomy(self, amount: float):
            self.outer.autonomy_level = min(1.0, self.outer.autonomy_level + amount)
            log.info(f"⚡ Autonomie boostée à {self.outer.autonomy_level:.2f}")
        def reset_autonomy_level(self):
            self.outer.autonomy_level = 0.0
            self.outer.last_interaction_time = time.time()
        def get_current_drive(self) -> float: return self.outer.autonomy_level