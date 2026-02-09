import os
import asyncio
import queue
import logging
import subprocess
from math import ceil
from modules.module import Module

# Configuration du logging pour voir les erreurs dans la console
logger = logging.getLogger('AudioPlayer')

class AudioPlayer(Module):
    def __init__(self, signals, enabled=True):
        super().__init__(signals, enabled)
        self.play_queue = queue.SimpleQueue()
        self.abort_flag = False
        self.paused = False
        self.API = self.API(self)

        # Liste des fichiers dans le dossier 'songs' comme sur le GitHub
        self.audio_files = []
        if self.enabled:
            if not os.path.exists("songs"):
                os.makedirs("songs")
            
            for file in os.listdir("songs"):
                if file.endswith(".mp3") or file.endswith(".wav"):
                    # On stocke des objets Audio pour la compatibilité API
                    audio_obj = self.Audio(file, os.path.join(os.getcwd(), "songs", file))
                    self.audio_files.append(audio_obj)

    async def run(self):
        logger.info("🎶 AudioPlayer (Mode PowerShell MP3) ACTIF")
        
        while not self.signals.terminate:
            if not self.enabled:
                await asyncio.sleep(1)
                continue

            # On réinitialise l'arrêt si on ne joue rien
            self.abort_flag = False

            # Si la queue contient un fichier à lire
            if not self.play_queue.empty():
                file_target = self.play_queue.get()
                
                # Recherche du chemin du fichier
                path_to_play = None
                
                # 1. On vérifie si c'est un chemin direct (ex: envoyé par le TTS)
                if os.path.exists(file_target):
                    path_to_play = file_target
                else:
                    # 2. Sinon on cherche dans la liste des fichiers du dossier 'songs'
                    for audio in self.audio_files:
                        if audio.file_name == file_target:
                            path_to_play = audio.path
                            break

                if path_to_play:
                    try:
                        logger.info(f"🔊 Clio joue : {path_to_play}")
                        self.signals.AI_speaking = True
                        
                        # On utilise un thread pour que PowerShell ne bloque pas tout le programme
                        await asyncio.to_thread(self._play_mp3, path_to_play)
                        
                    except Exception as e:
                        logger.error(f"❌ Erreur lecture audio : {e}")
                    finally:
                        self.signals.AI_speaking = False
                else:
                    logger.warning(f"⚠️ Fichier non trouvé : {file_target}")

            await asyncio.sleep(0.1)

    def _play_mp3(self, path):
        """Lance la lecture via Windows Media Player en arrière-plan"""
        full_path = os.path.abspath(path)
        # Commande PowerShell qui attend la fin de la lecture (playState 1 = Arrêté)
        cmd = [
            "powershell",
            "-Command",
            f"$m = New-Object -ComObject WMPlayer.OCX; "
            f"$m.url = '{full_path}'; "
            f"$m.controls.play(); "
            f"while($m.playState -ne 1){{Start-Sleep -m 100}}"
        ]
        # Exécution silencieuse
        subprocess.run(cmd, capture_output=True)

    class Audio:
        """Structure pour stocker les infos des fichiers"""
        def __init__(self, file_name, path):
            self.file_name = file_name
            self.path = path

    class API:
        """Interface utilisée par les autres modules (TTS, etc.)"""
        def __init__(self, outer):
            self.outer = outer

        def get_audio_list(self):
            return [audio.file_name for audio in self.outer.audio_files]

        def play_audio(self, file_name_or_path):
            self.outer.play_queue.put(file_name_or_path)

        def stop_playing(self):
            # On vide la file d'attente
            while not self.outer.play_queue.empty():
                try: self.outer.play_queue.get_nowait()
                except: break
            self.outer.abort_flag = True

        def pause_audio(self):
            self.outer.paused = True

        def resume_audio(self):
            self.outer.paused = False