import time
import json
import os
import logging
from typing import List, Dict, Any
from modules.module import Module

logger = logging.getLogger('SessionManager')

DISTRESS_THRESHOLD = 20 
MAX_IMPACT_DURATION = 60 

class SessionManager(Module):
    def __init__(self, signals: Any, enabled: bool = True):
        super().__init__(signals, enabled) 
        
        self.last_user_inputs: List[str] = ["", ""]
        self.emotion_impact_history: List[Dict[str, Any]] = []
        self.last_detected_emotion: str = "neutral"
        
        # 🚀 Chemin vers les objectifs persistants
        self.task_file = "memories/active_tasks.json"
        self.current_tasks = self._load_persisted_tasks()
        
        self.API = self.API(self)

    def _load_persisted_tasks(self):
        """Charge les objectifs que Clio doit garder en tête entre deux sessions."""
        try:
            if os.path.exists(self.task_file):
                with open(self.task_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Erreur chargement tâches : {e}")
        return []

    def _save_tasks(self):
        """Sauvegarde les tâches sur le disque."""
        try:
            os.makedirs(os.path.dirname(self.task_file), exist_ok=True)
            with open(self.task_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_tasks, f, indent=4)
        except Exception as e:
            logger.error(f"Erreur sauvegarde tâches : {e}")

    def _prune_impact_history(self):
        """Nettoie les vieux impacts émotionnels."""
        now = time.time()
        self.emotion_impact_history = [
            item for item in self.emotion_impact_history 
            if now - item['time'] < MAX_IMPACT_DURATION
        ]

    class API:
        def __init__(self, outer: 'SessionManager'):
            self.outer = outer

        # ✅ SOLUTION AU WARNING : Ajout de clear_session_context
        def clear_session_context(self):
            """Réinitialise l'état émotionnel et les entrées récentes pour une nouvelle activité."""
            self.outer.last_user_inputs = ["", ""]
            self.outer.emotion_impact_history = []
            self.outer.last_detected_emotion = "neutral"
            logger.info("🧹 Contexte de session réinitialisé (Activity Switch).")

        def get_current_goals(self) -> List[str]:
            """Retourne la liste des objectifs ouverts."""
            return [t['desc'] for t in self.outer.current_tasks if t.get('status') == 'open']

        def update_session_emotion(self, emotion: str, impact_score: int):
            """Enregistre un impact émotionnel."""
            self.outer._prune_impact_history()
            self.outer.emotion_impact_history.append({
                'time': time.time(),
                'emotion': emotion,
                'impact': impact_score
            })
            self.outer.last_detected_emotion = emotion

        def is_user_in_distress(self) -> bool:
            """Vérifie si le score de détresse accumulé est trop haut."""
            self.outer._prune_impact_history()
            total_impact = sum(item['impact'] for item in self.outer.emotion_impact_history)
            return total_impact >= DISTRESS_THRESHOLD