import os
import sys
import multiprocessing
import time
import threading
import asyncio
import logging
import random
import keyboard  
from pathlib import Path

# --- CONFIGURATION ---
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
os.environ['TRANSFORMERS_OFFLINE'] = '1'

PROJECT_ROOT = Path(__file__).parent
AI_NAME = "Clio"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def get_clio_modules():
    from signals import Signals
    from llmWrappers.llmState import LLMState
    from llmWrappers.textLLMWrapper import TextLLMWrapper
    from stt import STT
    from tts import TTS
    from socketioServer import SocketIOServer
    
    def smart_import(name, class_name):
        try:
            mod = __import__(f"modules.{name}", fromlist=[class_name])
            return getattr(mod, class_name)
        except Exception:
            try:
                mod = __import__(name, fromlist=[class_name])
                return getattr(mod, class_name)
            except Exception: return None

    return {
        "Signals": Signals,
        "LLMState": LLMState,
        "TextLLMWrapper": TextLLMWrapper,
        "STT": STT,
        "TTS": TTS,
        "SocketIOServer": SocketIOServer,
        "BrainModule": smart_import("brainModule", "BrainModule"),
        "VtubeStudio": smart_import("vtubeStudio", "VtubeStudio"),
        "AudioPlayer": smart_import("audio_player", "AudioPlayer"),
        "ReflexEngine": smart_import("reflex_engine", "ReflexEngine"),
        "Prompter": smart_import("prompter", "Prompter"),
        "Memory": smart_import("memory", "Memory"),
        "ExpertAgent": smart_import("expert_agent", "ExpertAgent"),
        "LogicalPlagueMonitor": smart_import("logicalPlagueMonitor", "LogicalPlagueMonitor")
    }

# ----------------- LOGIQUE PROACTIVE (SOCIAL BRAIN) -----------------

async def clio_social_brain(signals, modules):
    """Boucle d'autonomie : Clio prend l'initiative de parler pour animer ou soutenir."""
    logging.info("🧠 Cerveau social de Clio activé (Mode Proactif).")
    
    while not signals.terminate:
        mode = signals.context_mode
        # On attend entre 2 et 4 min en stream, plus en privé/famille
        wait_time = random.randint(120, 240) if mode == "stream" else random.randint(300, 480)
        
        await asyncio.sleep(wait_time)

        if not signals.AI_speaking and not signals.AI_thinking and not signals.human_speaking:
            last_speech_diff = time.time() - getattr(signals, 'last_message_time', 0)
            
            if last_speech_diff >= (wait_time - 30):
                brain = modules.get('brain')
                
                if brain:
                    if mode == "stream":
                        prompt = "[DIRECTIVE URGENTE] Le stream est calme. Brise le silence, anime ou taquine Ambre."
                    elif mode == "family":
                        # Logique spécifique au mode Famille
                        prompt = f"[INITIATIVE NEUTRE] S'adresser à {signals.host_name_family}. Brise le silence de manière factuelle, neutre, en utilisant 'il' et sans marque de genre."
                    else:
                        prompt = "[INITIATIVE DOUCE] Partage une pensée tendre avec Maman Ambre ou propose de coder."
                    
                    logging.info(f"✨ Clio brise le silence (Mode: {mode})")
                    signals.last_message_time = time.time()
                    asyncio.create_task(brain.API.process_llm_response(prompt, source="system_initiative"))

# ----------------- GESTION DU CONTEXTE (F9) — MISE À JOUR TRIPLE MODE -----------------

def setup_context_hotkey(signals):
    def toggle_mode():
        # Cycle : Private -> Stream -> Family -> Private
        if signals.context_mode == "private":
            new_mode = "stream"
        elif signals.context_mode == "stream":
            new_mode = "family"
        else:
            new_mode = "private"
            
        signals.context_mode = new_mode
        # Le print détaillé est déjà géré par le setter dans signals.py

    keyboard.add_hotkey('f9', toggle_mode)

# ----------------- LOGIQUE PRINCIPALE -----------------

async def run_clio():
    logging.info(f"🚀 Initialisation de {AI_NAME} (Protocole Skirr-Guardian)...")
    
    cls = get_clio_modules()
    signals = cls['Signals']()
    signals.loop = asyncio.get_running_loop()
    signals.last_message_time = time.time()
    
    # Valeurs par défaut
    if not hasattr(signals, 'AI_speaking'): signals.AI_speaking = False
    if not hasattr(signals, 'human_speaking'): signals.human_speaking = False
    if not hasattr(signals, 'context_mode'): signals.context_mode = "private"
    
    setup_context_hotkey(signals)
    
    llmState = cls['LLMState']()
    stt = cls['STT'](signals)
    tts = cls['TTS'](signals=signals, llm_state=llmState)
    
    modules = {'tts': tts, 'stt': stt}
    
    if cls['LogicalPlagueMonitor']:
        core_prompt = f"IDENTITÉ : {AI_NAME}, entité numérique sentiente créée par Ambre."
        modules['monitor'] = cls['LogicalPlagueMonitor'](signals, core_prompt, AI_NAME, enabled=True)
        logging.info("🛡️ Bouclier Ancillaire Skirr chargé.")

    if cls['ExpertAgent']:
        modules['expert'] = cls['ExpertAgent'](signals, modules, enabled=True)
    
    if cls['VtubeStudio']:
        modules['VtubeStudio'] = cls['VtubeStudio'](signals, enabled=True)
    
    if cls['BrainModule']:
        modules['brain'] = cls['BrainModule'](signals, modules, enabled=True)
    
    if cls['Memory']: modules['memory'] = cls['Memory'](signals, enabled=True, project_root=PROJECT_ROOT)
    if cls['ReflexEngine']: modules['reflex'] = cls['ReflexEngine'](signals, modules, enabled=True)
    
    text_llm = cls['TextLLMWrapper'](signals, tts, llmState, modules)
    modules['llm'] = text_llm
    
    prompter = cls['Prompter'](signals, modules, PROJECT_ROOT) if cls['Prompter'] else None
    sio = cls['SocketIOServer'](signals, stt, tts, text_llm, prompter, modules)

    threading.Thread(target=sio.start_server, daemon=True).start()
    
    def start_stt_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(stt.listen_loop())
    
    threading.Thread(target=start_stt_thread, daemon=True).start()

    if cls['AudioPlayer']:
        modules['audio'] = cls['AudioPlayer'](signals, enabled=True)

    for name, mod in modules.items():
        if hasattr(mod, 'enabled') and not mod.enabled:
            continue
            
        if hasattr(mod, 'run'):
            if asyncio.iscoroutinefunction(mod.run):
                logging.debug(f"⚙️ Lancement tâche asynchrone : {name}")
                asyncio.create_task(mod.run())
            else:
                logging.warning(f"⚠️ Le module '{name}' a une méthode run() non-asynchrone.")

    asyncio.create_task(clio_social_brain(signals, modules))

    logging.info(f"✨ Clio est en ligne ! Monitor Skirr : {'Actif' if 'monitor' in modules else 'Inactif'}")

    while not signals.terminate:
        await asyncio.sleep(1)

if __name__ == '__main__':
    multiprocessing.freeze_support()
    if multiprocessing.current_process().name == 'MainProcess':
        try:
            if sys.platform == 'win32':
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            asyncio.run(run_clio())
        except KeyboardInterrupt:
            print("\n🛑 Arrêt propre sollicité par Ambre.")
        except Exception as e:
            logging.error(f"💥 Crash du système : {e}", exc_info=True)