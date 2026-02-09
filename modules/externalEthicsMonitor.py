# Fichier : modules/externalEthicsMonitor.py

import logging
from typing import Dict, Any, Tuple
# Importe la classe de règles que vous avez déjà créée (anciennement EthicsProfile)
from .ethicsProfile import EthicsProfile as EthicsRules 
from .module import Module 

logger = logging.getLogger('ExternalEthicsMonitor')

class ExternalEthicsMonitor(Module):
    """
    Module pour le filtrage de premier niveau (Dogwhistle, Sarcasme simple).
    Utilise EthicsRules pour valider le contenu avant qu'il n'atteigne le LLM.
    """
    def __init__(self, signals, enabled: bool = True):
        super().__init__(signals, enabled)
        
        # 🚨 Utilise la classe de règles existante (le fichier ethics_patterns.json)
        self.rules = EthicsRules(patterns_filename="ethics_patterns.json")
        self.API = self.API(self)

    # 🚀 NOUVELLE FONCTION : Interface pour la validation du Prompter
    def validate_input(self, text: str) -> Tuple[bool, str, Dict[str, List[str]]]:
        """
        Valide le texte par rapport aux règles de bannissement.
        Retourne (is_safe, reason, terms_flagged).
        """
        if not self.enabled:
            return True, "Module désactivé", {}

        # 1. Validation primaire (rejet contextuel par phrase)
        is_safe, reason = self.rules.validate(text)

        if not is_safe:
            # 2. Si non sécurisé, trouve les termes exacts pour le Prompter
            terms = self.rules.flagged_terms(text)
            logger.warning(f"[ETHICS REJECT] {reason}: {terms}")
            return False, reason, terms
        
        # 3. Si sécurisé, vérifie s'il y a des termes paradoxaux pour l'annotation
        # NOTE: La logique paradoxale est gérée par le Prompter et paradox.py.
        
        return True, "OK", {}


    class API:
        def __init__(self, outer: 'ExternalEthicsMonitor'):
            self.outer = outer

        def check_safety(self, text: str) -> Tuple[bool, str, Dict[str, List[str]]]:
            """Point d'entrée pour la validation externe."""
            return self.outer.validate_input(text)