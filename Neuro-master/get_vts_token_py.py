import asyncio
import websockets
import json

PLUGIN_INFO = {
    "pluginName": "Clio VTS Plugin (Token)",
    "developerName": "Ambre",
    "authenticationToken": None,
    "apiVersion": "1.0",
}
VTS_ADDRESS = "ws://localhost:8000"

async def authenticate_and_get_token():
    try:
        # Se connecter au WebSocket de VTS
        async with websockets.connect(VTS_ADDRESS) as websocket:
            print(f"✅ Connecté à VTube Studio sur {VTS_ADDRESS}")

            # 1. Demander le jeton (simule la demande d'autorisation)
            request = {
                "apiName": "VTubeStudio",
                "apiVersion": "1.0",
                "requestID": "1",
                "messageType": "AuthenticationTokenRequest",
                "data": {
                    "pluginName": PLUGIN_INFO["pluginName"],
                    "developerName": PLUGIN_INFO["developerName"]
                }
            }
            await websocket.send(json.dumps(request))
            print("➡️ Demande d'autorisation envoyée. VEUILLEZ REGARDER VTS !")
            
            # 2. Recevoir la réponse (qui contient le jeton si autorisé)
            response = await asyncio.wait_for(websocket.recv(), timeout=20)
            data = json.loads(response)

            if data.get("messageType") == "AuthenticationTokenResponse" and data["data"].get("authenticationToken"):
                token = data["data"]["authenticationToken"]
                with open("vtubeStudio_token.txt", "w") as f:
                    f.write(token)
                print(f"✅ Jeton généré et sauvegardé dans 'vtubeStudio_token.txt'.")
                print("Le module VTS de Clio est maintenant prêt.")
            else:
                print(f"❌ Échec de la génération du jeton. Réponse: {data.get('data', {}).get('reason', 'Vérifiez la console VTS.')}")

    except ConnectionRefusedError:
        print("❌ ERREUR: VTube Studio n'est pas lancé ou l'API n'est pas activée sur le port 8000.")
    except Exception as e:
        print(f"❌ ERREUR générale : {e}")

if __name__ == "__main__":
    # Vérifier l'installation de websockets
    try:
        asyncio.run(authenticate_and_get_token())
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
             # Gérer les erreurs de boucle asynchrone courantes
             print("Erreur de boucle asynchrone, réessayez.")
        else:
             raise e