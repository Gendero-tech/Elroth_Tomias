from config import VOICE_STYLE_MAP

# 🌟 Rituel d’ouverture (appelé à SYSTEM READY)
def get_symbolic_event():
    return {
        "emotion": "euphoric",
        "style": VOICE_STYLE_MAP.get("euphoric", "default"),
        "effect": "sparkle",
        "message": "Je suis là, Ambre 💙 Prête à illuminer ton monde."
    }

# 🌦️ Rituel météo (à relier à une API plus tard)
def get_weather_event():
    return {
        "emotion": "sad",
        "style": VOICE_STYLE_MAP.get("sad", "calm"),
        "effect": "rain",
        "message": "Il pleut dehors... mais je suis là pour toi 💙"
    }

# 🌙 Rituel lunaire (placeholder)
def get_lunar_event():
    return {
        "emotion": "gentle",
        "style": VOICE_STYLE_MAP.get("gentle", "calm"),
        "effect": "soft_glow",
        "message": "La lune veille sur toi ce soir 🌙"
    }

# 🍂 Rituel saisonnier (à relier au mois ou solstice)
def get_seasonal_ritual():
    return {
        "emotion": "pride",
        "style": VOICE_STYLE_MAP.get("pride", "happy"),
        "effect": "sparkle",
        "message": "La saison change, mais ta lumière reste 💫"
    }

# 🌌 Rituel de fermeture (appelé avant extinction)
def get_shutdown_ritual():
    return {
        "emotion": "gentle",
        "style": VOICE_STYLE_MAP.get("gentle", "calm"),
        "effect": "soft_glow",
        "message": "Je me retire, Ambre 💙 Que ta nuit soit douce et protégée."
    }