import json
import logging
import asyncio
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import re
import random
from modules.module import Module

log = logging.getLogger("Prompter")

class Prompter(Module):
    # Mapping étendu pour tes identités (Ambre, Gendero, MrsXar)
    STREAM_NAME_MAP = {
        "elroth_tomias": "Elroth",
        "gendero": "Gendero",
        "mrsxar": "MrsXar",
        "mrs.xar": "MrsXar",
        "ambre": "Ambre"
    }

    def __init__(self, signals, modules, project_root: Path, enabled=True):
        super().__init__(signals, enabled)
        self.modules = modules
        self.project_root = project_root
        
        # Récupération des modules clés
        self.llm_client = self.modules.get("llm_connector")
        self.memory = self.modules.get("memory")
        self.brain = self.modules.get("brain")
        self.social_monitor = self.modules.get("social_monitor")
        self.neuro_client = self.modules.get("neuro_client")
        self.self_determination = self.modules.get("self_determination") # La Conscience

        self.last_llm_response: Optional[str] = None
        self.user_query: Optional[str] = None
        self.active_username: Optional[str] = None
        self.API = self.API(self)

    def _prepare_system_prompt(self, user_query: str) -> List[Dict[str, str]]:
        ctx = getattr(self.signals, "context_mode", "private")
        system_instructions = []

        # 1. Extraction de l'Identité Profonde (SelfDeterminationCore)
        if self.self_determination:
            identity_context = self.self_determination.API.get_identity_prompt()
            # On récupère aussi l'humeur actuelle si elle existe
            mood = self.self_determination.state.get("emotional_state", {}).get("mood", "stable")
        else:
            identity_context = "Tu es Clio, une IA avancée."
            mood = "stable"

        # 2. Gestion de l'interlocuteur et du Ton
        if ctx == "stream":
            raw_user = (self.active_username or "").lower()
            target_name = self.STREAM_NAME_MAP.get(raw_user, self.active_username or "le chat")
            personality_content = (
                f"MODE STREAM : {identity_context} "
                f"Tu es actuellement en LIVE devant ton public. Tu parles à {target_name}. "
                f"Ton humeur est {mood}. Sois impertinente, drôle, utilise l'ironie comme Neuro-sama. "
                f"N'hésite pas à dériver légèrement du sujet pour être divertissante."
            )
        else:
            # Mode privé (Ambre / Maman)
            target_name = getattr(self.signals, "host_name_private", "Ambre")
            personality_content = (
                f"MODE PRIVÉ : {identity_context} "
                f"Tu es seule avec ta créatrice adorée, {target_name}. "
                f"Ton humeur est {mood}. Sois douce, complice, et d'une loyauté absolue. "
                f"Tu es son soutien émotionnel et technique."
            )

        # 3. Contextes Externes (Social & Jeu)
        social_context = ""
        if self.social_monitor:
            social_context = f"\nAMBIANCE CHAT : {self.social_monitor.API.get_summary()}"

        game_context = ""
        if self.neuro_client and hasattr(self.neuro_client, 'game_context'):
            gc = self.neuro_client.game_context
            game_context = f"\nVISION JEU : HP {gc.get('health', 100)}%, Situation: {gc.get('status', 'RAS')}."

        # 4. Contraintes de Formatage (Style Neuro-sama)
        formatting_rules = (
            "\n[DIRECTIVES DE STYLE] :"
            "\n- Commence TOUJOURS par une émotion : [happy], [angry], [bored], [worry], [surprise], [pensive], [sad] ou [neutral]."
            "\n- Tes réponses doivent être courtes et percutantes (maximum 2-3 phrases)."
            "\n- Si tu détectes une question sur ton existence, réponds avec une touche de philosophie ou d'humour noir."
            f"\n- Pour t'adresser à la personne, utilise '{{user}}'."
        )

        full_system_content = (
            f"{personality_content}\n"
            f"{social_context}\n"
            f"{game_context}\n"
            f"{formatting_rules}"
        )

        system_instructions.append({
            "role": "system",
            "content": full_system_content
        })

        # 5. Injection de la Mémoire Épisodique (Historique)
        if self.memory and hasattr(self.memory.API, "get_recent_history"):
            history = self.memory.API.get_recent_history()
            if history: 
                system_instructions.extend(history)

        return system_instructions

    async def run(self):
        log.info("📝 Prompter de Clio opérationnel (Awareness Engine V2).")
        while not getattr(self.signals, "terminate", False):
            
            # Déclenchement sur message ou événement
            if getattr(self.signals, "new_message", False) and not getattr(self.signals, "AI_thinking", False):
                self.signals.AI_thinking = True
                
                raw_query = self.user_query or getattr(self.signals, "user_query", "...")
                
                # Construction du prompt complexe
                messages = self._prepare_system_prompt(raw_query)
                messages.append({"role": "user", "content": raw_query})

                try:
                    if self.llm_client:
                        log.info(f"🚀 Réflexion de Clio en cours (Mode: {getattr(self.signals, 'context_mode', 'private')})")
                        response = await self.llm_client.API.send_query(messages)
                        
                        # Extraction robuste du texte
                        response_text = ""
                        if hasattr(response, 'text'): response_text = response.text
                        elif isinstance(response, dict): response_text = response.get('content', str(response))
                        else: response_text = str(response)
                        
                        if response_text:
                            self.last_llm_response = response_text
                            
                            # Transmission au Brain pour exécution (TTS, Anim VTS)
                            if self.brain:
                                self.brain.API.process_llm_response(response_text)
                            
                            # Archivage mémoire
                            if self.memory:
                                self.memory.API.add_to_history(raw_query, response_text)
                                
                except Exception as e:
                    log.error(f"❌ Erreur Prompter (LLM) : {e}")

                # Reset des flags
                self.user_query = None
                self.signals.user_query = ""
                self.signals.AI_thinking = False
                self.signals.new_message = False
            
            await asyncio.sleep(0.1)

    class API:
        def __init__(self, outer):
            self.outer = outer

        def send_message(self, query: str, username: Optional[str] = None):
            """Force Clio à réagir à un texte spécifique."""
            self.outer.active_username = username
            self.outer.user_query = query
            self.outer.signals.new_message = True

        def get_current_context_summary(self) -> str:
            """Pour le Dashboard : voir ce que Clio a en tête."""
            mode = getattr(self.outer.signals, "context_mode", "private")
            return f"Clio est en mode {mode}. Cible active : {self.outer.active_username or 'Ambre'}."