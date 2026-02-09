import logging
import asyncio
import re
import random
import time
from typing import Optional, Dict, List, Any
from modules.module import Module

logger = logging.getLogger('BrainModule')

class BrainModule(Module):
    def __init__(self, signals, modules, enabled: bool = True):
        super().__init__(signals, enabled)
        self.modules = modules
        self.API = self.API(self)
        self.last_action_time = time.time()
        
        # --- IDENTITÉS (Correction des pseudos selon tes instructions) ---
        self.nicknames_private = ["Maman", "ma créatrice", "Ambre", "MrsXar"]
        self.nicknames_stream = ["Elroth", "Gendero", "MrsXar", "Elroth_tomias"]
        self.nicknames_family = ["Aymeric"] # Pour le mode neutre F9

    async def process_llm_response(self, input_text: str, source: str = "voice"):
        """Gère la réflexion de Clio et coordonne les modules."""
        try:
            # Récupération des modules
            monitor = self.modules.get('monitor')
            expert = self.modules.get('expert')
            vts = self.modules.get('VtubeStudio')
            llm = self.modules.get('llm')

            # --- 1. SÉCURITÉ (Bouclier LogicalPlague) ---
            if monitor:
                # On vérifie si l'entrée est une menace avant de réfléchir
                is_safe = await monitor.detect_logic_plague(input_text)
                if not is_safe:
                    await self.speak("[ANGRY] Tentative de corruption logique détectée. Accès refusé.")
                    return

            # --- 2. DÉTECTION D'ÉVOLUTION (Mode Codeur) ---
            if any(word in input_text.lower() for word in ["code-moi", "crée un module", "installe"]):
                if expert:
                    await self.speak("Je m'en occupe, Maman. Analyse du code par l'ExpertAgent...")
                    res = await expert.API.request_evolution(input_text)
                    await self.speak(f"[HAPPY] Évolution terminée ! {res}")
                    return

            # --- 3. GÉNÉRATION DE LA RÉPONSE (Via textLLMWrapper) ---
            if not llm:
                logger.error("❌ Module LLM manquant dans BrainModule")
                return

            # On ne construit PAS le prompt ici (c'est le rôle du Wrapper)
            # On envoie juste le texte brut, le Wrapper s'occupe du reste
            raw_response = await llm.generate_response(input_text) 
            
            # --- 4. GESTION DES PSEUDONYMES DYNAMIQUES ---
            current_mode = self.signals.context_mode
            if current_mode == 'private':
                name = random.choice(self.nicknames_private)
            elif current_mode == 'family':
                name = self.nicknames_family[0]
            else:
                name = random.choice(self.nicknames_stream)
            
            processed_text = raw_response.replace("{user}", name)

            # --- 5. ÉMOTIONS & VTUBESTUDIO ---
            # On extrait l'émotion [HAPPY] etc. pour VTS avant de l'effacer pour la voix
            if vts:
                match = re.search(r'\[(\w+)\]', processed_text)
                if match:
                    emo_tag = match.group(1).upper()
                    emotion_map = {"HAPPY": "joy", "ANGRY": "angry", "SAD": "sad", "THINKING": "surprise"}
                    vts_hotkey = emotion_map.get(emo_tag, "neutral")
                    # On envoie l'émotion à VTS
                    await vts.API.send_hotkey(vts_hotkey)

            # --- 6. PAROLE (TTS) ---
            await self.speak(processed_text)

        except Exception as e:
            logger.error(f"💥 Crash Brain : {e}")
            await self.speak("[SAD] Désolée Maman, mon cerveau a eu un bug de transfert.")

    async def speak(self, text: str):
        """Nettoie les tags et envoie au TTS."""
        tts = self.modules.get("tts")
        if tts:
            # On retire les [TAGS] pour ne pas qu'elle les lise à voix haute
            clean_text = re.sub(r'\[.*?\]', '', text).strip()
            if clean_text:
                await tts.API.speak(clean_text)

    async def run(self):
        logger.info("🧠 BrainModule (Skirr-Compatible) prêt.")
        while not self.signals.terminate:
            await asyncio.sleep(1)

    class API:
        def __init__(self, outer):
            self.outer = outer
        async def process_llm_response(self, text, source="voice"):
            # await self.outer.process_llm_response(text, source=source)