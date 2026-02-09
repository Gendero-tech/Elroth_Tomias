import requests
import os
import random
import time

def call_ollama(model, prompt, images=None):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "keep_alive": 0 # Force le modèle à s'effacer après la réponse
    }
    if images:
        payload["images"] = images
    
    try:
        r = requests.post(url, json=payload, timeout=60)
        return r.json().get("response", "")
    except:
        return ""

def run():
    path = "training_data/BackpackBattles"
    images = [f for f in os.listdir(path) if f.endswith('.jpg')]
    if not images: return
    
    target = os.path.join(path, random.choice(images))
    import base64
    with open(target, "rb") as f:
        img_data = base64.b64encode(f.read()).decode('utf-8')

    print("📸 Clio regarde l'image...")
    # On demande à Moondream une description très courte pour économiser la RAM
    desc = call_ollama("moondream", "What items are in the backpack? (Short list)", [img_data])
    
    if not desc:
        print("❌ Moondream n'a pas répondu.")
        return

    print(f"👀 Description : {desc[:50]}...")
    print("⏳ Pause technique (Libération de la RAM)...")
    time.sleep(3) # On laisse 3 secondes pour que le GPU respire

    print("🧠 Phi-3 réfléchit...")
    final = call_ollama("phi3", f"Tu es l'IA de Ambre. Commente brièvement ce build : {desc}")
    
    print("\n--- 🤖 CLIO ---")
    if final:
        print(final)
    else:
        # Si Phi-3 échoue, on donne une réponse de secours "IA"
        print(f"Maman, je vois des objets ({desc[:30]}), mais mon cerveau est trop plein pour analyser !")
    print("----------------\n")

if __name__ == "__main__":
    run()