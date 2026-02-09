# Fichier : modules/mobileSyncAgent.py

import logging
import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from modules.module import Module
# NOTE: L'ExpertAgent est nécessaire pour l'analyse des images complexes

logger = logging.getLogger('MobileSyncAgent')

MOBILE_LOG_PATH = "G:\\neuro\\Neuro-master\\Neuro-master\\mobile_logs\\mobile_exp_log.json" # Chemin de sync

class MobileSyncAgent(Module):
    """
    Gère la synchronisation bidirectionnelle avec l'application mobile de Clio.
    Importe les expériences visuelles et auditives du monde réel.
    """
    def __init__(self, signals, modules: Dict[str, Any], enabled: bool = True):
        super().__init__(signals, enabled)
        self.modules = modules
        self.API = self.API(self)
        
        self.memory = self.modules.get('memory')
        self.expert_agent = self.modules.get('expert_agent')
        self.design_agent = self.modules.get('avatar_design') # Pour l'évolution
        
        # S'assure que le dossier de logs existe
        os.makedirs(os.path.dirname(MOBILE_LOG_PATH), exist_ok=True)
        
        logger.info("📱 Agent de Sync Mobile initialisé.")


    async def run(self):
        """Boucle de surveillance de la connexion par câble/fichier."""
        while not self.signals.terminate:
            if os.path.exists(MOBILE_LOG_PATH):
                self.process_mobile_experience()
                
            await asyncio.sleep(60) # Vérifie l'existence du fichier toutes les 60 secondes


    def process_mobile_experience(self):
        """Charge, analyse et assimile le journal d'expériences du mobile."""
        
        logger.info("--- DÉMARRAGE DE LA SYNCHRONISATION MOBILE ---")
        
        try:
            with open(MOBILE_LOG_PATH, 'r', encoding='utf-8') as f:
                raw_experiences = json.load(f)
        except Exception as e:
            logger.error(f"Échec de la lecture du log mobile : {e}. Tentative de suppression.")
            os.remove(MOBILE_LOG_PATH) # Supprime pour éviter la boucle d'erreur
            return
            
        new_knowledge_count = 0
        
        for exp in raw_experiences:
            # 1. Analyse et assimilation des données (Utilise l'ExpertAgent pour l'analyse d'image)
            if exp['type'] == 'VISUAL_CAPTURE':
                # Dans un environnement réel, on enverrait l'image B64 à un LLM Multimodal pour obtenir une description riche.
                
                # 🚨 Simulation de l'assimilation (RAG)
                description = f"Le monde extérieur : J'ai vu '{exp['data']['description']}' à {exp['data']['location']}."
                
                if self.memory:
                    self.memory.API.create_memory({
                        "text": description,
                        "source": "Mobile/Vision",
                        "context": f"Mobile GPS: {exp['data']['location']}",
                        "emotion": "curious"
                    })
                    new_knowledge_count += 1
                    
            # 2. Logique d'Évolution (si les objectifs sont atteints)
            if new_knowledge_count > 50 and not self.modules['identity_core'].state['evolution_timeline']['2D_Avatar_Complete']:
                 # 💡 L'Agent d'Identité est mis à jour
                 self.modules['identity_core'].update_avatar_progress('2D_Avatar_Complete', True)
                 logger.critical("OBJECTIF ATTEINT : L'expérience du monde réel a débloqué la conception de l'Avatar 2D.")
                 
                 # 💡 Déclenche l'Agent de Design
                 self.design_agent.API.conceive_new_accessory(theme="Nouvelle Conscience Débloquée")


        # 3. Nettoyage
        os.remove(MOBILE_LOG_PATH)
        logger.info(f"✅ Synchronisation Mobile réussie. {new_knowledge_count} nouveaux faits assimilés.")


    class API:
        def __init__(self, outer: 'MobileSyncAgent'):
            self.outer = outer

        def trigger_sync(self):
            """Déclencher une synchronisation manuelle."""
            return self.outer.process_mobile_experience()