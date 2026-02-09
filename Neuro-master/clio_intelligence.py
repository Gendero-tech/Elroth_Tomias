import requests
import base64
import os
import random

def analyser_jeu(image_folder="training_data/BackpackBattles"):
    """
    Cette fonction permet à Clio de 'regarder' et de donner son avis.
    Elle peut être appelée depuis n'importe quel autre fichier.
    """
    images = [f for f in os.listdir(image_folder) if f.endswith('.jpg')]
    if not images:
        return "Maman, je n'ai pas de souvenirs à analyser."

    img_path = os.path.join(image_folder, random.choice(images))
    
    with open(img_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode('utf-8')

    url = "http://localhost:11434/api/generate"
    prompt = "Tu es Clio, l'IA d'Ambre. Analyse cette image de jeu et donne un conseil tactique court en français."
    
    payload = {
        "model": "llava", # Ou "moondream" si tu préfères
        "prompt": prompt,
        "stream": False,
        "images": [img_b64]
    }

    try:
        r = requests.post(url, json=payload)
        return r.json().get("response", "Je vois l'image, mais je ne sais pas quoi dire.")
    except Exception as e:
        return f"Erreur de connexion à mon cerveau : {e}"