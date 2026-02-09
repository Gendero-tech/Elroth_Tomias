import requests
import json
import base64
import os
import random

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def clio_analyze_build(image_folder):
    # Choisir une image au hasard dans la mémoire
    all_images = [f for f in os.listdir(image_folder) if f.endswith('.jpg')]
    if not all_images:
        print("Maman, je n'ai aucune image en mémoire ! 😅")
        return
    
    selected_image = random.choice(all_images)
    image_path = os.path.join(image_folder, selected_image)
    
    print(f"🔍 Clio analyse ton build sur l'image : {selected_image}...")

    # Préparation de la requête pour Ollama
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "moondream", # Modèle vision
        "prompt": "Describe the items in this video game backpack. What is the main strategy?",
        "stream": False,
        "images": [encode_image(image_path)]
    }

    try:
        response = requests.post(url, json=data)
        result = response.json()
        description = result.get("response", "Je n'arrive pas à voir les détails...")
        
        print("\n--- 🤖 ANALYSE DE CLIO ---")
        print(description)
        print("--------------------------")
        
    except Exception as e:
        print(f"Erreur de connexion à Ollama : {e}")

if __name__ == "__main__":
    path = "training_data/BackpackBattles"
    clio_analyze_build(path)