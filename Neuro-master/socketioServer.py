import socketio
import uvicorn
import logging
import asyncio
import json
import os
import subprocess
import sys
import threading
import time
import re
from typing import Dict, Any, List, Optional

# --- NOUVEAUX IMPORTS (pour les routes HTTP) ---
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

# --- FILE D'ATTENTE GLOBALE ---
twitch_webhook_queue = asyncio.Queue()

# Configure le logging pour ce module
log = logging.getLogger('SocketIOServer')

class SocketIOServer:
    def __init__(self, signals, stt, tts, llms, prompter, modules):
        log.info("Initialisation du SocketIOServer (Mode Fusionné Corrigé V6 - VTS Assets)...")
        self.signals = signals
        self.stt = stt
        self.tts = tts
        self.llmWrapper = llms  
        self.prompter = prompter
        self.modules = modules

        # --- 1. Création du serveur HTTP (Starlette) ---
        self.http_app = Starlette(routes=[
            Route('/api/twitch_input', endpoint=self.handle_twitch_webhook, methods=['POST']),
            # Route pour les actions LLM directes sur les experts (ex: BrainModule)
            Route('/api/delegate_action', endpoint=self.handle_delegate_action, methods=['POST']), 
            Route('/api/explain', endpoint=self.handle_explain, methods=['POST']), 
        ])

        # --- 2. Création du serveur Socket.IO ---
        self.sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
        
        # --- 3. FUSION DES DEUX ---
        self.app = socketio.ASGIApp(self.sio, other_asgi_app=self.http_app)

        self.register_handlers()
        log.info("Écouteurs d'événements (SIO + HTTP) enregistrés.")
        
    def clean_chat_history(self, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if not history: return []
        cleaned_history = []
        for message in history:
            role = message.get("role")
            content_safe = message.get("content") or ""
            message["content"] = content_safe
            if role not in ['user', 'assistant', 'system']: continue
            if not cleaned_history:
                cleaned_history.append(message)
                continue
            last_role = cleaned_history[-1]['role']
            if last_role == 'system' and role == 'system':
                 cleaned_history[-1]['content'] += "\n\n[INSTRUCTION FUSIONNÉE] " + message["content"]
                 continue
            if role == last_role and role != 'system':
                log.warning(f"Alternance de rôle cassée détectée: {role}. Fusion.")
                cleaned_history[-1]['content'] += "\n\n[MESSAGE FUSIONNÉ] " + message["content"]
            else:
                cleaned_history.append(message)
        return cleaned_history

    # --- NOUVEAU GESTIONNAIRE HTTP POUR LA DÉLÉGATION ---
    async def handle_delegate_action(self, request: Request):
        """Permet au Dashboard d'appeler directement une action de délégation LLM (simule le format LLM)."""
        try:
             data = await request.json()
             action_type = data.get('type').upper() # Ex: NEURO
             action_prompt = data.get('prompt')   # Ex: add_game_entry(...)
             
             if not action_type or not action_prompt:
                 return JSONResponse({"status": "error", "message": "Type ou prompt manquant"}, status_code=400)
                 
             response_text = f"[DELEGATE:{action_type}:{action_prompt}]"
             
             # Utilise la logique de délégation du Prompter (qui gère l'exécution réelle)
             final_response = await asyncio.to_thread(self.prompter._handle_delegation, response_text)

             if final_response: # Si la délégation a eu lieu
                 return JSONResponse({"status": "success", "response": "Action déléguée et exécutée."}, status_code=200)
             else:
                 return JSONResponse({"status": "error", "message": "Action non reconnue par le Prompter."}, status_code=400)

        except Exception as e:
            log.error(f"[WEBHOOK ERROR] : {e}")
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


    # --- GESTIONNAIRES HTTP (Inchangés) ---
    async def handle_twitch_webhook(self, request: Request):
        try:
            data = await request.json()
            username = data.get('username', 'UtilisateurTwitch')
            message = data.get('message', '')
            message_type = data.get('type', 'CHAT_MESSAGE')
            await twitch_webhook_queue.put({"username": username, "message": message, "type": message_type})
            self.signals.new_message = True 
            log.info(f"[WEBHOOK] Message Twitch reçu de {username}")
            return JSONResponse({"status": "received", "user": username}, status_code=200)
        except Exception as e:
            log.error(f"[WEBHOOK ERROR] : {e}")
            return JSONResponse({"status": "error", "message": str(e)}, status_code=400)

    async def handle_explain(self, request: Request):
        try:
            data = await request.json()
            log.info(f"[API] Requête 'Expliquer segment' reçue.")
            if self.prompter and hasattr(self.prompter, 'explain_segment'):
                explanation_result = await asyncio.to_thread(self.prompter.explain_segment, data)
                return JSONResponse({"explanation": explanation_result}, status_code=200)
            else:
                return JSONResponse({"status": "error", "message": "Prompter non initialisé"}, status_code=500)
        except Exception as e:
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    # --- GESTIONNAIRES SOCKET.IO ---
    def register_handlers(self):
        
        @self.sio.on('connect')
        async def handle_connect(sid, environ):
            log.info(f"Client Connecté (Cockpit Streamlit): {sid}")
            await self.sio.emit('server_message', {'data': 'Connexion au Cerveau de Clio réussie!'}, room=sid)

        @self.sio.on('disconnect')
        async def handle_disconnect(sid):
            log.warning(f"Client Déconnecté: {sid}")

        # --- Chat LLM SYNCHRONE ---
        @self.sio.on('request_llm_response')
        async def handle_llm_request(sid, data):
            log.info(f"Requête LLM synchrone reçue de {sid}")
            prompt = data.get('prompt')
            chat_history = data.get('chat_history', []) 
            system_instruction = data.get('system_instruction', '')

            def sync_llm_call(p, s_inst, hist):
                current_history = hist.copy() if hist is not None else [] 
                current_history = self.clean_chat_history(current_history)
                
                # 🚨 AJOUT DES INSTRUCTIONS SYSTÈME AU DÉBUT DE L'HISTORIQUE
                if s_inst:
                     if not current_history or current_history[0].get("role") != "system":
                         current_history.insert(0, {"role": "system", "content": s_inst})
                     else:
                         current_history[0]["content"] += "\n\n[INSTRUCTION SYSTÈME AJOUTÉE] " + s_inst
                
                current_history.append({"role": "user", "content": p})
                
                # Le Prompter est l'intermédiaire qui gère l'injection de contexte (RAG, NEURO)
                # Nous simulons l'appel direct pour cet endpoint synchrone
                return self.llmWrapper.get_response(current_history) 

            try:
                response = await asyncio.to_thread(sync_llm_call, prompt, system_instruction, chat_history)
                if isinstance(response, str) and response.startswith("Erreur du Cerveau"): raise Exception(response)
                
                # 🚀 AMÉLIORATION : Délégation après la réponse synchrone (comme dans Prompter.py)
                is_delegated = await asyncio.to_thread(self.prompter._handle_delegation, response)
                
                if is_delegated:
                    # Si c'est une délégation (ex: VTS), la réponse vocale a déjà été donnée.
                    return f"[Action Déléguée - Voir console/logs]" 
                
                return response
            except Exception as e:
                log.error(f"Erreur LLM: {e}", exc_info=True)
                return f"Erreur du Cerveau (LLM): {e}"

        # --- Chat LLM ASYNCHRONE ---
        @self.sio.on('request_chat_response')
        async def handle_chat_request(sid, data):
            chat_history = data.get('chat_history', [])
            chat_history.append({"role": "user", "content": data.get('prompt')})
            self.signals.history = chat_history 
            self.signals.new_message = True

        # --- CONTROLE TTS ---
        @self.sio.on('control_tts')
        async def handle_tts_control(sid, data):
            text_to_speak = data.get('text')
            style = data.get('style', 'chat')
            log.info(f"Ordre TTS (VRAI) reçu: {text_to_speak[:20]}...")
            
            tts_module = self.modules.get('tts')
            if tts_module and hasattr(tts_module, 'API'):
                await asyncio.to_thread(tts_module.API.speak, text_to_speak, style) 
            
            # Sync lèvres/émotion
            avatar_module = self.modules.get('vtube_studio') or self.modules.get('animaze_osc')
            if avatar_module and hasattr(avatar_module, 'API') and hasattr(avatar_module.API, 'send_hotkey'):
                await asyncio.to_thread(avatar_module.API.send_hotkey, style)

        # --- CONTROLE TWITCH ---
        @self.sio.on('control_twitch')
        async def handle_twitch_control(sid, data):
            action = data.get('action')
            value = data.get('value')
            log.info(f"Ordre TWITCH (VRAI) reçu: {action}")
            twitch_client = self.modules.get('twitch')
            if not twitch_client or not hasattr(twitch_client, 'API'): return
            try:
                if action == 'GO_LIVE': twitch_client.API.go_live() 
                elif action == 'UPDATE_INFO': twitch_client.API.update_info(title=value.get('title'), game=value.get('game'))
            except Exception as e: log.error(f"Erreur Twitch: {e}")

        # --- CONTROLE JEUX (Simplifié et corrigé pour utiliser l'API BrainModule) ---
        @self.sio.on('control_game')
        async def handle_game_control(sid, data):
            action = data.get('action')
            log.info(f"Ordre JEU (VRAI) reçu: {action}")
            game_brain = self.modules.get('game_brain') 
            if not game_brain or not hasattr(game_brain, 'API'): return "Module Jeu absent"
            try:
                api = game_brain.API
                
                if action == 'SCAN_GAMES': 
                     return api.scan_for_games() 
                elif action == 'ADD_GAME': 
                    # 🚨 CORRECTION : Utilise la méthode add_game_entry avec tous les arguments
                    return api.add_game_entry(
                        game_name=data.get('name'), 
                        executable=data.get('exec'), 
                        search_pattern=data.get('pattern'),
                        save_pattern=data.get('save_pattern')
                    )
                elif action == 'LAUNCH_GAME': 
                     return api.launch_game_for_training(data.get('game_name'))
                elif action == 'START_PLAYING':
                     api.start_clio_playing(data.get('game_name'))
                     return "Clio prend le contrôle du jeu."
                elif action == 'STOP_PLAYING':
                     api.stop_clio_playing()
                     return "Clio relâche le contrôle."
                return "Action de jeu non reconnue."
            except Exception as e: return f"Erreur Jeu: {e}"

        # --- CONTROLE MONTAGE ---
        @self.sio.on('control_montage')
        async def handle_montage_control(sid, data):
            action = data.get('action')
            montage_module = self.modules.get('maintenance') 
            if not montage_module: return
            try:
                if action == 'GENERATE_SCRIPT': 
                    return await asyncio.to_thread(montage_module.API.generate_reaction_script, data.get('transcript'))
                elif action == 'LAUNCH_MONTAGE':
                    await asyncio.to_thread(montage_module.API.launch_shortcut_montage, transcript=data.get('transcript'), emotion=data.get('emotion'), title=data.get('title'))
            except Exception as e: log.error(f"Erreur Montage: {e}")

        # --- CONTROLE VTUBE STUDIO (CORRIGÉ ET COMPLET) ---
        @self.sio.on('control_animaze') # On garde le nom du canal pour compatibilité
        async def handle_animaze_control(sid, data):
            action = data.get('action')
            payload = data.get('data')

            vts_module = self.modules.get('vtube_studio') or self.modules.get('animaze_osc')
            
            if not vts_module or not hasattr(vts_module, 'API'):
                 log.error("⚠️ Module VTube Studio introuvable.")
                 return

            api = vts_module.API

            try:
                if action == 'send_hotkey' or action == 'set_expression':
                    api.send_hotkey(payload)
                elif action == 'set_mouth_open':
                    api.set_mouth_open(payload)
                elif action == 'spawn_microphone':
                    api.spawn_microphone()
                elif action == 'despawn_microphone':
                    api.despawn_microphone()
                elif action == 'move_model':
                    api.move_model(payload)
                elif action == 'SET_ACTIVE':
                    api.set_movement_status(True)
                    api.send_hotkey('gentle')
                elif action == 'SET_IDLE':
                    api.set_movement_status(False)
                elif action == 'LAUNCH':
                    if hasattr(api, 'start_connection'): api.start_connection()
                elif action == 'load_item':
                    api.load_item(payload)
                elif action == 'unload_item':
                    api.unload_item(payload)

            except Exception as e:
                 log.error(f"❌ Erreur lors de l'exécution de la commande VTS '{action}': {e}")


        # --- REDEMARRAGE DOUX ---
        @self.sio.on('dashboard_soft_restart')
        async def dashboard_soft_restart(sid):
            log.warning("🚨 Signal SOFT RESTART. Arrêt propre...")
            if self.modules.get('memory') and hasattr(self.modules['memory'], 'shutdown'):
                await asyncio.to_thread(self.modules['memory'].shutdown)

            self.signals.terminate = True
            
            def restart_process_and_exit():
                time.sleep(1) 
                subprocess.Popen([sys.executable] + sys.argv)
                os._exit(0) 

            threading.Thread(target=restart_process_and_exit, daemon=True).start()
            await self.sio.disconnect(sid)

    def start_server(self):
        """Lance le serveur Uvicorn (HTTP + SocketIO)."""
        port_to_use = 8081 
        log.info(f"Démarrage du serveur Uvicorn (HTTP+SIO) sur http://localhost:{port_to_use}")
        try:
            uvicorn.run(self.app, host='127.0.0.1', port=port_to_use, log_level="warning")
        except OSError as e:
            if e.errno == 10048 or e.errno == 98:
                log.critical(f"❌ ERREUR FATALE: Port {port_to_use} occupé.")
            else:
                log.critical(f"Erreur serveur: {e}")
            self.signals.terminate = True
        except Exception as e:
            log.critical(f"Échec démarrage serveur: {e}")
            self.signals.terminate = True