import re
from typing import Dict, List, Any

# NOTE: Le logging est préféré à print() dans les modules
import logging
logger = logging.getLogger('EmotionDetector')

class EmotionDetector:
    # 🚀 AMÉLIORATION : Utilisation d'un dictionnaire de pondération
    def __init__(self, signals: Any, emotionSync: Any, modules: Dict[str, Any] = None): 
        self.signals = signals
        self.emotionSync = emotionSync
        self.memory = modules.get('memory') if modules else None
        
        # 🧠 Mots-clés associés à chaque émotion, avec PONDÉRATION (mot, score)
        self.emotion_keywords: Dict[str, List[Tuple[str, int]]] = {
            # Émotions fortement positives ou négatives (Score de base 2)
            "happy":     [("bravo", 3), ("victoire", 3), ("gagné", 2), ("heureux", 2), ("content", 1), ("yay", 3), ("réussi", 2), ("super", 1)],
            "sad":       [("désolé", 1), ("triste", 2), ("perdu", 2), ("échec", 3), ("mort", 3), ("solitude", 3), ("pas bien", 2)],
            # Détresse (Score de base 3)
            "anxious":   [("stress", 3), ("anxiété", 4), ("peur", 3), ("angoissé", 4), ("panique", 5), ("inquiète", 2), ("fatigué", 1)],
            "angry":     [("rage", 4), ("colère", 3), ("énervé", 2), ("fâché", 2), ("dégoûté", 2), ("injuste", 3), ("crise", 4), ("idiot", 1)],
            # Émotions légères ou contextuelles (Score de base 1)
            "dreamy":    [("rêve", 1), ("imagine", 1), ("étoile", 1), ("univers", 1), ("magie", 1), ("flottant", 1)],
            "mocking":   [("creeper", 1), ("explosé", 1), ("haha", 1), ("nul", 1), ("mdr", 1), ("troll", 1), ("fail", 1)],
            "surprised": [("quoi", 1), ("hein", 1), ("incroyable", 2), ("choqué", 2), ("impossible", 2), ("oh", 1)],
            "calm":      [("respire", 1), ("doucement", 1), ("calme", 1), ("tranquille", 1), ("zen", 1), ("repos", 1)],
        }
        
        # 🚀 AMÉLIORATION : Définition de l'impact des émotions (pour le SessionManager)
        self.impact_scores: Dict[str, int] = {
            "happy": 5, "sad": 7, "anxious": 9, "angry": 8, "dreamy": 2, "mocking": 3, "surprised": 4, "calm": 1
        }


    def detect_emotion(self, message: str) -> Dict[str, Any]:
        """
        Détecte l'émotion dominante basée sur le score total des mots-clés trouvés.
        Retourne l'émotion, le score total, et une estimation de l'impact.
        """
        message = message.lower()
        emotion_scores: Dict[str, int] = {}
        
        # 1. Calcul des scores pour chaque émotion
        for emotion, keywords in self.emotion_keywords.items():
            current_score = 0
            for word, weight in keywords:
                # Utiliser des limites de mots pour éviter les fausses détections
                if re.search(rf"\b{word}\b", message):
                    current_score += weight
            
            if current_score > 0:
                emotion_scores[emotion] = current_score

        # 2. Déterminer l'émotion dominante
        if not emotion_scores:
            dominant_emotion = "calm"
            total_score = 0
        else:
            # Trouve l'émotion avec le score le plus élevé
            dominant_emotion = max(emotion_scores, key=emotion_scores.get)
            total_score = emotion_scores[dominant_emotion]

        # 3. Calcul de l'impact (pour le SessionManager)
        impact = self.impact_scores.get(dominant_emotion, 1) * total_score
        
        return {
            "emotion": dominant_emotion,
            "score": total_score,
            "impact": impact # Utile pour évaluer le besoin d'intervention
        }


    def process_message(self, message: str):
        """Analyse le message, met à jour la mémoire et synchronise l'avatar."""
        detection_result = self.detect_emotion(message)
        emotion = detection_result["emotion"]
        
        logger.info(f"Détection : '{emotion}' (Score: {detection_result['score']}, Impact: {detection_result['impact']})")
        
        # 🚀 AMÉLIORATION : Mettre à jour la mémoire de session avec l'émotion et l'impact
        if self.memory:
            # NOTE : update_session_emotion devra être adapté dans Memory.py/SessionManager
            self.memory.API.update_session_emotion(emotion, detection_result['impact'])
            
        # 🚀 AMÉLIORATION : Synchroniser l'avatar VTS avec l'émotion dominante
        self.emotionSync.apply_emotion(emotion, message)