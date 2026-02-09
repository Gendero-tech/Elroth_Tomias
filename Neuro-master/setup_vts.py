import asyncio
import pyvts
import os

async def register_clio():
    print("--- CONFIGURATION INITIALE DE CLIO POUR VTUBE STUDIO ---")
    
    # 1. Définition du plugin
    plugin_info = {
        "plugin_name": "Clio VTS Ultimate",
        "developer": "Ambre",
        "authentication_token_path": "./vtubeStudio_token.txt"
    }
    
    # --- MODIFICATION ICI : On force le port 8005 ---
    # Par défaut pyvts utilise 8001, ce qui causait ton erreur 1225
    myvts = pyvts.vts(plugin_info=plugin_info, port=8005)
    
    print("1. Connexion à VTube Studio (Port 8005)...")
    try:
        await myvts.connect()
        print("   -> Connecté !")
    except Exception as e:
        print(f"   -> ERREUR : VTube Studio est-il ouvert ? API activée sur le port 8005 ? ({e})")
        return

    print("\n2. Demande d'autorisation...")
    print("   >>> REGARDE TON ÉCRAN VTUBE STUDIO ET CLIQUE SUR 'ALLOW' (AUTORISER) MAINTENANT <<<")
    
    try:
        await myvts.request_authenticate_token()
        await myvts.request_authenticate()
        print("   -> SUCCÈS ! Token reçu et fichier 'vtubeStudio_token.txt' créé.")
    except Exception as e:
        print(f"   -> Erreur lors de l'authentification : {e}")
    
    await myvts.close()
    print("\n--- FIN DE LA CONFIGURATION. TU PEUX LANCER MAIN.PY ---")

if __name__ == "__main__":
    asyncio.run(register_clio())