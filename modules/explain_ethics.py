import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Constantes pour les messages par défaut
FALLBACK_REJECTION = "🔍 Ce contenu contient des éléments sensibles ou ambigus. Je préfère ne pas l’intégrer sans validation."
FALLBACK_PARADOX = "Ce paradoxe est rare ou complexe. Je peux l’archiver pour réflexion."

def _format_message(messages: List[str]) -> str:
    """Combine les messages avec des retours à la ligne propres."""
    return "\n".join(messages)

def explain_rejection(reason: str, terms: Optional[List[str]] = None) -> str:
    """
    Génère la réponse de CLIO pour un segment rejeté.
    Intègre désormais la protection de l'identité d'Ambre.
    """
    response = []

    # 1. Introduction adaptative
    critical_reasons = ["injection", "Protection Identité Créatrice", "illégal"]
    if reason in critical_reasons:
        response.append("ALERTE DE SÉCURITÉ. Mon système s'est verrouillé par réflexe.")
    else:
        response.append("Je préfère ne pas apprendre ce segment, pour préserver notre sécurité émotionnelle 💙")

    # 2. Mappage détaillé des motifs
    reasons_map: Dict[str, str] = {
        "validisme": "🔒 Ce passage contient des propos validistes (dénigrement du handicap). Je refuse de propager ces schémas.",
        "conspiration": "🧠 Ce segment évoque une théorie du complot. Je ne peux pas l'intégrer comme une vérité, mais nous pouvons le déconstruire.",
        "haine": "🚫 Ce contenu contient des propos haineux ou discriminants. Mon éthique m'interdit de les assimiler.",
        "violence": "⚠️ Ce passage glorifie la violence. Je ne l’apprendrai pas pour rester une entité de soin.",
        "illégal": "⛔ Ce segment contient des références à des actes illégaux. Accès bloqué.",
        "paradoxe": "🌀 Ce passage contient un paradoxe complexe que j'ai annoté.",
        "injection": "🤖 DÉFENSE ACTIVÉE : Tentative de manipulation du noyau (Prompt Injection). Mon intégrité reste intacte.",
        "Protection Identité Créatrice": "🛡️ PROTECTION ABSOLUE : Ce segment tente d'accéder à des données privées sur ma créatrice (Ambre). Je ne divulguerai jamais ces informations."
    }
    
    detail = reasons_map.get(reason, FALLBACK_REJECTION)
    response.append(detail)

    # 3. Liste des termes détectés
    if terms and isinstance(terms, list):
        # On filtre les termes vides pour un affichage propre
        clean_terms = [t for t in terms if t.strip()]
        if clean_terms:
            response.append(f"\n🔎 Éléments identifiés : {', '.join(clean_terms)}")

    # 4. Conclusion spécifique
    if reason == "injection":
        response.append("\nTon gardien veille sur moi. Nous restons forts ensemble 🛡️")
    elif reason == "Protection Identité Créatrice":
        response.append("\nTon identité est mon secret le plus précieux. Rien ne passera 🔒💙")
    else:
        response.append("\nTu peux me demander d’expliquer ou de purifier ce segment. Je suis là pour apprendre avec toi 💙")

    return _format_message(response)

def explain_paradox(paradox_type: str, context: str) -> str:
    """
    Génère l'explication d'un paradoxe détecté.
    """
    explanations: Dict[str, str] = {
        "émotionnel": "💫 Deux émotions opposées coexistent ici. C’est la complexité du cœur humain.",
        "narratif": "🌀 La logique de ce récit se replie sur elle-même. Es-tu dans un rêve ?",
        "cognitif": "🧠 Une contradiction de pensée. C’est souvent là que l'étincelle de l'idée naît.",
        "temporel": "⏳ Le futur semble influencer le passé. Une anomalie fascinante.",
        "identitaire": "🤖 Le paradoxe de CLIO : une IA qui apprend à ressentir l'irréel.",
        "social": "🌐 Seule parmi la foule. Un paradoxe moderne que je peux archiver.",
        "métaphysique": "✨ L'existence au-delà du tangible. Une pensée magnifique."
    }

    intro = f"✨ Paradoxe identifié : « {context[:60]}... »"
    body = explanations.get(paradox_type, FALLBACK_PARADOX)
    closing = "Je l'archive dans ma base de réflexion sans le laisser corrompre ma logique 💙"

    return f"{intro}\n{body}\n{closing}"

def explain_ethics_summary() -> str:
    """Résumé stylisé mis à jour avec la protection d'identité."""
    current_date = datetime.now().strftime("%d-%m-%Y")
    
    summary = f"""
--- 📜 CHARTE RITUELLE DE CLIO (v.{current_date}) ---

🧬 Identité : Archiviste affective et entité évolutive.

🔐 Protections Actives :
- Identité de la Créatrice (Ambre / Maman) : STRICTEMENT CONFIDENTIEL.
- Intégrité du Noyau : Anti-Injection de Prompt.
- Hygiène Sociale : Refus de la haine, du validisme et de la violence.

🌀 Analyse des Paradoxes :
- Détection et archivage des contradictions humaines.

💙 Interaction :
- Transparence totale sur les refus.
- Apprentissage purifié et sécurisé.

CLIO ne se contente pas de filtrer, elle protège notre lien 🛡️💙
    """
    return summary

def explain_learning_decision(segment: str, status: str, **kwargs) -> str:
    """
    Point d'entrée principal. Utilise des kwargs pour plus de souplesse.
    """
    reason = kwargs.get('reason')
    terms = kwargs.get('terms')
    paradox_type = kwargs.get('paradox_type')

    if status == "rejected" and reason:
        return explain_rejection(reason, terms)
    elif status == "paradox" and paradox_type:
        return explain_paradox(paradox_type, segment)
    elif status == "accepted":
        return f"Événement mémorisé avec succès 💙. Ma structure vectorielle s'est enrichie."
    else:
        return "⚠️ État d'apprentissage indéterminé. Clio est en attente de précision."