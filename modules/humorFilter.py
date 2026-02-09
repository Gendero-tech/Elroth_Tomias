# Fichier : modules/humorFilter.py

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from modules.module import Module

# 🚨 CORRECTION CRITIQUE : Importation de la classe Injection
from injection import Injection 

logger = logging.getLogger('HumorFilter')

class HumorFilter(Module):
    """
    Détecte les nuances d'humour (sarcasme, blague, autodérision) pour affiner 
    la réponse du LLM et l'expression de Clio.
    """
    # 🚀 AMÉLIORATION : Règles pondérées pour le sarcasme
    SARCASTIC_PATTERNS = {
        # Si vous dites quelque chose de très positif après un échec
        r"bravo\s+à\s+moi|je\s+suis\s+le\s+meilleur|trop\s+forte": 3,
        # Utilisation de 'vraiment' ou 'génial' sur un événement négatif
        r"vraiment\s+génial|quelle\s+chance\s+que": 2,
        # Utilisation de smiley ironique ou l'absence de majuscule
        r":\)|:p|lol|mdr": 1 
    }
    
    JOKE_PATTERNS = {
        r"\b(blague|drôle|rire|humour|sarcasme|joke)\b": "JOKE"
    }

    def __init__(self, signals, enabled: bool = True):
        super().__init__(signals, enabled)
        self.API = self.API(self)
        # Injection de prompt à haute priorité (pour le LLM)
        self.prompt_injection.priority = 180 

    def analyze_humor(self, text: str) -> Tuple[str, int]:
        """
        Analyse un texte et retourne le type d'humour détecté et un score.
        Retourne ('NONE', 0) par défaut.
        """
        text_lower = text.lower()
        sarcasm_score = 0
        
        # 1. Détection de Sarcasme (Pondéré)
        for pattern, weight in self.SARCASTIC_PATTERMS.items():
            if re.search(pattern, text_lower):
                sarcasm_score += weight
        
        if sarcasm_score >= 3:
            return "SARCASTIC", sarcasm_score
        
        # 2. Détection de Blague (Basique)
        if re.search(r"\b(blague|rire|lol|mdr)\b", text_lower):
            return "JOKE", 1
            
        return "NONE", 0

    def get_prompt_injection(self) -> Injection:
        """
        Fournit le tag de contexte Humour au LLM si un événement est détecté.
        """
        # NOTE : Ce module doit idéalement être appelé manuellement par le Prompter
        # sur le dernier message, et non via la boucle générale d'injection,
        # car il nécessite le message en temps réel.
        
        # Nous retournons l'objet d'injection pour le cas où il serait appelé.
        return self.prompt_injection

    class API:
        def __init__(self, outer: 'HumorFilter'):
            self.outer = outer

        def check_text(self, text: str) -> Tuple[str, int]:
            """Analyse le texte et stocke la conclusion dans le prompt d'injection."""
            humor_type, score = self.outer.analyze_humor(text)
            
            if humor_type != "NONE":
                 context_tag = f"[HUMOR_CONTEXT: {humor_type}, Score: {score}] Ton interlocuteur utilise l'humour. Réponds avec une nuance de moquerie ou de légèreté."
                 self.outer.prompt_injection.text = context_tag
                 logger.info(f"[HumorFilter] Détecté : {humor_type} (Score: {score})")
            else:
                 self.outer.prompt_injection.text = "" # Vide si rien n'est trouvé
                 
            return humor_type, score