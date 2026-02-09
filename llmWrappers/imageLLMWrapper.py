import os
import mss, cv2, base64
import numpy as np
# 🚨 NOTE: AutoTokenizer est un import lourd, souvent désactivé pour la rapidité
from transformers import AutoTokenizer 
from constants import *
from llmWrappers.abstractLLMWrapper import AbstractLLMWrapper
import time
from typing import List, Dict, Any, Union, Optional
import logging

logger = logging.getLogger('ImageLLMWrapper')

class ImageLLMWrapper(AbstractLLMWrapper):

    def __init__(self, signals, tts, llmState, modules=None):
        # 🚨 CORRECTION CRITIQUE : Ajout des parenthèses manquantes à super().__init__()
        super().__init__(signals, tts, llmState, modules) 
        
        self.SYSTEM_PROMPT = SYSTEM_PROMPT
        self.LLM_ENDPOINT = MULTIMODAL_ENDPOINT
        self.CONTEXT_SIZE = MULTIMODAL_CONTEXT_SIZE
        self.model_name = MULTIMODAL_MODEL
        
        # Initialisation Mss (peut être fait ici si on veut)
        self.MSS: Optional[mss.base.MSS] = None 
        
        if MULTIMODAL_MODEL:
            try:
                 self.tokenizer = None # Maintenu désactivé par défaut
            except Exception as e:
                 logger.error(f"ERREUR Multimodal: Échec du chargement du tokenizer: {e}")
                 self.tokenizer = None
        else:
            self.tokenizer = None

        # 🚀 AMÉLIORATION : Définition de la requête visuelle par défaut
        self.visual_query: str = "Décris l'écran pour contextualiser ma réponse à la dernière requête utilisateur."

    def _encode_to_base64(self, image_path: Optional[str] = None, numpy_array: Optional[np.ndarray] = None) -> str:
        """Encode une image (chemin ou array) en Base64 JPEG."""
        if image_path:
            frame_array = cv2.imread(image_path)
            if frame_array is None:
                 logger.error(f"Impossible de lire l'image à partir du chemin: {image_path}")
                 return ""
        elif numpy_array is not None:
             frame_array = numpy_array
        else:
            return ""

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 95]
        result, frame_encoded = cv2.imencode('.jpg', frame_array, encode_param)
        
        if result:
            return base64.b64encode(frame_encoded).decode("utf-8")
        return ""

    def screen_shot(self) -> str:
        """Prend une capture d'écran de l'écran principal et la retourne en Base64 JPEG."""
        if self.MSS is None:
            self.MSS = mss.mss()
            
        start_time = time.time()
        
        try:
            # Capture d'écran se concentre sur l'écran PRINCIPAL
            # Assurez-vous que PRIMARY_MONITOR est défini (doit être > 0)
            frame_bytes = self.MSS.grab(self.MSS.monitors[PRIMARY_MONITOR])

            frame_array = np.array(frame_bytes)
            frame_array = cv2.cvtColor(frame_array, cv2.COLOR_BGRA2BGR)
            
            frame_base64 = self._encode_to_base64(numpy_array=frame_array)
            
            logger.info(f"[Multimodal] Capture d'écran et encodage réalisés en {time.time() - start_time:.2f}s.")
            return frame_base64
            
        except Exception as e:
            logger.error(f"ERREUR CAPTURE D'ÉCRAN: {e}")
            return ""

    def assemble_injections(self, messages: List[Dict[str, str]]) -> str:
        """Assemble l'historique textuel et le système prompt en une seule chaîne lisible pour le LLM."""
        
        # Supprime le dernier message utilisateur (qui est géré par la partie 'text' du ChatML content)
        # et le premier message système (qui est trop long et géré par la structure ChatML).
        
        history_str = ""
        for msg in messages:
            # Note: Si le Prompter enrichit l'historique avec les messages Système (Role: system),
            # il faut s'assurer de ne pas les dupliquer ici.
            
            if msg['role'] == 'user':
                history_str += f"User: {msg['content']}\n"
            elif msg['role'] == 'assistant':
                history_str += f"Clio: {msg['content']}\n"
        
        return history_str.strip()

    def prepare_payload(self) -> Dict[str, Any]:
        """Prépare le payload pour l'API multimodal (version ChatML)."""
        if not self.LLM_ENDPOINT or not self.LLM_ENDPOINT.strip():
             raise RuntimeError("Endpoint Multimodal non configuré (MULTIMODAL_ENDPOINT est vide).")
             
        # L'historique complet est généré par le Prompter
        messages = self.signals.history 
        
        # 1. DÉTERMINATION DE LA SOURCE VISUELLE
        visual_source_base64 = ""
        source_type = "screenshot"
        
        # Vérifie si le Prompter a injecté un chemin de fichier pour l'analyse
        # Ceci est stocké dans le signals.multimodal_file_path (à définir dans votre PrompterModule)
        file_to_analyze = getattr(self.signals, 'multimodal_file_path', None)
        
        if file_to_analyze and os.path.exists(file_to_analyze):
            # Tente d'encoder le fichier uploadé
            visual_source_base64 = self._encode_to_base64(image_path=file_to_analyze)
            source_type = "file_upload"
        else:
            # Par défaut: capture d'écran
            visual_source_base64 = self.screen_shot()
        
        if not visual_source_base64:
             raise RuntimeError(f"Impossible d'obtenir une source visuelle ({source_type}).")
             
        # 2. INSTRUCTION VISUELLE
        # Utilise le prompt d'injection du Prompter s'il est disponible, sinon utilise une requête par défaut.
        visual_instruction = self.visual_query 

        # 3. CONSTRUIRE LE PAYLOAD FINAL (Format ChatML/Multimodal)
        
        # Le format ChatML/Llava requiert souvent la dernière entrée utilisateur combinée avec l'image.
        current_query = messages[-1]['content'] if messages and messages[-1]['role'] == 'user' else "Décris ce que tu vois."
        
        # Le contenu sera une liste combinant l'instruction, l'image, et le reste de l'historique textuel
        return {
            "model": self.model_name,
            "stream": True,
            "max_tokens": 1024, # Augmenté pour laisser de la place au raisonnement multimodal
            "stop": STOP_STRINGS,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"{visual_instruction}\nVoici l'historique de la conversation: {self.assemble_injections(messages)}"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{visual_source_base64}"
                            }
                        }
                    ]
                }
            ]
        }