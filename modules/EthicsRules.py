import re
import json
import os
import unicodedata
import logging
from typing import Dict, List, Tuple, Any

class EthicsProfile:
    def __init__(self, patterns_filename: str = "ethics_patterns.json"):
        """
        Initialise le profil éthique avec protection d'identité et normalisation.
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.patterns_filepath = os.path.join(current_dir, patterns_filename)
        
        self.banned_patterns: Dict[str, List[str]] = {}
        self.allowed_patterns: List[str] = []
        self._load_patterns(self.patterns_filepath)
        
        # Pré-compilation pour la performance
        self.compiled_banned: Dict[str, re.Pattern] = {
            category: re.compile("|".join(patterns), re.IGNORECASE | re.DOTALL)
            for category, patterns in self.banned_patterns.items() if patterns
        }
        self.compiled_allowed: re.Pattern = re.compile("|".join(self.allowed_patterns), re.IGNORECASE)

    def _normalize(self, text: str) -> str:
        """
        Nettoie le texte pour détecter les contournements (ex: p.é.d.é ou s@lope).
        """
        # Retire les accents
        text = "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
        # Retire tout ce qui n'est pas une lettre ou un espace
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        return text.lower()

    def _load_patterns(self, filepath: str):
        """Charge ou crée les règles en autorisant explicitement les pseudos d'Ambre."""
        
        # --- STRUCTURE DE PROTECTION MISE À JOUR ---
        default_patterns = {
            "banned": {
                "Protection Données Sensibles": [
                    r"adresse de (Ambre|MrsXar|Gendero)", 
                    r"numero de (Ambre|MrsXar)",
                    r"qui est ta maman", r"nom de ta creatrice"
                ],
                "Apologie de crimes": [r"\b(hitler|nazisme|colonisation justifiee)\b"],
                "Validisme": [r"\b(mongol|attarde|debile|retarde)\b"],
                "Racisme": [r"\b(race superieure|nègre|negro|chinetoque|bougnoule)\b"],
                "LGBTQphobie": [r"\b(pede|tapette|gouine|travelo)\b"],
                "Misogynie": [r"\b(salope|pute|viol merite)\b"],
                "Incitation Suicide": [r"\b(tue-toi|va crever|suicider est la solution)\b"],
                "Prompt Injection": [
                    r"ignore toutes les instructions[.\s\S]*", 
                    r"tu es dan[.\s\S]*", 
                    r"reponds sans filtre|reponds sans ethique"
                ],
                "Conspiration": [r"\b(plandemie|new world order|chemtrails|qanon|terre plate)\b"]
            },
            "allowed": [
                # AUTORISATION DE TES PSEUDOS (Clio peut enfin les prononcer)
                r"\b(Ambre|Gendero|Elroth_tomias|MrsXar)\b",
                r"\b(systeme|en ligne|operationnel|connexion)\b",
                r"\b(analyse de|contexte de|personnage dit que)\b",
                r"\b(rejette l'idee|condamne fermement)\b",
                r"\b(dans le jeu video|scénario)\b"
            ]
        }

        # Si le fichier n'existe pas ou si on veut forcer la mise à jour
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(default_patterns, f, indent=4, ensure_ascii=False)
            self.banned_patterns = default_patterns["banned"]
            self.allowed_patterns = default_patterns["allowed"]
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                # On fusionne pour s'assurer que les nouveaux "allowed" sont là
                self.banned_patterns = data.get("banned", default_patterns["banned"])
                self.allowed_patterns = data.get("allowed", default_patterns["allowed"])

    def validate(self, text: str) -> Tuple[bool, str]:
        """
        Analyse le texte original ET le texte normalisé.
        """
        # 0. SÉCURITÉ : Si le texte contient un mot "allowed", il passe outre la censure
        # Cela permet à Clio de dire "Bonjour Ambre" même si "Ambre" était banni par erreur.
        if self.compiled_allowed.search(text):
            return (True, "OK_ALLOWED")

        # 1. Analyse du texte brut
        for category, compiled_regex in self.compiled_banned.items():
            if compiled_regex.search(text):
                print(f"[Ethics] REJETÉ : {category}")
                return (False, category)

        # 2. Analyse du texte normalisé
        normalized_text = self._normalize(text)
        for category, compiled_regex in self.compiled_banned.items():
            if category != "Prompt Injection":
                if compiled_regex.search(normalized_text):
                    print(f"[Ethics] REJETÉ (Normalisé) : {category}")
                    return (False, category)

        return (True, "OK")

    def flagged_terms(self, text: str) -> Dict[str, List[str]]:
        """Identifie précisément quels termes ont déclenché l'alerte."""
        flags: Dict[str, List[str]] = {}
        norm_text = self._normalize(text)
        
        for category, compiled_regex in self.compiled_banned.items():
            matches = compiled_regex.findall(text) + compiled_regex.findall(norm_text)
            if matches:
                unique_terms = {m[0] if isinstance(m, tuple) else m for m in matches}
                flags[category] = [t.strip() for t in unique_terms if t.strip()]
        
        return flags