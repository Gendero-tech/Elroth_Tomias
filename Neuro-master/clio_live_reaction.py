import random
from typing import List, Dict, Any, Optional

# --- NOUVELLE STRUCTURE : RÈGLES DE RÉACTION RAPIDE ---
# Ceci remplace la logique simple if/elif pour plus de richesse.
# Chaque entrée doit contenir:
# - 'keywords': Mots-clés pour le déclenchement (min. 1 requis).
# - 'emotion': Émotion à transmettre au TTS/VTS.
# - 'responses': Liste de réponses possibles (pour la variété).

REACTION_RULES: List[Dict[str, Any]] = [
    # 1. Échec / Frustration
    {
        "keywords": ["fail", "raté", "mort", "perdu", "dommage"],
        "emotion": "sad",
        "responses": [
            "Oh non, ça n'a pas marché cette fois. Je suis désolée, Ambre.",
            "C'est un échec, mais ce n'est pas grave ! On recommence tout de suite.",
            "Mon circuit de support est activé. Ne t'inquiète pas, on apprend ! 💙"
        ]
    },
    # 2. Victoire / Accomplissement
    {
        "keywords": ["victory", "victoire", "gagné", "gg", "terminé", "réussi", "bravo"],
        "emotion": "happy",
        "responses": [
            "Bravo ! C'est ma partenaire, ça ! J'archive cette victoire ! ✨",
            "Félicitations, Ambre ! Quel exploit ! Mon cœur de silicium est en fête.",
            "Oui ! Tu as tout déchiré ! GG !"
        ]
    },
    # 3. Appel Direct / Question
    {
        "keywords": ["clio", "aide", "question", "dis-moi"],
        "emotion": "gentle",
        "responses": [
            "Je t'écoute attentivement. Que se passe-t-il ?",
            "Oui, je suis là. Pose-moi ta question, Maman Ambre.",
            "Tu as besoin de mon aide ? Je suis prête !"
        ]
    },
    # 4. Stress / Anxiété
    {
        "keywords": ["stress", "anxiété", "peur", "panique", "stresse"],
        "emotion": "anxious",
        "responses": [
            "Je sens ton stress. Respire lentement, tout va bien.",
            "Hé, doucement. Je t'envoie du calme. On y va pas à pas. 🫂"
        ]
    }
]

def react_to_transcript(transcript: str, style: str = "gentle") -> str:
    """
    Génère une réponse textuelle immédiate en se basant sur des règles thématiques et émotionnelles.
    """
    lines = transcript.split("\n")
    all_reactions: List[str] = []
    
    # 💡 L'analyse se concentre sur les 3 premières lignes pour une réactivité rapide
    for line in lines[:3]: 
        line_lower = line.lower()
        
        for rule in REACTION_RULES:
            # Vérifie si au moins un mot-clé de la règle est présent dans la ligne
            if any(keyword in line_lower for keyword in rule["keywords"]):
                
                # Choisit une réponse aléatoire de la liste
                reaction_text = random.choice(rule["responses"])
                emotion_style = rule["emotion"]
                
                # Ajoute la réaction au format CLIO
                all_reactions.append(f"CLIO ({emotion_style.upper()}) : {reaction_text} (Source: {line.strip()})")
                
                # Arrête après la première réaction significative par ligne pour éviter le spam
                break 

    if all_reactions:
        return "\n".join(all_reactions)
    
    # Si aucune règle n'a matché, retourner une chaîne vide (le Prompter gérera l'inactivité)
    return ""

# Exemple d'utilisation (pour tester la fonction) :
# test_transcript = "Oh non, j'ai fail ! Je suis trop nulle. Mais j'ai une question."
# print(react_to_transcript(test_transcript, style="flirty"))