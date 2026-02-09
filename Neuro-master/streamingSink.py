import io
# 🚨 NÉCESSAIRE : Importation de pydub pour le traitement audio
from pydub import AudioSegment 
from discord.sinks.core import Filters, Sink, default_filters, AudioData
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from stt import STT # Pour le type hinting

class StreamingSink(Sink):
    """
    Sink personnalisé qui convertit le flux audio Discord (48kHz stéréo)
    en flux PCM mono 16kHz pour le module STT/Whisper.
    """

    def __init__(self, signals: Any, stt: 'STT', filters: Optional[Dict[str, Any]] = None):
        if filters is None:
            filters = default_filters
            
        # Initialisation du mixin Filters
        super().__init__(**filters) 

        self.encoding = "pcm"
        self.vc = None
        self.audio_data = {} # Utiliser pour l'enregistrement, non requis pour le streaming STT

        self.signals = signals
        self.stt = stt
        
        print("[StreamingSink] Initialisé. Prêt pour l'écoute vocale (nécessite FFmpeg).")


    # Override the write method to instead stream the audio elsewhere
    @Filters.container
    def write(self, data: bytes, user: Any):
        """
        Méthode de réception de l'audio en temps réel.
        data est le morceau audio brut de 20ms (par défaut).
        """
        # La logique de stockage AudioData n'est pas nécessaire pour le streaming STT,
        # mais laissons la logique d'ajout au dictionnaire en place pour la compatibilité:
        if user not in self.audio_data:
            file = io.BytesIO()
            self.audio_data.update({user: AudioData(file)})

        file = self.audio_data[user]
        file.write(data) 
        
        # --- PHASE CRITIQUE : CONVERSION DE L'AUDIO POUR STT ---
        # 🚨 L'audio Discord est généralement 48kHz, Stéréo. STT nécessite 16kHz, Mono.
        
        try:
            # 1. Initialiser AudioSegment à partir des données Discord (48kHz, 16-bit, Stéréo)
            sound = AudioSegment(
                data=data,
                sample_width=2, # 16 bit
                frame_rate=48000,
                channels=2
            )
            
            # 2. Convertir en Mono
            sound = sound.set_channels(1)
            
            # 3. Rééchantillonner à 16kHz
            sound = sound.set_frame_rate(16000)
            
            # 4. Envoyer les données PCM brutes à STT (Whisper)
            if self.signals.stt_ready:
                self.stt.feed_audio(sound.raw_data)
            
        except Exception as e:
            # Cette erreur se produit souvent si FFmpeg est manquant ou si les données sont corrompues.
            print(f"[StreamingSink] ERREUR Pydub/Audio : {e}")

    # Cette méthode n'est pas utilisée pour le streaming, mais laissons-la pour la compatibilité de l'héritage.
    def format_audio(self, audio):
        return