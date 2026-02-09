import logging
import time
import asyncio
import os
from RealtimeSTT import AudioToTextRecorder
from modules.module import Module

os.environ['ORT_LOGGING_LEVEL'] = '3'
logger = logging.getLogger('STT')

class STT(Module):
    def __init__(self, signals, modules=None, enabled: bool = True):
        super().__init__(signals, enabled)
        self.modules = modules or {} 
        self.recorder = None
        # On n'a pas besoin de self.API = self.API(self) ici si on utilise run()

    def process_text(self, text: str):
        """Envoie le texte reconnu au cerveau de Clio."""
        if not text.strip() or len(text.strip()) < 2:
            return
            
        print(f"\n✨ [STT FINAL] : {text}") 
        self.signals.last_message_time = time.time()
        
        # Correction de l'appel au cerveau :
        # On utilise le module 'llm' ou 'brain' via les signaux
        brain = self.modules.get('brain')
        if brain:
            # On utilise create_task car nous sommes déjà dans la boucle de run()
            asyncio.run_coroutine_threadsafe(
                brain.process_llm_response(text, source="voice"), 
                self.signals.loop
            )

    async def listen_loop(self):
        """Boucle d'écoute stable."""
        try:
            await asyncio.sleep(2)
            logger.info("🎤 Initialisation du STT (Whisper Tiny)...")
            
            # Version stable pour RealtimeSTT
            self.recorder = AudioToTextRecorder(
                model="tiny",            
                language="fr",
                device="cpu",            
                compute_type="int8",    
                level=logging.ERROR,      
                beam_size=1,
                silero_use_onnx=True,     
                silero_sensitivity=0.4,   
                enable_realtime_transcription=False, 
                spinner=False,
                use_microphone=True
            )

            logger.info("✅ STT PRÊT.")
            
            while not self.signals.terminate:
                if self.enabled and not self.signals.AI_speaking:
                    # On capture le texte. to_thread est parfait ici.
                    text = await asyncio.to_thread(self.recorder.text)
                    if text:
                        self.process_text(text)
                else:
                    await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"❌ Erreur STT : {e}")
            await asyncio.sleep(5)

    async def run(self): 
        await self.listen_loop()