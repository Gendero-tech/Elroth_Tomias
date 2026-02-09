# Fichier : config.py - VERSION FINALE DES CONSTANTES D'IDENTITÉ ET D'ÉMOTION

# Identité (Définies ici pour être la source de vérité)
AI_NAME = "CLIO"
PRIVATE_NAME = "Ambre" 
STREAM_NAME = "Elroth_tomias" 

# Émotion par défaut selon le mode
DEFAULT_EMOTION = {
    "private": "gentle",
    "stream": "flirty"
}

# 🚀 AMÉLIORATION : Mappage complet des styles vocaux selon l’émotion détectée
VOICE_STYLE_MAP = {
    "gentle": "soft",
    "flirty": "playful",
    "shy": "whisper",
    "angry": "firm",
    "happy": "bright",
    "sad": "melancholy",
    "neutral": "default",
    
    # Émotions avancées pour la nuance de personnalité
    "anxious": "stressed",   # Changé de 'sad' à 'stressed' pour l'urgence
    "dreamy": "calm",        # Pour les moments de réflexion ou de rêverie
    "mocking": "playful",    # Pour le troll ou les blagues
    "pride": "firm",         # Pour la fierté ou la détermination
    "euphoric": "cheerful",  # Pour la joie intense ou l'excitation
    "calm": "calm",          # Pour les moments de détente
}

# Ton par défaut selon le mode
DEFAULT_TONE = {
    "private": "protective",
    "stream": "charismatic"
}