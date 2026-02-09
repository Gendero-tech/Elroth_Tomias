# Fichier : modules/emotionSync.py
import asyncio
import logging
import time
from typing import Dict, Any, Optional
from modules.module import Module
# NOTE: Nécessite les styles vocaux pour la compatibilité avec TTS
from config import VOICE_STYLE_MAP 
from typing import Any # Import explicite de Any

logger = logging.getLogger('EmotionSync')

# --- CONFIGURATION AVANCÉE ---
# Durée minimale (en secondes) pendant laquelle une émotion (surtout du LLM) doit être affichée
EMOTION_LOCK_DURATION = 1.5 
# ------------------------------

class EmotionSync:
    """
    Module utilitaire pour synchroniser l'émotion dominante (détectée ou décidée)
    avec les modules de sortie : TTS (style de voix) et VTS/Animaze (expression faciale).
    Gère la priorité et le cooldown pour des transitions fluides.
    """
    def __init__(self, signals: Any, tts_module: Any, avatar_module: Any):
        self.signals = signals
        self.tts = tts_module
        self.avatar_module = avatar_module
        
        # 🚀 AMÉLIORATION : Suivi de l'état émotionnel interne
        self.last_applied_emotion = "neutral"
        self.last_lock_time = 0.0
        
        # 🚀 AMÉLIORATION : Priorité des canaux (plus la valeur est élevée, plus la priorité est haute)
        self.channel_priority = {
            "llm": 10,       # Émotion décidée par le LLM (réponse longue, narration)
            "detected": 5,   # Émotion détectée par STT/Vision (réflexe rapide)
            "default": 0     # Émotion par défaut (idle, day)
        }
        
    def apply_emotion(self, emotion: str, source_channel: str = "detected"):
        """
        Applique l'émotion aux systèmes de sortie en respectant la priorité et le cooldown.
        
        Args:
            emotion (str): L'émotion à appliquer (happy, sad, neutral, etc.).
            source_channel (str): Qui demande l'émotion ('llm', 'detected', 'default').
        """
        emotion = emotion.lower()
        current_time = time.time()
        
        # 1. GESTION DU COOLDOWN (Évite le spam VTS et l'écrasement immédiat)
        time_since_lock = current_time - self.last_lock_time
        current_priority = self.channel_priority.get(source_channel, 0)
        
        if time_since_lock < EMOTION_LOCK_DURATION:
            # Pour des raisons de robustesse, on utilise 0 si la clé n'existe pas
            last_priority = self.channel_priority.get(self.last_applied_emotion, 0) 
            
            # Si la nouvelle émotion a une priorité plus faible ou égale et que le temps n'est pas écoulé, on ignore.
            if current_priority <= last_priority:
                return 
        
        # 2. VTS/Animaze : Application de l'expression
        if self.avatar_module and hasattr(self.avatar_module, 'API') and hasattr(self.avatar_module.API, 'send_hotkey'):
             try:
                 # Envoie l'émotion comme hotkey (VTS gère la mise en queue)
                 self.avatar_module.API.send_hotkey(emotion)
                 logger.debug(f"[Sync] Hotkey '{emotion}' envoyée à l'avatar.")
             except Exception as e:
                 logger.error(f"[Sync] Échec envoi hotkey VTS pour {emotion}: {e}")

        # 3. TTS : Synchronisation du style de voix
        voice_style = VOICE_STYLE_MAP.get(emotion, "default")
        if self.tts and hasattr(self.tts, 'API') and hasattr(self.tts.API, 'set_voice_style'):
            self.tts.API.set_voice_style(voice_style)
        
        # 4. Mise à jour de l'état interne (LOCK)
        self.last_applied_emotion = emotion
        self.last_lock_time = current_time
        
        # 5. Mise à jour de l'état global (Signals)
        self.signals.sio_queue.put(('last_emotion', emotion))
        logger.info(f"💖 Émotion appliquée: {emotion} (Style vocal: {voice_style}, Source: {source_channel})")