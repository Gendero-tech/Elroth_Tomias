import copy
import requests
import sseclient
import json
import time
import os
import logging
from dotenv import load_dotenv
# 🚨 CORRECTION CRITIQUE : Importe HOST_NAME_PRIVATE qui existe dans constants.py
from constants import SYSTEM_PROMPT, HOST_NAME_PRIVATE, AI_NAME 
from modules.injection import Injection
from typing import List, Dict, Any, Union, Optional
from requests.exceptions import RequestException # Import nécessaire pour la gestion d'erreur

logger = logging.getLogger('AbstractLLMWrapper')

class AbstractLLMWrapper:

    def __init__(self, signals, tts, llmState, modules: Optional[Dict] = None): 
        self.signals = signals
        self.llmState = llmState
        self.tts = tts
        self.API = self.API(self)
        self.modules = modules if modules is not None else {}

        self.headers = {"Content-Type": "application/json"}

        load_dotenv()

        # Below constants must be set by child classes
        self.model_name: Optional[str] = None # 🚀 NOUVEAU: Nom du modèle pour les logs
        self.LLM_ENDPOINT: Optional[str] = None
        self.CONTEXT_SIZE: Optional[int] = None
        self.tokenizer: Optional[Any] = None # HACK: souvent non implémenté pour les API externes
        
        self.ethics_profile: Optional[Any] = self.modules.get("ethics_profile")
            
    # ----------------------------------------------------------------------
    # GESTION DES INJECTIONS (CORE LOGIC)
    # ----------------------------------------------------------------------

    def _fetch_and_cleanup_injections(self) -> List[Injection]:
        """ Collecte les injections de tous les modules, les trie, puis demande le nettoyage. """
        injections: List[Injection] = []

        # 1. Collecte les injections
        for name, module in self.modules.items():
            # Vérifie si le module supporte l'injection (via get_prompt_injection)
            if name != 'tts' and hasattr(module, 'get_prompt_injection'):
                injection = module.get_prompt_injection()
                if injection.priority >= 0 and injection.text.strip():
                    injections.append(injection)
            
        # 2. Demande le nettoyage (pour effacer les messages Twitch, etc.)
        for module in self.modules.values():
            if hasattr(module, 'cleanup'):
                module.cleanup()

        # 3. Trie les injections par priorité (basse à haute)
        return sorted(injections, key=lambda x: x.priority)


    def assemble_injections(self) -> str:
        """ Assemble les injections triées en une seule chaîne de prompt. """
        injections = self._fetch_and_cleanup_injections()
        
        prompt = ""
        for injection in injections:
            prompt += injection.text + "\n"
            
        return prompt.strip()


    # ----------------------------------------------------------------------
    # MÉTHODES DE BASE / VÉRIFICATIONS
    # ----------------------------------------------------------------------

    def is_filtered(self, text: str) -> bool:
        """ Vérifie les termes blacklistés (filtre de sécurité basique en sortie). """
        
        # 1. Vérification du Profil Éthique (si disponible)
        if self.ethics_profile:
            is_valid, _ = self.ethics_profile.validate(text)
            if not is_valid:
                logger.warning("[LLM Filter] Message filtré par le Profil Éthique.")
                return True

        # 2. Vérification de la Blacklist
        text_padded = " " + text.lower() + " "
        if any((" " + bad_word.lower() + " ") in text_padded for bad_word in self.llmState.blacklist):
            logger.warning(f"[LLM Filter] Message filtré : terme blacklisté trouvé.")
            return True
            
        return False

    def generate_prompt(self) -> List[Dict[str, str]]:
        """ 
        Génère l'historique de conversation tronqué pour le contexte.
        NOTE: Les injections doivent être gérées par le Prompter et non ici pour le ChatML standard.
        """
        messages = copy.deepcopy(self.signals.history)
        
        # Logique de troncature conservée
        max_messages_to_keep = 15 
        
        if len(messages) > max_messages_to_keep:
            # Tronque le milieu (méthode de maintien du contexte)
            system_prompt = messages[0] if messages and messages[0]['role'] == 'system' else None
            
            # Tronque le milieu
            messages = messages[-max_messages_to_keep:]
            
            # S'assure que le prompt système est toujours en tête
            if system_prompt and messages[0] != system_prompt:
                 messages.insert(0, system_prompt)

        return messages


    def _speak_response(self, response_text: str):
        """ Gère la délégation de la parole au module TTS. """
        self.signals.last_message_time = time.time()
        self.signals.AI_speaking = True
        self.signals.AI_thinking = False
        
        # 🚨 CORRECTION CRITIQUE : Délégation à l'API du module TTS
        tts_module = self.modules.get('tts')
        if tts_module and hasattr(tts_module.API, 'speak'):
             tts_module.API.speak(response_text)
        else:
             logger.error("API TTS non disponible pour la lecture.")


    def prepare_payload(self):
        raise NotImplementedError("Must implement prepare_payload in child classes")

    def prompt(self):
        """ Gère la boucle de streaming et la mise à jour des signaux. """
        if not self.llmState.enabled:
            return

        # 🚀 AMÉLIORATION : Démarrage de la mesure de latence
        start_time = time.time()
        
        self.signals.AI_thinking = True
        self.signals.new_message = False
        self.signals.sio_queue.put(("reset_next_message", None))

        try:
            data = self.prepare_payload()
        except RuntimeError as e:
            logger.error(f"ERREUR PROMPT: {e}")
            self.signals.AI_thinking = False
            return
            
        try:
            # L'appel réel à l'API du LLM
            stream_response = requests.post(
                self.LLM_ENDPOINT + "/v1/chat/completions", 
                headers=self.headers, 
                json=data,
                verify=False, 
                stream=True,
                timeout=120
            )
            stream_response.raise_for_status()
            response_stream = sseclient.SSEClient(stream_response)
        except requests.exceptions.RequestException as e:
            logger.error(f"ERREUR REQUÊTE LLM: Échec de la connexion ou erreur HTTP : {e}")
            self.signals.AI_thinking = False
            self.signals.sio_queue.put(("next_chunk", f"Erreur de connexion LLM: {e}"))
            self.signals.sio_queue.put(("reset_next_message", None))
            return

        AI_message = ''
        ttft_logged = False
        
        try:
            for event in response_stream.events():
                if self.llmState.next_cancelled:
                    continue

                try:
                    payload = json.loads(event.data)
                    chunk = payload['choices'][0]['delta']['content']
                except (json.JSONDecodeError, KeyError):
                    continue
                
                # Mesure TTFT et le temps total
                if not ttft_logged and chunk:
                    ttft = time.time() - start_time
                    self.signals.llm_latency = ttft
                    ttft_logged = True
                
                AI_message += chunk
                self.signals.sio_queue.put(("next_chunk", chunk))
        
        except Exception as e:
            logger.error(f"ERREUR STREAMING LLM: {e}")
            
        if self.llmState.next_cancelled:
            self.llmState.next_cancelled = False
            self.signals.sio_queue.put(("reset_next_message", None))
            self.signals.AI_thinking = False
            return

        # --- GESTION FINALE ET STOCKAGE ---
        
        # Le Prompter doit gérer le nettoyage des tags (émotions, délégations) avant de stocker et de parler.
        # Ici, nous ne faisons qu'un filtrage final de sécurité si le Prompter a laissé échapper du contenu toxique.
        if self.is_filtered(AI_message):
             AI_message = "Je ne peux pas répondre à cela. Ce sujet est filtré par mes règles éthiques."

        logger.info("AI OUTPUT: " + AI_message)

        self.signals.history.append({"role": "assistant", "content": AI_message})
        
        self._speak_response(AI_message)


    class API:
        def __init__(self, outer: 'AbstractLLMWrapper'):
            self.outer = outer

        def get_blacklist(self) -> List[str]:
            return self.outer.llmState.blacklist

        def set_blacklist(self, new_blacklist: List[str]):
            self.outer.llmState.blacklist = new_blacklist
            try:
                with open('blacklist.txt', 'w', encoding='utf-8') as file:
                    for word in new_blacklist:
                        file.write(word + "\n")
            except Exception as e:
                print(f"ERREUR: Impossible de sauvegarder blacklist.txt: {e}")

            self.outer.signals.sio_queue.put(('get_blacklist', new_blacklist))

        def set_LLM_status(self, status: bool):
            self.outer.llmState.enabled = status
            if status:
                self.outer.signals.AI_thinking = False
            self.outer.signals.sio_queue.put(('LLM_status', status))

        def get_LLM_status(self) -> bool:
            return self.outer.llmState.enabled

        def cancel_next(self):
            self.outer.llmState.next_cancelled = True
            # NOTE: Utilise l'endpoint du LLMWrapper pour l'arrêt de la génération
            requests.post(self.outer.LLM_ENDPOINT + "/v1/internal/stop-generation", headers={"Content-Type": "application/json"})