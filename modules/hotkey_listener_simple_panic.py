# Fichier : hotkey_listener_simple_panic.py
import keyboard
import sys
import threading
import time

# --- MOCKS NECESSAIRES ---
# Simuler l'API du ControlModule pour l'appel de sécurité
class PanicControlAPI:
    def lock_control(self, status: bool):
        print(f"🔒 [PANIC_API] Verrouillage global demandé: {status}")
    def release_all(self):
        print("🚨 [PANIC_API] Relâchement de tous les boutons et touches (Urgence).")

# --- INITIALISATION ---
global_control_api = PanicControlAPI()

# 🚨 NOUVEAU HOTKEY D'URGENCE
PANIC_HOTKEY = "²" 

def panic_mode_toggle():
    """Déclenche le verrouillage du contrôle et le relâchement immédiat."""
    global_control_api.lock_control(True) # Verrouille le contrôle
    time.sleep(0.1)
    global_control_api.release_all() # Relâche les touches
    print(f"===========================================================")
    print(f"|  CLIO PANIC MODE ACTIVÉ. Contrôle restitué à l'humain. |")
    print(f"===========================================================")


def start_panic_listener():
    print(f"CLIO DÉFENSE 🎧 Écoute active du Hotkey de Panique : {PANIC_HOTKEY}")
    
    # Enregistre le hotkey pour appeler la fonction de panique
    keyboard.add_hotkey(PANIC_HOTKEY, panic_mode_toggle)

    try:
        # Garde le thread en vie jusqu'à ce que l'utilisateur appuie sur 'esc'
        keyboard.wait("esc") 
    except KeyboardInterrupt:
        pass
    finally:
        print("Arrêt de l'écoute des hotkeys.")

if __name__ == "__main__":
    start_panic_listener()