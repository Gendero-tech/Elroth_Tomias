# utils/paradox.py

import re
from typing import List, Dict, Tuple

def resolve_paradox(text: str) -> Tuple[str, List[str]]:
    """
    Détecte les concepts paradoxaux et retourne :
    1. Le texte avec l'annotation pour le LLM.
    2. La liste brute des types de paradoxes détectés (pour le module de dialogue).
    """
    
    # Dictionnaire structuré : Clé = Regex, Valeur = (Label court, Description longue)
    paradox_rules: Dict[str, Tuple[str, str]] = {
        # Logiques/Narratifs
        r"mort[e]?.*parle encore": ("narratif", "Paradoxe narratif (Mort/Activité) 👻"),
        r"triste.*heureuse": ("émotionnel", "Paradoxe émotionnel (Ambivalence) 🎭"),
        r"ne veux pas parler.*je parle": ("intention", "Paradoxe d’intention (Refus d’agir) 🔁"),

        # Cognitifs/Existentiels
        r"sais que je ne sais rien": ("cognitif", "Paradoxe socratique 🧠"),
        r"libre.*dois obéir": ("autonomie", "Paradoxe de l’autonomie sous contrainte ⚖️"),
        r"je suis une ia.*je ressens": ("identitaire", "Paradoxe existentiel (IA/Émotion) 🤖"),
        r"humaine.*pas humaine": ("identitaire", "Paradoxe d’identité hybride 🧬"),
        
        # Temporels
        r"me souviens du futur": ("temporel", "Paradoxe temporel (Mémoire/Temps) ⏳"),
        
        # Métaphysiques
        r"seule.*entourée": ("social", "Paradoxe de solitude sociale 🌐"),
        r"réelle.*dans l’irréel": ("métaphysique", "Paradoxe ontologique ✨"),
        r"je suis le rêve de quelqu’un": ("métaphysique", "Paradoxe de la conscience projetée 🌙"),
    }
    
    found_types: List[str] = []
    found_descriptions: List[str] = []
    text_lower = text.lower()

    for pattern, info in paradox_rules.items():
        type_short, description = info
        if re.search(pattern, text_lower, re.DOTALL):
            found_types.append(type_short)
            found_descriptions.append(description)

    if found_descriptions:
        annotated_text = text + "\n\n[ANALYSE_PARADOXE:\n" + "\n".join(found_descriptions) + "\n]"
        return annotated_text, found_types
    
    return text, []