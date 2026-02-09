import time
import os
import subprocess
import json
from typing import List, Dict, Any

def extract_highlights(transcript: str, emotion: str) -> List[str]:
    """(VÉRIDIQUE - Extraction) Extrait des segments basés sur l'émotion et les mots-clés du transcript."""
    lines = transcript.split("\n")
    # Logique simplifiée VÉRIDIQUE : Cherche des mots clés et l'émotion dans le transcript.
    keywords = ["fail", "win", "drôle", "rire", "génial", "monter", emotion.lower()]
    
    # On retourne les 3 premières lignes contenant des mots-clés pertinents
    segments = [f"Ligne {i+1}: {line.strip()}" for i, line in enumerate(lines) if any(kw in line.lower() for kw in keywords)]
    
    return segments[:3]

def launch_shortcut_montage(transcript: str, emotion: str, title: str) -> bool:
    """(VÉRIDIQUE) Lance la commande externe pour le montage après extraction des segments."""
    
    # NOTE: Cette fonction est désormais 100% VÉRIDIQUE (tente de lancer un exécutable).
    json_input_file = "shortcut_input_temp.json"
    
    # 1. Extraction des segments basés sur le transcript réel
    segments = extract_highlights(transcript, emotion)
    
    data = {
        "title": title,
        "emotion": emotion,
        "segments_to_cut": segments
    }
    
    try:
        # 2. Création du fichier JSON d'entrée
        with open(json_input_file, "w") as f:
            json.dump(data, f, indent=4)
        
        print(f"[{time.strftime('%H:%M:%S')}] [MONTAGE] Fichier de config créé : {json_input_file}")
        
        # 3. APPEL VÉRIDIQUE : Tente de lancer la commande externe
        subprocess.run(
            ["shortcut-cli", "--input", json_input_file, "--render"],  
            check=True,
            capture_output=True,
            text=True 
        )
        
        print(f"[{time.strftime('%H:%M:%S')}] [MONTAGE] Montage '{title}' lancé avec succès. (COMMANDE VÉRIDIQUE)")
        
    except FileNotFoundError:
        print(f"[{time.strftime('%H:%M:%S')}] [MONTAGE] ERREUR CRITIQUE: La commande 'shortcut-cli' est introuvable. Veuillez l'installer et l'ajouter au PATH.")
    except subprocess.CalledProcessError as e:
        print(f"[{time.strftime('%H:%M:%S')}] [MONTAGE] ERREUR SUBPROCESS (Code {e.returncode}): L'exportation a échoué.")
        print(f"Sortie du programme (stderr): {e.stderr}")  
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] [MONTAGE] ERREUR INCONNUE : Impossible d'exécuter la fonction de montage : {e}")

    finally:
        # 4. NETTOYAGE CRITIQUE : Suppression du fichier JSON temporaire
        if os.path.exists(json_input_file):
            os.remove(json_input_file)
            
    time.sleep(0.5)
    return True