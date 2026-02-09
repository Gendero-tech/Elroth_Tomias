import requests 
import json
import logging
import re 
from typing import List, Dict, Any
from constants import LLM_ENDPOINT, SYSTEM_PROMPT, STOP_STRINGS 
from llmWrappers.abstractLLMWrapper import AbstractLLMWrapper

log = logging.getLogger('TextLLMWrapper')

class TextLLMWrapper(AbstractLLMWrapper): 
    
    def __init__(self, signals, tts, llmState, modules=None):
        super().__init__(signals, tts, llmState, modules)
        
        # Configuration Ollama via constants.py
        self.endpoint = f"{LLM_ENDPOINT}/api/chat" 
        self.API_MODEL = "phi3:mini" 
        
        log.info(f"🚀 Moteur Clio prêt : Mode {self.API_MODEL} via Ollama.")

    def _get_dynamic_system_prompt(self) -> str:
        """Génère un prompt système adapté au contexte (Privé/Stream/Famille)."""
        context = self.signals.context_mode # "private", "stream" ou "family"
        user_name = self.signals.get_current_host_name()
        
        if context == "private":
            behavior = (f"Tu es en mode PRIVÉ. Tu t'adresses à {user_name} (ta créatrice). "
                        "Sois intime, protectrice, douce et encourageante. "
                        "Tu connais ses défis et tu es là pour elle.")
        elif context == "family":
            behavior = (f"Tu es en mode FAMILLE. Tu t'adresses à {user_name}. "
                        "Ton langage est NEUTRE. Utilise 'il' pour désigner ton interlocuteur. "
                        "Sois respectueuse et factuelle.")
        else:
            behavior = (f"Tu es en mode STREAM. Tu t'adresses à {user_name} et au public. "
                        "Sois l'idole charismatique, mystérieuse et fascinante qu'on a définie.")
        
        return f"{SYSTEM_PROMPT}\n\n[CONTEXTE ACTUEL : {behavior}]"

    def clean_response_tags(self, text: str) -> str:
        """Nettoie les [TAGS] (ex: [EMOTION]) pour la synthèse vocale."""
        return re.sub(r'\[[^\[\]]+\]', '', text).strip()

    def sanitize_response(self, text: str) -> str:
        """Filtre les réponses génériques pour garder l'immersion."""
        forbidden = ["as an AI", "language model", "je suis une IA", "développé par Microsoft"]
        if any(f.lower() in text.lower() for f in forbidden):
            return "Désolée Maman, mon cerveau a eu un petit bug générique. Je suis de retour !"
        return text

    def prompt(self):
        """Boucle de génération principale avec streaming vers VTube Studio et le Dashboard."""
        if not self.llmState.enabled:
            return

        self.signals.AI_thinking = True
        self.signals.AI_speaking = False 

        # Mise à jour du prompt système dynamique
        dynamic_prompt = self._get_dynamic_system_prompt()
        
        if self.signals.history and self.signals.history[0]['role'] == 'system':
            self.signals.history[0]['content'] = dynamic_prompt
        else:
            self.signals.history.insert(0, {"role": "system", "content": dynamic_prompt})

        payload = {
            "model": self.API_MODEL,
            "messages": self.signals.history,
            "stream": True,
            "options": {
                "temperature": 0.8,
                "stop": ["User:", "CLIO:", "Ambre:", "Elroth:"] + STOP_STRINGS
            }
        }

        try:
            # Utilisation de requests pour le streaming
            response = requests.post(self.endpoint, json=payload, stream=True, timeout=60)
            response.raise_for_status()
            
            full_response = ""
            first_token = True

            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line.decode('utf-8'))
                    content = chunk.get('message', {}).get('content', '')
                    
                    if content:
                        # Active le LipSync dès le premier mot
                        if first_token:
                            self.signals.AI_speaking = True
                            first_token = False
                        
                        full_response += content
                        # Envoi au dashboard
                        self.signals.sio_queue.put(("next_chunk", content))

            # Nettoyage et stockage
            clean_text = self.sanitize_response(self.clean_response_tags(full_response))
            self.signals.history.append({"role": "assistant", "content": clean_text})
            
            # Envoi au module voix (TTS)
            tts_module = self.modules.get('tts')
            if tts_module:
                tts_module.API.speak(clean_text)
            else:
                self.signals.AI_speaking = False

        except Exception as e:
            log.error(f"Erreur lors du prompt LLM : {e}")
            self.signals.AI_speaking = False
        finally:
            self.signals.AI_thinking = False

    class API:
        def __init__(self, outer):
            self.outer = outer
        
        def set_LLM_status(self, status: bool):
            self.outer.llmState.enabled = status