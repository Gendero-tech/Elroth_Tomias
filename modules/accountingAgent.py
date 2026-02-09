# Fichier : modules/accountingAgent.py

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, Tuple
from modules.module import Module

logger = logging.getLogger('AccountingAgent')

class AccountingAgent(Module):
    """
    Expert spécialisé dans la comptabilité, la fiscalité (impôts/URSSAF) et la gestion
    financière de premier niveau.
    Délègue les analyses complexes à l'ExpertAgent.
    """
    def __init__(self, signals, modules: Dict[str, Any], enabled: bool = True):
        super().__init__(signals, enabled)
        self.modules = modules
        self.API = self.API(self)
        
        # Dépendances critiques
        self.expert_agent = self.modules.get('expert_agent')
        self.knowledge = self.modules.get('knowledge') # Pour les documents juridiques (RAG)
        
        # Mémorisation des dernières métriques pour le contexte
        self.last_financial_metrics: Dict[str, Union[int, float]] = {}
        
        # 💡 Enregistrement d'une action pour l'optimisation des ressources
        if self.expert_agent and hasattr(self.expert_agent.API, 'add_expert_action'):
             # Permet à Clio de demander "Fais ma déclaration URSSAF"
             # (Nous devrons ajouter cette méthode d'enregistrement à ExpertAgent.py)
             pass 
        
        logger.info("💰 Agent Comptable initialisé.")

    async def run(self):
        # Ce module n'a pas besoin d'une boucle continue, il réagit aux délégations LLM.
        pass

    def _analyze_document_with_llm(self, document_text: str, specific_query: str) -> str:
        """
        Envoie un document ou un problème complexe à l'ExpertAgent (Gemini/GPT) pour analyse.
        """
        if not self.expert_agent:
            return "Expert Agent non disponible pour l'analyse."

        # Construction du prompt d'ingénierie pour l'expert
        prompt = (
            f"Tu es un expert comptable et fiscaliste français. Analyse le document ou le contexte suivant :\n\n"
            f"--- DOCUMENT/CONTEXTE ---\n{document_text}\n-------------------------\n\n"
            f"Tâche : {specific_query}. Fournis une réponse claire, concise et basée sur le droit français (si applicable)."
        )
        
        try:
            # Utilise l'appel Gemini pour sa capacité à gérer de longs contextes
            result = self.expert_agent.API.call_gemini_for_science(prompt)
            return result
        except Exception as e:
            return f"Erreur d'analyse par l'expert LLM: {e}"

    # --- API (Pour les délégations LLM et les autres modules) ---
    class API:
        def __init__(self, outer: 'AccountingAgent'):
            self.outer = outer

        def optimize_stockage(self, current_inventory: Dict[str, int]) -> str:
            """
            Analyse les niveaux de stock et propose des ajustements pour l'optimisation.
            Ceci est une simulation de la gestion des stocks d'une entreprise.
            """
            
            stock_value = sum(qty * 10 for item, qty in current_inventory.items()) # Valeur simulée
            
            if stock_value > 5000:
                suggestion = "L'inventaire est trop élevé. Suggestion: Vendre l'excédent de 'Widget C' pour libérer du capital."
            else:
                 suggestion = "L'inventaire est stable. Aucun ajustement majeur requis."
                 
            return f"[Compta - Stock] Valeur Totale du Stock Estimée: {stock_value}€. {suggestion}"

        def calculate_urssaf(self, revenue: float) -> str:
            """
            Simule le calcul de l'URSSAF et des impôts (simplifié) pour un micro-entrepreneur.
            """
            urssaf_rate = 0.22 # Taux simulé
            tax_rate = 0.017 # Taux impôt libératoire
            
            urssaf_due = revenue * urssaf_rate
            tax_due = revenue * tax_rate
            
            result = (f"Revenu déclaré: {revenue:.2f}€. "
                      f"Montant URSSAF estimé (22%): {urssaf_due:.2f}€. "
                      f"Montant Impôts estimé (1.7%): {tax_due:.2f}€. "
                      f"Total à payer: {(urssaf_due + tax_due):.2f}€."
                      f"Veuillez consulter un professionnel pour confirmation.")
                      
            return result

        def analyze_legal_document(self, document_text: str, query: str) -> str:
            """
            Analyse un document légal pour répondre à une question spécifique (délégation LLM).
            """
            logger.info("Délégation de l'analyse légale à l'ExpertAgent...")
            
            document_summary = self.outer._analyze_document_with_llm(document_text, query)
            
            if "Erreur d'analyse" in document_summary:
                 return document_summary
                 
            # 💡 AMÉLIORATION : Formate la sortie pour le LLM Prompter
            return f"[ANALYSE LÉGALE - EXPERT LLM] Requête: '{query}'. Résultat: {document_summary}"