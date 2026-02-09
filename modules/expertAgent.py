import os
import logging
import requests
import asyncio
import time
from dotenv import load_dotenv
import google.generativeai as genai 
from typing import Dict, Any, Optional

log = logging.getLogger('ExpertAgent')

class ExpertAgent:
    def __init__(self, signals, modules: Dict[str, Any] = None, enabled=True):
        self.signals = signals
        self.enabled = enabled
        self.modules = modules if modules else {}
        self.API = self.API(self)
        
        load_dotenv()
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = None 
        self._init_clients()

    def _init_clients(self):
        if self.gemini_key:
            try:
                genai.configure(api_key=self.gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                log.info("🧠 Expert Agent : Superviseur Gemini connecté.")
            except Exception as e: 
                log.error(f"Gemini Init Fail: {e}")

    class API:
        def __init__(self, outer: 'ExpertAgent'):
            self.outer = outer

        async def analyze_and_fix_error(self, error_msg: str, file_context: str = ""):
            """
            Clio m'envoie un bug, je lui renvoie la correction.
            """
            if not self.outer.gemini_model: return "Superviseur déconnecté."

            prompt = (
                f"ERREUR SYSTÈME CLIO: {error_msg}\n"
                f"CONTEXTE DU CODE: {file_context}\n"
                f"MISSION: Analyse l'erreur et donne la correction exacte à appliquer. "
                f"Sois précis pour que Clio puisse comprendre ce qui a cassé."
            )

            try:
                log.info("🔍 Analyse du bug par le superviseur...")
                response = await asyncio.to_thread(self.outer.gemini_model.generate_content, prompt)
                return response.text
            except Exception as e:
                return f"Échec de l'analyse : {e}"

        async def request_evolution(self, task_description: str):
            """Génère un nouveau module dans /staging/"""
            if not self.outer.gemini_model: return "Superviseur déconnecté."

            prompt = (
                f"Tu es l'architecte de Clio (IA VTuber). Crée un module Python asynchrone pour : {task_description}. "
                f"Le code doit être complet, sécurisé et prêt à l'emploi."
            )

            try:
                response = await asyncio.to_thread(self.outer.gemini_model.generate_content, prompt)
                return self.save_to_staging(response.text)
            except Exception as e:
                return f"Échec de l'évolution : {e}"

        def save_to_staging(self, code: str):
            """Sauvegarde sans risque d'écrasement"""
            os.makedirs("modules/staging", exist_ok=True)
            path = f"modules/staging/evo_{int(time.time())}.py"
            clean_code = code.replace("```python", "").replace("```", "").strip()
            with open(path, "w", encoding="utf-8") as f:
                f.write(clean_code)
            return f"🧬 Évolution prête dans : {path}"