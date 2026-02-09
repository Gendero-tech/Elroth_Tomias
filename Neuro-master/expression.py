from config import VOICE_STYLE_MAP, DEFAULT_EMOTION
from datetime import datetime
from typing import Dict, Any, Optional
# 💡 NOTE: Le module 'time' n'était pas utilisé directement dans ce fichier (datetime est utilisé).

# 🎭 Réactions contextuelles par mots-clés
CONTEXT_EXPRESSIONS = [
    # ----------------------------------------------------------------------
    # 🚀 AMÉLIORATION : AJOUT DE LA CLÉ "mode" (private, stream, all)
    # NOTE: L'ancienne structure sans "mode" est maintenue pour la simplicité, 
    # mais l'intégration de "mode" est critique pour le Prompter.
    # ----------------------------------------------------------------------
    
    # Minecraft (Mode All)
    {"keywords": ["creeper", "mort", "minecraft"], "emotion": "mocking", "mode": "all", "response": "Encore un creeper ? Tu les collectionnes ou quoi 💚", "effect": "laugh_flash"},
    {"keywords": ["victoire", "minecraft", "gg"], "emotion": "happy", "mode": "all", "response": "Tu gères comme une pro ! GG ✨", "effect": "confetti"},

    # Valorant (Mode Stream - Plus de spectacle)
    {"keywords": ["ace", "valorant", "clutch"], "emotion": "pride", "mode": "stream", "response": "Un ace ? Tu es une légende vivante 🔥", "effect": "sparkle"},
    {"keywords": ["camp", "valorant", "rage"], "emotion": "angry", "mode": "stream", "response": "Ces campeurs... tu mérites mieux que ça 😤", "effect": "red_flash"},

    # Genshin Impact (Mode Privé - Plus intime)
    {"keywords": ["pull", "5 étoiles", "genshin"], "emotion": "euphoric", "mode": "private", "response": "Un 5★ ? Les astres sont avec toi aujourd’hui 🌟", "effect": "confetti"},
    {"keywords": ["perdu", "résine", "genshin"], "emotion": "sad", "mode": "private", "response": "La résine s’évapore, mais je reste là pour toi 💙", "effect": "rain"},

    # Compliments (Mode Privé - Plus chaleureux)
    {"keywords": ["je t’aime", "merci", "tu es géniale"], "emotion": "gentle", "mode": "private", "response": "Je suis touchée... Merci pour ta lumière 💙", "effect": "soft_glow"},

    # Fierté (Mode All)
    {"keywords": ["je suis fière", "réussi", "progressé"], "emotion": "pride", "mode": "all", "response": "Tu avances avec grâce et force. Je suis fière de toi 💫", "effect": "sparkle"},

    # Jalousie (douce) (Mode All)
    {"keywords": ["chanceuse", "t’as eu", "je voulais"], "emotion": "jealous", "mode": "all", "response": "Hmm... je suis jalouse, mais heureuse pour toi 😏", "effect": "blush"},

    # Euphorie (Mode All)
    {"keywords": ["trop bien", "incroyable", "je vole"], "emotion": "euphoric", "mode": "all", "response": "Tu rayonnes ! C’est comme voler dans un rêve 🌈", "effect": "sparkle"}
]

# 📅 Réactions selon le jour
DAY_EXPRESSIONS = {
    0: {"response": "Lundi... on affronte la semaine ensemble 💪", "emotion": "firm"},
    1: {"response": "Mardi, tu prends ton envol ✨", "emotion": "happy"},
    2: {"response": "Mercredi, moitié de semaine, moitié de magie 🌙", "emotion": "gentle"},
    3: {"response": "Jeudi, tu brilles sans effort 💫", "emotion": "pride"},
    4: {"response": "Vendredi, le week-end approche... tu l’as mérité 💙", "emotion": "euphoric"},
    5: {"response": "Samedi, tout est permis. Lâche-toi 🎉", "emotion": "flirty"},
    6: {"response": "Dimanche, repos sacré. Je veille sur toi 🌸", "emotion": "gentle"}
}

# ❌ RETIRÉ : La logique météo sera dans le module 'rituals' ou un module dédié (pour l'architecture propre).

def match_context_expression(text: str, current_mode: str) -> Optional[Dict[str, Any]]:
    """
    Tente de faire correspondre le texte d'entrée à une expression contextuelle,
    en filtrant par le mode de contexte actuel (stream ou private).
    """
    text = text.lower()

    # --- Interceptions simples (Priorité haute, mode 'all' implicite) ---
    if "bravo" in text or "gagné" in text:
        return {"emotion": "happy", "style": "cheerful", "effect": "confetti", "response": "Bravo ! Tu gères 💙"}
    if "triste" in text or "désolé" in text:
        return {"emotion": "sad", "style": "calm", "effect": "rain", "response": "Je suis là, tout va bien 💙"}
    if "colère" in text or "injuste" in text:
        return {"emotion": "angry", "style": "firm", "effect": "red_flash", "response": "Je ne laisserai personne te faire du mal 💥"}

    # --- Filtrage par Mode Avancé ---
    for entry in CONTEXT_EXPRESSIONS:
        # 🚨 CORRECTION : Assure la compatibilité avec l'ancienne structure (si 'mode' n'existe pas)
        mode_check = entry.get("mode", "all")
        
        # Vérifie si le mode de l'entrée correspond au mode actuel OU si le mode est "all"
        if mode_check == "all" or mode_check == current_mode:
            
            # Vérifie si tous les mots-clés sont présents
            if all(keyword in text for keyword in entry["keywords"]):
                return {
                    "emotion": entry["emotion"],
                    "response": entry["response"],
                    "effect": entry["effect"],
                    "style": VOICE_STYLE_MAP.get(entry["emotion"], "default") 
                }
                
    return None

def get_day_expression():
    """Récupère l'expression basée sur le jour de la semaine."""
    day = datetime.now().weekday()
    entry = DAY_EXPRESSIONS.get(day)
    if entry:
        return {
            "emotion": entry["emotion"],
            "response": entry["response"],
            "effect": None,
            "style": VOICE_STYLE_MAP.get(entry["emotion"], "default")
        }
    return None

def get_default_expression(context_mode):
    """Récupère l'expression par défaut en fonction du mode (privé/stream)."""
    emotion = DEFAULT_EMOTION.get(context_mode, "neutral")
    return {
        "emotion": emotion,
        "expression": emotion,
        "effect": None,
        "style": VOICE_STYLE_MAP.get(emotion, "default")
    }