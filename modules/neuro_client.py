import websocket
import threading
import json
import time
import logging
import asyncio
from modules.module import Module
from typing import Optional, Any, Dict, List

log = logging.getLogger('NeuroClient')
log.setLevel(logging.INFO)

class NeuroClient(Module):
    """
    Système Nerveux de Clio : Gère la connexion WebSocket avec le jeu (Warframe/MMO)
    et injecte le contexte décisionnel dans le LLM.
    """
    def __init__(self, signals, tts_module=None, vts_module=None, prompter_module=None, modules=None, enabled: bool = True):
        super().__init__(signals, enabled)
        self.tts = tts_module      
        self.vts = vts_module      
        self.prompter = prompter_module 
        self.modules = modules or {}
        
        # Configuration WebSocket
        self.ws_url = "ws://localhost:8000" 
        self.ws: Optional[websocket.WebSocketApp] = None 
        self.is_connected = False
        
        # Contexte et Objectifs
        self.game_context: Dict[str, Any] = {} 
        self.current_game_goal: str = "Pas d'objectif défini (mode exploration)." 
        
        # Paramètres de résilience
        self.retry_count = 0
        self.max_retries = 5
        self.loop_running = False 

        # Enregistrement automatique pour l'injection de prompt
        if prompter_module and hasattr(prompter_module, 'register_module_injection'):
             prompter_module.register_module_injection(self.get_prompt_injection, priority=200)
             log.info("🎮 NeuroClient : Injection de contexte enregistrée dans le Prompter.")
        
        self.API = self.API(self)

    # --- ARC RÉFLEXE (SURVIE) ---
    def _check_auto_reflexes(self):
        """ Analyse le contexte en temps réel pour déclencher des actions de survie immédiates. """
        if not self.game_context: return

        # Exemple Warframe : Si la vie est sous 25%, on force un soin ou un bouclier
        hp = self.game_context.get('vie', 100)
        # Nettoyage si c'est une string (ex: "45%")
        if isinstance(hp, str): hp = int(''.join(filter(str.isdigit, hp)) or 100)

        if hp < 25:
            log.warning(f"🚨 RÉFLEXE : Santé critique ({hp}%). Envoi d'une commande de survie.")
            self.API.send_game_action("EMERGENCY_HEAL")
            # On signale au TTS de prévenir l'utilisateur
            if self.tts:
                self.signals.new_message = True # Réveille le Brain pour un commentaire oral

    # --- SYNTHÈSE POUR LE LLM ---
    def get_prompt_injection(self) -> str:
        """ Synthétise les données complexes du jeu en langage naturel pour le Cerveau de Clio. """
        if not self.is_connected:
             return f"[ÉTAT JEU : DÉCONNECTÉ] Rappel objectif : {self.current_game_goal}"

        context_synth = f"\n--- 🎮 CONTEXTE TEMPS RÉEL (SDK) ---\n"
        context_synth += f"OBJECTIF DE SESSION : {self.current_game_goal}\n"
        
        try:
            hp = self.game_context.get('vie', 'Inconnue')
            enemies = self.game_context.get('ennemis_proches', 0)
            energy = self.game_context.get('energie', '100%')
            
            context_synth += f"STATS: ❤️ {hp} | ⚡ {energy} | ⚠️ Ennemis: {enemies}\n"
            context_synth += f"LOCALISATION: {self.game_context.get('zone', 'Secteur inconnu')}\n"
            
            # Limiter la taille du contexte brut pour économiser les tokens
            raw_data = str(self.game_context)[:150] + "..."
            context_synth += f"DONNÉES CAPTEURS: {raw_data}\n"
            context_synth += "COMMANDE DISPONIBLE: [DELEGATE:NEURO:nom_action]\n"
            
        except Exception as e:
            context_synth += f"ERREUR SYNTHÈSE : {e}"
            
        return context_synth

    # --- GESTION DE LA CONNEXION ---
    def init_event_loop(self):
        if self.enabled:
            self.start_connection_thread()

    def start_connection_thread(self):
        if not self.loop_running:
            threading.Thread(target=self.connect_loop, daemon=True).start()

    def connect_loop(self):
        self.loop_running = True
        while not self.signals.terminate:
            if self.retry_count >= self.max_retries:
                log.error("🛑 NeuroClient : Échecs répétés. Mise en veille de la connexion.")
                self.loop_running = False
                break

            try:
                self.ws = websocket.WebSocketApp(
                    self.ws_url,
                    on_open=self.on_open,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close
                )
                self.ws.run_forever()
                time.sleep(5)
                self.retry_count += 1
            except Exception as e:
                log.error(f"Erreur Loop Neuro: {e}")
                time.sleep(5)

    def on_open(self, ws):
        log.info("✅ NeuroClient : Liaison établie avec le port 8000.")
        self.is_connected = True
        self.retry_count = 0
        ws.send(json.dumps({"command": "startup", "identity": "CLIO_AGENT_V2"}))

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            if "context" in data:
                self.game_context = data["context"]
                self._check_auto_reflexes() # Vérification immédiate sans passer par le LLM
        except Exception as e:
            log.debug(f"Message non-JSON: {message}")

    def on_error(self, ws, error):
        log.warning(f"⚠️ Erreur WebSocket Neuro : {error}")

    def on_close(self, ws, code, msg):
        log.info("🔌 NeuroClient : Connexion fermée.")
        self.is_connected = False

    # --- INTERFACE API ---
    class API:
        def __init__(self, outer: 'NeuroClient'):
            self.outer = outer

        def set_game_goal(self, goal: str):
            """ Définit ce que Clio doit accomplir (ex: 'Protéger Gendero pendant le farm') """
            self.outer.current_game_goal = goal
            log.info(f"🎯 Nouvel objectif : {goal}")

        def send_game_action(self, action_name: str):
            """ Envoie une commande physique au jeu. """
            if not self.outer.is_connected:
                return "Erreur : NeuroClient déconnecté."

            payload = {"command": "action", "data": action_name}
            try:
                self.outer.ws.send(json.dumps(payload))
                log.info(f"🎮 ACTION ENVOYÉE : {action_name}")
                return f"Action {action_name} exécutée."
            except Exception as e:
                return f"Échec action : {e}"

        def get_current_state(self):
            return self.outer.game_context