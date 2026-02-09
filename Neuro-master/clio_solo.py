import requests
import base64
import os
import random

def clio_vision_direct(image_folder):
    # Sélection
    images = [f for f in os.listdir(image_folder) if f.endswith('.jpg')]
    if not images: return
    img_path = os.path.join(image_folder, random.choice(images))
    
    with open(img_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode('utf-8')

    print(f"📸 Clio (LLaVA) analyse ton build...")

    url = "http://localhost:11434/api/generate"
    # Ici, on demande TOUT d'un coup
    prompt = "Tu es Clio, l'assistante de Ambre. Regarde ce sac à dos de jeu. Dis-moi en français quel est l'objet le plus fort que tu vois et donne un petit conseil."
    
    payload = {
        "model": "llava", 
        "prompt": prompt,
        "stream": False,
        "images": [img_b64]
    }

    try:
        r = requests.post(url, json=payload)
        response = r.json().get("response", "Je n'ai pas pu analyser l'image.")
        print("\n--- 🤖 CONSEIL DIRECT DE CLIO ---")
        print(response)
        print("---------------------------------\n")
    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    clio_vision_direct("training_data/BackpackBattles")