# Fichier : modules/legalAdvisor.py

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, Tuple

from modules.module import Module

logger = logging.getLogger('LegalAdvisor')

class LegalAdvisor(Module):
    """
    Expert spécialisé dans la conformité légale, le droit du travail et la fiscalité de premier niveau.
    Délègue la recherche et l'analyse de documents à l'ExpertAgent.
    """
    def __init__(self, signals, modules: Dict[str, Any], enabled: bool = True):
        super().__init__(signals, enabled)
        self.modules = modules
        self.API = self.API(self)
        
        # Dépendances critiques
        self.expert_agent = self.modules.get('expert_agent')
        self.knowledge = self.modules.get('knowledge') # Base de connaissance légale (RAG)
        
        logger.info("⚖️ Conseiller Légal initialisé.")

    async def run(self):
        # Module réactif : pas de boucle continue nécessaire.
        pass

    def _get_document_context(self, query: str, top_k: int = 3) -> str:
        """
        Récupère les lois, décrets, ou articles pertinents de la base de connaissance 
        (Knowledge RAG) pour fournir une source à l'ExpertAgent.
        """
        if not self.knowledge:
            return "Base de connaissance légale non disponible."

        # Récupère les faits les plus similaires dans la base statique
        results = self.knowledge.API.search_rag(query, top_k=top_k)
        
        context = []
        if results:
            context.append("--- ARTICLES DE LOI ET RÉGLEMENTATIONS RÉCUPÉRÉS ---")
            for i, item in enumerate(results):
                context.append(f"Source {i+1} ({item.get('source', 'RAG')}): {item.get('text', 'Texte non trouvé')}")
            context.append("-----------------------------------------------------")
        
        return "\n".join(context)

    def _analyze_query_with_llm(self, full_prompt: str) -> str:
        """
        Envoie le prompt enrichi à l'ExpertAgent (Gemini/GPT) pour l'analyse finale.
        """
        if not self.expert_agent:
            return "Expert Agent non disponible pour l'analyse LLM."

        try:
            # Utilise l'appel Gemini pour sa capacité à gérer de longs contextes RAG
            result = self.expert_agent.API.call_gemini_for_science(full_prompt)
            return result
        except Exception as e:
            return f"Erreur d'analyse par l'expert LLM: {e}"


    # --- API (Pour les délégations LLM et les analyses) ---
    class API:
        def __init__(self, outer: 'LegalAdvisor'):
            self.outer = outer

        def provide_legal_advice(self, user_query: str) -> str:
            """
            Fournit des conseils légaux de premier niveau sur une question.
            """
            # 1. Récupération du contexte légal (Lois RAG)
            context = self.outer._get_document_context(user_query)
            
            # 2. Construction du prompt d'ingénierie pour l'expert
            prompt = (
                f"Tu es un conseiller juridique expérimenté. Analyse la requête de l'utilisateur "
                f"en utilisant le contexte légal fourni. Si le contexte est vide, utilise tes connaissances générales.\n\n"
                f"{context}\n\n"
                f"Requête Utilisateur : {user_query}\n"
                f"Réponds avec des étapes claires, en citant la source si possible. Termine toujours par une mise en garde légale (Disclaimer)."
            )
            
            # 3. Délégation à l'ExpertAgent
            analysis_result = self.outer._analyze_query_with_llm(prompt)
            
            return f"[CONSEIL LÉGAL] {analysis_result}"

        def analyze_tax_status(self, business_type: str, revenue: float) -> str:
            """
            Analyse et explique les obligations fiscales et sociales (URSSAF) en fonction 
            du type d'entreprise et du revenu (simulation réelle).
            """
            
            # Récupération des données RAG sur URSSAF et Impôts
            query = f"Taux URSSAF et fiscalité pour {business_type} avec {revenue}€ de revenu."
            legal_context = self.outer._get_document_context(query, top_k=5)
            
            # Délégation de la tâche de calcul et d'explication au LLM
            prompt = (
                f"Tu es un fiscaliste. Analyse le statut '{business_type}' pour un revenu de {revenue}€ en utilisant les lois suivantes :\n"
                f"{legal_context}\n"
                f"Calcule les charges sociales (URSSAF) et fiscales principales (taux réels simplifiés) et explique les prochaines étapes de déclaration. Sois précis et prudente."
            )
            
            analysis_result = self.outer._analyze_query_with_llm(prompt)
            
            return f"[ANALYSE FISCALE/URSSAF] {analysis_result}"