import logging
import edge_tts
import asyncio
import re
import os
import time
from modules.module import Module

logger = logging.getLogger('TTS')

class TTS(Module):
    def __init__(self, signals, modules=None, enabled: bool = True, **kwargs):
        """
        Initialisation du module TTS.
        **kwargs permet d'accepter des arguments supplémentaires comme 'llm_state' 
        sans faire planter le programme.
        """
        super().__init__(signals, enabled)
        self.modules = modules or {}
        self.voice = "fr-FR-DeniseNeural" 
        self.rate = "+15%" 
        self.volume = "+0%"
        self.lock = asyncio.Lock()
        self.API = self.API(self)
        
        # Création du dossier temp s'il n'existe pas
        if not os.path.exists("temp"): 
            os.makedirs("temp")

    def clean_text(self, text: str) -> str:
        if not text: return ""
        # Nettoie les expressions entre astérisques ou crochets (pensées de l'IA)
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\*.*?\*', '', text)
        return text.strip()

    async def generate_audio(self, text: str):
        async with self.lock:
            cleaned_text = self.clean_text(text)
            if not cleaned_text: 
                return

            # Chemin absolu pour que PowerShell trouve le fichier sans erreur
            output_path = os.path.abspath(os.path.join("temp", f"tts_{int(time.time())}.mp3"))

            try:
                # 1. Synthèse vocale via Edge-TTS
                communicate = edge_tts.Communicate(cleaned_text, self.voice, rate=self.rate)
                await communicate.save(output_path)
                
                # 2. Envoi à l'AudioPlayer
                # On cherche le module sous 'audio' ou 'audio_player' (selon ton main.py)
                player = self.modules.get('audio') or self.modules.get('audio_player')
                
                if player:
                    logger.info(f"📤 Envoi de l'audio au player : {output_path}")
                    player.API.play_audio(output_path)
                else:
                    logger.error("❌ Module AudioPlayer non trouvé dans self.modules")

            except Exception as e:
                logger.error(f"❌ TTS Error: {e}")

    async def run(self):
        # Le TTS est passif, il attend qu'on appelle son API.speak() via le cerveau
        while not self.signals.terminate:
            await asyncio.sleep(1)

    class API:
        def __init__(self, outer):
            self.outer = outer
        async def speak(self, text: str):
            """Appelé par TextLLMWrapper ou BrainModule"""
            await self.outer.generate_audio(text)