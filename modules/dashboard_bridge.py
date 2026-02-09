import streamlit as st
import os
import time
import cv2
import subprocess
import json
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any

# 🚨 CORRECTION CRITIQUE : Importation de la classe parente
from modules.module import Module

logger = logging.getLogger('DashboardBridge')

# --- CHEMINS ABSOLUS CORRIGÉS (Définis globalement pour Streamlit) ---
# Ces variables DOIVENT être définies au niveau du script pour que Streamlit les trouve.
BASE_DIR = r"G:\neuro\Neuro-master\Neuro-master"

MEMORIES_DIR = os.path.join(BASE_DIR, "memories")
INPUT_DIR = os.path.join(MEMORIES_DIR, "inputs")
INPUT_JSON = os.path.join(MEMORIES_DIR, "dashboard_input.json")
HISTORY_JSON = os.path.join(MEMORIES_DIR, "chat_history.json")

# TA CONFIG TAPO
TAPO_URL = "rtsp://ambre:clio1234@192.168.1.193:554/stream1"

# Création dossiers (sécurité)
if not os.path.exists(MEMORIES_DIR): os.makedirs(MEMORIES_DIR)
if not os.path.exists(INPUT_DIR): os.makedirs(INPUT_DIR)


# --- FONCTIONS UTILITAIRES POUR STREAMLIT ---

def send_command(text: str) -> bool:
    """Ecrit l'ordre pour main.py (via le pont dashboard_bridge)"""
    # Ajout du rôle pour une distinction plus claire
    data = {"role": "user", "message": text, "timestamp": time.time()}
    try:
        with open(INPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        return True
    except Exception as e:
        # st.error ne fonctionne que dans Streamlit. Utiliser print/log ici pour la robustesse du module.
        print(f"Erreur écriture JSON : {e}")
        return False

def load_chat_secure() -> List[Dict[str, Any]]:
    """Lit l'historique de chat de manière sécurisée (tentatives multiples)."""
    if not os.path.exists(HISTORY_JSON):
        return []
        
    for _ in range(3):
        try:
            with open(HISTORY_JSON, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            time.sleep(0.05)
        except Exception:
            time.sleep(0.05)
            
    return []

def save_chat_secure(history: List[Dict[str, Any]]):
    """Sauvegarde l'historique de chat de manière sécurisée (tentatives multiples)."""
    for _ in range(3):
        try:
            with open(HISTORY_JSON, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"BRIDGE SAVE ERROR: Échec de l'écriture de l'historique : {e}")
            time.sleep(0.1)
    return False

def list_all_files(directory):
    file_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith((".py", ".json", ".txt", ".md")):
                file_list.append(os.path.join(root, file))
    return file_list


class DashboardBridge(Module): # Hérite de Module
    """
    Module pont qui gère la communication basée sur des fichiers entre l'application principale
    et l'interface Streamlit.
    """
    def __init__(self, signals, prompter):
        super().__init__(signals)
        # Supprime la référence à prompter pour forcer l'utilisation de signals
        # self.prompter = prompter
        
        # Créer l'historique vide s'il n'existe pas (utilise la fonction sécurisée)
        if not os.path.exists(HISTORY_JSON):
            try:
                save_chat_secure([])
            except: pass

    async def run(self):
        logger.info(f"🌉 Surveillance active sur : {INPUT_JSON}")
        while not self.signals.terminate:
            await asyncio.sleep(0.5)
            
            if os.path.isfile(INPUT_JSON):
                try:
                    # 1. Lire le message du Dashboard (Lecture sécurisée)
                    data = None
                    for _ in range(3):
                        try:
                            with open(INPUT_JSON, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            break
                        except json.JSONDecodeError:
                            await asyncio.sleep(0.1)
                        except Exception:
                            await asyncio.sleep(0.1)
                    
                    if data:
                        user_message = data.get("message", "")
                        
                        if user_message:
                            logger.info(f"📩 Message reçu : {user_message}")
                            
                            # 2. SAUVEGARDER TON MESSAGE TOUT DE SUITE
                            self.update_history("user", user_message)
                            
                            # 3. Envoyer au cerveau via SIGNAL (CORRECTION DÉFINITIVE)
                            # CORRECTION: Utilisation de self.signals.send_signal('user_input', (message, source))
                            # C'est la seule méthode publique générique de la classe Signals.
                            self.signals.send_signal('user_input', (user_message, "dashboard"))

                        # 4. Supprimer le fichier pour dire "Reçu !"
                        os.remove(INPUT_JSON)
                    
                except FileNotFoundError:
                    pass
                except Exception as e:
                    # L'erreur 'process_input' n'apparaîtra plus ici
                    logger.error(f"Erreur de pont (lecture/traitement) : {e}", exc_info=True)
                    # En cas d'erreur, on supprime pour ne pas bloquer la boucle
                    try: os.remove(INPUT_JSON)
                    except: pass

    def update_history(self, role: str, content: str):
        """Ajoute un message à l'historique visible dans le dashboard"""
        history = load_chat_secure() # Utilise la fonction de lecture sécurisée
        
        timestamp = time.strftime("%H:%M")
        # On ajoute le message
        history.append({"role": role, "content": content, "time": timestamp})
        
        # On garde seulement les 20 derniers échanges pour ne pas surcharger
        history = history[-20:]
        
        # 🚨 Utilise la fonction de sauvegarde sécurisée
        save_chat_secure(history)


# ----------------------------------------------------------------
# LOGIQUE STREAMLIT (LANCEMENT DU DASHBOARD)
# ----------------------------------------------------------------

if __name__ == '__main__':
    st.set_page_config(page_title="CLIO | Cockpit v6 (HARD LINK)", page_icon="🔗", layout="wide")
    
    # --- SIDEBAR DIAGNOSTIC (VÉRIFICATION VITALE) ---
    if st.sidebar.button("Initialiser / Vérifier"):
        st.rerun()

    with st.sidebar:
        st.header("🔧 DIAGNOSTIC LIEN")
        
        if os.path.exists(BASE_DIR):
            st.success(f"✅ Racine trouvée sur G:\...")
        else:
            st.error(f"❌ Racine INTROUVABLE : {BASE_DIR}")
            st.warning("Vérifie le chemin dans le code (ligne 15)")

        if os.path.exists(INPUT_JSON):
            st.warning("📨 Message en attente (Clio dort ?)")
        else:
            st.info("📭 Boîte vide (Clio a lu)")

        st.divider()
        
        st.subheader("TESTS RAPIDES VTS")
        c1, c2 = st.columns(2)
        if c1.button("😃 Joie"):
            if send_command("commande vts happy"): st.toast("Ordre VTS envoyé")
        if c2.button("😠 Colère"):
            if send_command("commande vts angry"): st.toast("Ordre VTS envoyé")
        
        st.subheader("TEST VOCAL")
        if st.button("🔊 Parler"):
            if send_command("Dis bonjour pour tester ta voix"): st.toast("Ordre Vocal envoyé")

        st.divider()
        if st.button("🔄 Actualiser"): st.rerun()

    # --- ONGLETS ---
    t1, t2, t3, t4 = st.tabs(["💬 TCHAT", "👁️ VISION", "🎮 JEUX", "📂 EXPLORATEUR"])

    # 1. TCHAT
    with t1:
        history = load_chat_secure()
        cont = st.container(height=400, border=True)
        with cont:
            if not history: st.info("Aucun historique trouvé dans 'memories/chat_history.json'")
            for msg in history:
                role = msg.get('role', 'user')
                av = "🧠" if role == "assistant" else "👤"
                with st.chat_message(role, avatar=av):
                    st.write(msg.get('content', ''))
                    if msg.get('time'):
                        st.caption(msg.get('time', ''))

        # Zone saisie
        if txt := st.chat_input("Ecrire à Clio..."):
            with cont:
                with st.chat_message("user", avatar="👤"): st.write(txt)
            
            if send_command(txt):
                st.toast("Envoyé au cerveau !", icon="🚀")
                
                history_len_before = len(history)
                with st.spinner("Clio réfléchit..."):
                    for i in range(20):
                        time.sleep(0.2)
                        new_hist = load_chat_secure()
                        if len(new_hist) > history_len_before:
                            st.rerun()
                            break
                    
                # Le warning est mis à jour pour refléter le changement
                st.warning("Pas de réponse immédiate. Vérifiez que **main.py tourne** et **écoute le signal 'user_input'**.")

    # 2. VISION
    with t2:
        st.subheader("Flux Vidéo")
        col1, col2 = st.columns([1, 3])
        with col1:
            src = st.radio("Source", ["Tapo (RTSP)", "Webcam (Index 0)"])
            
            if 'cam_on' not in st.session_state: st.session_state.cam_on = False
            btn_label = "🔴 Éteindre" if st.session_state.cam_on else "🟢 Allumer"
            
            if st.button(btn_label):
                st.session_state.cam_on = not st.session_state.cam_on
                st.rerun()
                
            if st.session_state.cam_on:
                st.caption(f"Source active : {src}")
        
        with col2:
            if st.session_state.get('cam_on', False):
                u = TAPO_URL if "Tapo" in src else 0
                
                cap = cv2.VideoCapture(u)
                spot = st.empty()
                
                if not cap.isOpened():
                    st.error("❌ Erreur de connexion à la Caméra/RTSP.")
                    st.session_state.cam_on = False
                else:
                    try:
                        while st.session_state.get('cam_on', False):
                            ret, frame = cap.read()
                            if not ret: break
                            
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            spot.image(frame, use_column_width=True)
                            
                            time.sleep(0.01)
                            
                    except Exception as e:
                        st.error(f"Erreur de flux vidéo : {e}")
                        st.session_state.cam_on = False
                        
                    finally:
                        cap.release()
                        if st.session_state.cam_on:
                            st.info("La caméra a été déconnectée. Cliquez sur Allumer pour réessayer.")
                    
            else:
                st.info("Caméra éteinte. Cliquez sur 'Allumer' pour démarrer le flux.")

    # 3. JEUX
    with t3:
        st.subheader("Lancement de Jeux et Logiciels")
        games = {
            "Pokemon Infinite Fusion": r"G:\PokemonFusion\InfiniteFusionFR-6.5.1\PIFLauncher1.1.2\PIFLauncher1.1.2\PIFLauncher1.1.0\GameFiles\InfiniteFusion\InfiniteFusion.exe",
            "Steam": r"G:\Steam\steam.exe",
            "Minecraft (Xbox)": r"C:\XboxGames\Minecraft Launcher\Content\Minecraft.exe"
        }
        cols = st.columns(3)
        i = 0
        for n, p in games.items():
            with cols[i%3]:
                st.markdown(f"**{n}**")
                if os.path.exists(p):
                    if st.button(f"Jouer 🚀", key=n):
                        try:
                            os.startfile(p)
                            st.toast(f"{n} lancé !", icon="🎮")
                        except Exception as e:
                            st.error(f"Erreur lancement : {e}")
                else:
                    st.caption("❌ Introuvable. Vérifiez le chemin.")
                    st.code(p)
            i+=1

    # 4. EXPLORATEUR (DEBUG)
    with t4:
        st.subheader("Explorateur de Fichiers du Projet")
        st.info(f"Exploration de : {BASE_DIR}")
        search = st.text_input("🔍 Rechercher fichier (ex: config)...")
        files = list_all_files(BASE_DIR)
        
        # Affichage des résultats filtrés
        result_container = st.container(height=400)
        with result_container:
            count = 0
            for f in files:
                if search.lower() in f.lower():
                    st.code(f)
                    count += 1
            if search and count == 0:
                st.warning("Aucun fichier correspondant trouvé.")
            elif not search:
                st.caption(f"Affichez {len(files)} fichiers. Entrez un terme de recherche pour filtrer.")