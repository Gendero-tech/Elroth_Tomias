import asyncio
import queue
import logging
import time
from typing import List, Dict, Any, Optional

logger = logging.getLogger('Signals')

class Signals:
    """
    Classe centrale d'échange et de gestion des signaux pour Clio.
    Gère la circulation de l'information entre la Vision, les Réflexes et le Cerveau.
    """

    def __init__(self):
        # 🚩 Signal d'arrêt global et modules
        self._terminate = False
        self.modules: Dict[str, Any] = {} 
        self.loop: Optional[asyncio.AbstractEventLoop] = None

        # ⚙️ Configuration d'identité et Contexte
        self._context_mode = "private" # "private", "stream", ou "family"
        self._current_game = "none" 
        self.ai_name = "Clio"
        
        # 🧠 Mémoire et Intelligence
        self.history: List[Dict[str, str]] = [] # Stocke le dialogue pour Ollama
        self._AI_thinking = False
        self._AI_speaking = False

        # 🎤 Événements et queues asynchrones
        self.action_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self.new_stt_result = asyncio.Event()
        self.response_ready = asyncio.Event()
        self.dashboard_update_event = asyncio.Event()
        
        # 🔗 Files de communication (Dashboard & TTS)
        # SimpleQueue pour éviter les conflits de threads
        self.sio_queue: queue.SimpleQueue[tuple[str, Any]] = queue.SimpleQueue()
        self.transcribed_text_queue: queue.Queue[str] = queue.Queue()

    # 🚀 MÉTHODES DE GESTION D'IDENTITÉ
    def get_current_host_name(self) -> str:
        """ Retourne le nom que Clio doit utiliser selon le contexte actuel """
        from constants import HOST_NAME_PRIVATE, HOST_NAME_STREAM, HOST_NAME_FAMILY
        if self._context_mode == "private":
            return HOST_NAME_PRIVATE
        elif self._context_mode == "family":
            return HOST_NAME_FAMILY
        return HOST_NAME_STREAM

    # ----------------------------------------------------
    # PROPRIÉTÉS (SETTERS) - Déclenchent des actions auto
    # ----------------------------------------------------

    @property
    def context_mode(self) -> str:
        return self._context_mode

    @context_mode.setter
    def context_mode(self, value: str):
        allowed_modes = ["private", "stream", "family"]
        val = value.lower()
        if val in allowed_modes and self._context_mode != val:
            self._context_mode = val
            print(f"🎹 SIGNALS: Bascule identité -> {val.upper()} | Cible: {self.get_current_host_name()}")
            self.sio_queue.put(('context_mode', val))

    @property
    def AI_speaking(self) -> bool:
        return self._AI_speaking

    @AI_speaking.setter
    def AI_speaking(self, value: bool):
        self._AI_speaking = value
        self.sio_queue.put(('AI_speaking', value))
        if value:
            # On logge en debug pour ne pas polluer mais on garde l'info
            logger.debug(f"🔊 {self.ai_name} parle...")

    @property
    def AI_thinking(self) -> bool:
        return self._AI_thinking

    @AI_thinking.setter
    def AI_thinking(self, value: bool):
        self._AI_thinking = value
        self.sio_queue.put(('AI_thinking', value))

    @property
    def terminate(self) -> bool:
        return self._terminate

    @terminate.setter
    def terminate(self, value: bool):
        self._terminate = value
        if value:
            self.sio_queue.put(('system_terminate', True))
            print("🛑 SIGNALS: Signal d'arrêt global activé.")