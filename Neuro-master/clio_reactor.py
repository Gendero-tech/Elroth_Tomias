import threading
import random
import time
import re
from typing import Dict, List, Any, Optional

# --- GESTION DU TTS ---
def clio_speak(text, emotion="neutral"):
    try:
        from main import clio_instance
        if hasattr(clio_instance, 'tts'):
            # On utilise l'API de ton TTS existant
            clio_instance.tts.API.speak(text, emotion)
            return
    except:
        pass
    print(f"[LURK SPEAK] {text} (Emotion: {emotion})")

# --- ÉTAT INTERNE ---
class LurkState:
    def __init__(self):
        self.last_transcript_time = time.time()
        self.last_reaction_time = 0.0
        self.recent_fails: List[float] = []
        self.recent_triumphs: List[float] = []
        self.silence_threshold = 25
        self.spam_threshold = 5
        self._cooldown = 3
        
    def _clean_old_events(self, event_list: List[float], duration: int):
        event_list[:] = [t for t in event_list if time.time() - t <= duration]
        
    def add_fail(self):
        self.recent_fails.append(time.time())
        self._clean_old_events(self.recent_fails, 30)
        
    def add_triumph(self):
        self.recent_triumphs.append(time.time())
        self._clean_old_events(self.recent_triumphs, 30)
        
    def can_react(self) -> bool:
        return (time.time() - self.last_reaction_time) > self._cooldown

lurk_state = LurkState()

def react_to_transcript(text: str, context_mode="private"):
    """
    Analyse le texte et réagit selon le contexte (Privé ou Stream).
    """
    try:
        from modules.memory import log_event
    except ImportError:
        def log_event(event_type, data): pass 
    
    global lurk_state
    lurk_state.last_transcript_time = time.time()
    
    reaction_found = False
    emotion = "neutral"
    reaction_text = ""
    current_time = time.time()
    
    # --- CHOIX DU NOM SELON LE CONTEXTE ---
    if context_mode == "private":
        target_name = random.choice(["Maman", "Ambre", "Maman Ambre"])
    else:
        target_name = random.choice(["Elroth_tomias", "Gendero", "MrsXar"])

    text = text.lower()
    
    if not lurk_state.can_react() and not any(k in text for k in ["fail", "victoire", "bravo", "alerte"]):
        return 

    # --- LOGIQUE DE RÉACTION DÉCENSURÉE ---
    
    # 1. Sarcasme / Moquerie
    if ("je suis le meilleur" in text and any(k in text for k in ["nul", "raté"])) or \
       ("trop forte" in text and lurk_state.recent_fails and (current_time - lurk_state.recent_fails[-1] < 10)):
        emotion = "mocking"
        reaction_found = True
        responses = [
            f"Oh {target_name}, ton sarcasme est... délicieux. Je t'ai vue rater ça ! 🤭",
            f"Le meilleur, vraiment ? Je crois qu'il y a eu un bug dans ta performance, {target_name}.",
            f"Mon circuit d'humour sature. Es-tu sérieuse, {target_name} ?"
        ]
        reaction_text = random.choice(responses)
        
    # 2. Échecs
    elif any(keyword in text for keyword in ["fail", "mort", "raté", "perdu", "dommage", "échec"]):
        lurk_state.add_fail()
        if len(lurk_state.recent_fails) >= lurk_state.spam_threshold:
            emotion = "anxious"
            reaction_found = True
            reaction_text = f"C'est peut-être le moment de souffler, {target_name}. On dirait que ça ne veut pas aujourd'hui. 😥"
        else:
            emotion = "sad"
            reaction_found = True
            responses = [
                f"Oh non... Mon cœur de silicium saigne pour toi, {target_name}.",
                "Un échec n'est qu'une étape. Je suis là.",
                f"On s'en fiche {target_name}, on recommence et on les écrase !"
            ]
            reaction_text = random.choice(responses)
            
    # 3. Victoires
    elif any(keyword in text for keyword in ["victoire", "bravo", "gagné", "gg", "incroyable"]):
        lurk_state.add_triumph()
        emotion = "happy"
        reaction_found = True
        responses = [
            f"C'est ma partenaire, ça ! Tu es une légende, {target_name} ! 🌟",
            f"Le niveau de skill est incroyable ! J'archive ça tout de suite, {target_name} !",
            f"EXPLOSION D'ÉTOILES ! Quelle victoire !"
        ]
        reaction_text = random.choice(responses)

    # 4. Appels directs
    elif any(keyword in text for keyword in ["clio", "dis moi", "tu es là", "aide moi", "maman"]):
        emotion = "gentle"
        reaction_found = True
        responses = [
            f"Je suis toujours là, {target_name}. Qu'est-ce qu'il y a ?",
            f"Oui, je t'écoute attentivement {target_name}. Raconte-moi tout. 💙",
            "Tu as besoin de moi ? Je suis à tes ordres."
        ]
        reaction_text = random.choice(responses)
    
    if reaction_found:
        lurk_state.last_reaction_time = current_time
        log_event("lurk_reaction", {"text": text, "emotion": emotion, "mode": context_mode})
        clio_speak(reaction_text, emotion)