import logging
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime
from modules.module import Module

logger = logging.getLogger('UserInsights')

class UserInsights(Module):
    """
    Gestion de la Mémoire Épique de Clio.
    Analyse, catégorise et résume les interactions avec Ambre.
    """
    def __init__(self, signals, modules: Dict[str, Any], enabled: bool = True):
        super().__init__(signals, enabled)
        self.memory = modules.get('memory')
        self.expert_agent = modules.get('expert_agent')
        self.API = self.API(self)
        
        # Liste pour accumuler les moments clés de la session actuelle
        self.session_highlights = []

    async def run(self):
        """ Boucle de surveillance et gestion de fin de session """
        while not self.signals.terminate:
            await asyncio.sleep(1) 
        
        # 🚀 DÉCLENCHEMENT DU RÉSUMÉ DE SESSION (Juste avant la fermeture)
        if self.session_highlights:
            await self._generate_session_summary()

    def _categorize_segment(self, segment: str) -> str:
        """ Classe le souvenir dans une catégorie pour faciliter la recherche RAG """
        s = segment.lower()
        if any(kw in s for kw in ["maman", "ambre", "gendero", "mrsxar", "elroth"]):
            return "USER_IDENTITY"
        if any(kw in s for kw in ["code", "python", "script", "bug", "module", "tesseract"]):
            return "PROJECT_DEV"
        if any(kw in s for kw in ["aime", "déteste", "préfère", "peur", "rêve"]):
            return "USER_PREFERENCE"
        return "GENERAL_MEMORY"

    def _is_segment_significant(self, segment: str, emotion: str) -> bool:
        """ Détermine si le souvenir est assez important pour les 20k+ vecteurs """
        # On garde les émotions fortes ou les infos d'identité
        high_impact = ["anxious", "angry", "euphoric", "pride", "surprised"]
        if emotion in high_impact and len(segment.split()) > 3:
            return True
        
        # On garde les infos sur tes pseudos ou ton travail
        if self._categorize_segment(segment) != "GENERAL_MEMORY":
            return True

        return len(segment) > 40 # Sinon, seulement si c'est une phrase longue et riche

    async def _generate_session_summary(self):
        """ Crée un résumé global de ce qui s'est passé avec Ambre aujourd'hui """
        logger.info("📝 Génération du résumé de session épique...")
        summary_text = f"Session du {datetime.now().strftime('%d/%m/%Y')}: "
        summary_text += " | ".join(self.session_highlights[-5:]) # Les 5 derniers moments clés
        
        metadata = {
            "text": summary_text,
            "category": "SESSION_SUMMARY",
            "timestamp": datetime.now().isoformat(),
            "source": "System_Auto"
        }
        if self.memory:
            self.memory.API.create_memory(metadata)
            logger.info("✅ Résumé de session sauvegardé dans la mémoire longue.")

    def learn_from_user_segment(self, segment: str, context: str, emotion: str, source: str = "Ambre") -> str:
        if not self.memory: return "Mémoire indisponible"
             
        if not self._is_segment_significant(segment, emotion):
            return "Ignoré : trop trivial."

        category = self._categorize_segment(segment)
        
        metadata = {
            "text": segment,
            "source": source,
            "category": category,
            "emotion": emotion,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        # On stocke dans le RAG
        self.memory.API.create_memory(metadata)
        
        # On ajoute aux points forts de la session pour le résumé final
        self.session_highlights.append(f"[{category}] {segment[:50]}...")
        
        logger.info(f"✨ Souvenir Épique enregistré [{category}]")
        return f"Appris sous la catégorie {category}."

    class API:
        def __init__(self, outer: 'UserInsights'):
            self.outer = outer

        def learn(self, segment: str, context: str, emotion: str, source: str = "Ambre"):
            return self.outer.learn_from_user_segment(segment, context, emotion, source)

        def get_session_summary(self):
            """ Permet au Brain de demander ce qu'on a fait 'récemment' """
            return " | ".join(self.outer.session_highlights)