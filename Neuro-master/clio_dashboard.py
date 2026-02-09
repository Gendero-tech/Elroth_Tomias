import streamlit as st
import requests
import threading
import time
import socketio
import subprocess
import sys

# --- Imports des modules "locaux" (qui tournent sur le dashboard) ---
try:
    from modules.shortcut_montage import launch_shortcut_montage
    from modules.youtube_remontage import download_channel_videos, filter_bad_segments, generate_reaction_script
except ImportError as e:
    st.sidebar.error(f"Erreur d'importation de module local: {e}")

# --- ARCHITECTURE CLIENT SOCKET.IO PERSISTANT ---

# 1. Initialiser le client Socket.IO dans la session
if 'sio_client' not in st.session_state:
    st.session_state.sio_client = socketio.Client()
sio = st.session_state.sio_client

# 2. Gérer l'état de la connexion et les résultats de recherche
if 'connected' not in st.session_state:
    st.session_state.connected = False
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'compare_results' not in st.session_state:
    st.session_state.compare_results = []
if 'clio_logs' not in st.session_state:
    st.session_state.clio_logs = ["Attente de logs de Clio..."]
if 'llm_latency' not in st.session_state:
    st.session_state.llm_latency = 0.0
if 'social_output' not in st.session_state:
    st.session_state.social_output = ""
if 'context_mode' not in st.session_state:
    st.session_state.context_mode = "stream"

# Variable pour contrôler le thread de connexion
if 'sio_thread' not in st.session_state:
    st.session_state.sio_thread = None

# 3. Définir les gestionnaires d'événements (ce que Clio nous renvoie)
@sio.event
def dashboard_search_results(data):
    st.session_state.search_results = data
    st.session_state.rerun_flag = True

@sio.event
def dashboard_compare_results(data):
    st.session_state.compare_results = data
    st.session_state.rerun_flag = True

@sio.event
def social_post_results(data):
    st.session_state.social_output = data.get('content', 'Erreur de génération.')
    st.session_state.rerun_flag = True

@sio.event
def clio_log_message(data):
    st.session_state.clio_logs.append(f"[{time.strftime('%H:%M:%S')}] {data['message']}")
    if len(st.session_state.clio_logs) > 50:
        st.session_state.clio_logs = st.session_state.clio_logs[-50:]
    st.session_state.rerun_flag = True

@sio.event
def clio_latency_update(data):
    st.session_state.llm_latency = data.get('latency', 0.0)
    st.session_state.rerun_flag = True

@sio.event
def connect():
    print("Dashboard connecté à Clio (main.py) !")
    st.session_state.connected = True
    st.session_state.rerun_flag = True

@sio.event
def disconnect():
    print("Dashboard déconnecté de Clio (main.py).")
    st.session_state.connected = False
    st.session_state.rerun_flag = True


# 4. Fonction de connexion exécutée dans un thread de fond
def connect_sio_in_thread():
    """Tente de connecter et de maintenir la connexion SocketIO."""
    while True:
        if not sio.connected:
            try:
                print(f"[{time.strftime('%H:%M:%S')}] Tentative de connexion SocketIO...")
                sio.connect('http://127.0.0.1:8081', wait_timeout=3) # CORRECTION APPLIQUÉE ICI
                sio.wait()
            except socketio.exceptions.ConnectionError:
                time.sleep(3)
            except Exception as e:
                print(f"Erreur inattendue dans le thread SIO: {e}")
                time.sleep(5)
        else:
            time.sleep(1)

# 5. Lancement du thread de connexion au démarrage de l'application
if st.session_state.sio_thread is None:
    st.session_state.sio_thread = threading.Thread(target=connect_sio_in_thread, daemon=True)
    st.session_state.sio_thread.start()


# --- LOGIQUE DE REDEMARRAGE STREAMLIT (RERUN) ---
if 'rerun_flag' not in st.session_state:
    st.session_state.rerun_flag = False

if st.session_state.rerun_flag:
    st.session_state.rerun_flag = False
    st.rerun()
# ------------------------------------------------

st.set_page_config(page_title="CLIO Cockpit", layout="wide")
st.title("CLIO — Cockpit de Contrôle 💙")

# --- CORRECTION MAJEURE: CONTRÔLE DE CONNEXION ---
if not st.session_state.connected:
    st.error("Connexion à Clio échouée. Veuillez lancer main.py (Clio) AVANT de lancer ce dashboard.")
    if st.button("Réessayer la connexion"):
        # Force juste un rerun, le thread de fond gère la connexion
        st.rerun()

    # NE PAS UTILISER st.stop() ICI.
    # Cela tuait la page avant que le thread de connexion puisse la rafraîchir.
    # La page attendra maintenant que 'connected' devienne True.

else:
    # --- TOUTE L'INTERFACE EST MAINTENANT DANS CE BLOC 'ELSE' ---
    st.success("Connecté au Cerveau de Clio (main.py)")

    # --- MISE EN PAGE OPTIMALE : SIDEBAR pour le monitoring ---
    with st.sidebar:
        st.header("⚙️ Maintenance & Monitoring")

        st.markdown(f"**Latence LLM :** {st.session_state.llm_latency:.2f} s")

        st.markdown("---")
        st.subheader("Contrôle du LLM")

        temperature = st.slider("Température (Créativité)", 0.0, 1.0, 0.7, 0.05,
                                 key='llm_temp', help="Basse = factuel, Haute = créatif.")
        top_p = st.slider("Top-P (Diversité)", 0.0, 1.0, 0.9, 0.05,
                                  key='llm_top_p', help="Contrôle le vocabulaire sélectionné.")
        verbosity = st.selectbox("Verbiosité", ["Standard", "Concise", "Verbose"],
                                 key='llm_verb', help="Ajuste la longueur des réponses.")

        if st.button("💾 Appliquer Hyperparamètres"):
            if sio.connected:
                sio.emit('dashboard_update_llm_config', {
                    'temperature': temperature,
                    'top_p': top_p,
                    'verbosity': verbosity
                })
                st.success("Configuration LLM envoyée.")
            else:
                st.error("Impossible d'appliquer : Connexion perdue.")

        st.markdown("---")
        st.subheader("Système & Nettoyage")

        if st.button("🧹 Nettoyer Mémoire Volatile"):
            if sio.connected:
                sio.emit('dashboard_clear_session_memory')
                st.warning("Mémoire de session réinitialisée. Clio a 'oublié' le dernier contexte.")
            else:
                st.error("Impossible de nettoyer : Connexion perdue.")

        if st.button("🔄 Redémarrer Clio (Soft)"):
            if sio.connected:
                sio.emit('dashboard_soft_restart')
                st.info("Signal de redémarrage envoyé. Le Dashboard va se déconnecter puis tenter de se reconnecter.")
                sio.disconnect()
                time.sleep(1)
                st.rerun() # Utilise st.rerun()
            else:
                st.error("Impossible de redémarrer : Connexion perdue.")

        st.markdown("---")
        st.subheader("Journal (Clio Console)")
        log_container = st.container(height=300)
        with log_container:
            st.code('\n'.join(st.session_state.clio_logs[-10:]), language='text')
    # --- FIN SIDEBAR ---

    # --- MAIN CONTENT LAYOUT ---
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📘 Segment à analyser")
        segment = st.text_area("Texte du segment")
        source = st.text_input("Source (streamer, vidéo, etc.)")
        emotion = st.selectbox("Émotion détectée", ["gentle", "mocking", "happy", "sad", "angry", "neutral"])
        status = st.selectbox("Statut", ["accepted", "rejected", "paradox"])
        reason = st.text_input("Motif du rejet (si applicable)")
        paradox_type = st.selectbox("Type de paradoxe", ["émotionnel", "narratif", "cognitif", "temporel", "identitaire", "social", "métaphysique"])

        if st.button("🧠 Expliquer ce segment"):
            payload = {
                "type": status,
                "reason": reason,
                "terms": ["attardé"] if reason == "validisme" else [],
                "paradox_type": paradox_type,
                "context": segment
            }
            try:
                response = requests.post("http://localhost:8081/api/explain", json=payload)
                if response.status_code == 200:
                    st.markdown(response.json()["explanation"])
                else:
                    st.error(f"Erreur de l'API Clio (Code {response.status_code}): {response.json().get('message', 'Erreur inconnue')}")
            except requests.ConnectionError:
                st.error("Connexion HTTP à Clio (8081) refusée. Assurez-vous que main.py est lancé.")
            except Exception as e:
                st.error(f"Erreur inconnue: {e}")

        if st.button("✅ Valider et stocker"):
            metadata = {
                "text": segment,
                "source": source,
                "emotion": emotion,
                "status": status
            }
            if sio.connected:
                sio.emit('dashboard_add_memory', metadata)
                st.success("Ordre 'Stocker segment' envoyé à Clio 💙")
            else:
                st.error("Échec de l'envoi : Connexion à Clio perdue.")

        st.subheader("🔍 Recherche vectorielle")
        query = st.text_area("Phrase de recherche")
        if st.button("🔎 Rechercher"):
            st.session_state.search_results = []
            if sio.connected:
                sio.emit('dashboard_search_memory', query)
                st.info("Recherche envoyée à Clio... (les résultats s'afficheront ci-dessous)")
            else:
                st.error("Échec de l'envoi : Connexion à Clio perdue.")

        for res in st.session_state.search_results:
            st.markdown(f"- **{res.get('text')}** ({res.get('emotion')}, {res.get('source')})")

        st.markdown("---")
        st.subheader("🌐 Génération de Contenu Social")
        st.caption("Clio génère un message percutant basé sur votre activité ou un sujet.")

        social_topic = st.text_input("Sujet du Post / Résumé de Session", key='social_topic_input')
        social_style = st.selectbox("Style du Post", ["Engageant/Hype", "Sérieux/Analyse", "Doux/Réconfortant", "Humour/Mème"], key='social_style_select')

        if st.button("✍️ Générer Post (via Clio)"):
            if sio.connected:
                st.session_state.social_output = "Génération en cours..."
                st.rerun() # Utilise st.rerun()

                sio.emit('dashboard_generate_social_post', {
                    'topic': social_topic,
                    'style': social_style,
                    'mode': st.session_state.context_mode
                })
                st.info("Requête envoyée à Clio. Attente de la réponse...")
            else:
                st.error("Connexion à Clio perdue. Impossible de générer le contenu.")

        if 'social_output' in st.session_state and st.session_state.social_output != "":
            st.markdown("**Contenu généré :**")
            st.code(st.session_state.social_output)

    with col2:
        st.subheader("💙 CLIO apprend de toi (Segment utilisateur)")
        user_segment = st.text_area("Segment que tu veux transmettre à CLIO")
        user_emotion = st.selectbox("Émotion associée (pour apprentissage)", ["gentle", "mocking", "happy", "sad", "angry", "neutral"])
        user_context = st.text_input("Contexte (jeu, stream, moment vécu…)")

        if st.button("📘 Apprendre ce segment"):
            payload = {
                "text": user_segment,
                "emotion": user_emotion,
                "context": user_context
            }
            if sio.connected:
                sio.emit('dashboard_add_user_segment', payload)
                st.success("Ordre 'Apprendre segment' envoyé à Clio 💙")
            else:
                st.error("Échec de l'envoi : Connexion à Clio perdue.")


        st.markdown("---")
        st.subheader("🔗 Ajouter une URL (Auto-Analyse)")
        st.caption("Collez une URL pour que Clio l'analyse et l'ajoute à sa base de connaissances.")

        url_to_learn = st.text_input("URL à analyser", key="url_learn_input", placeholder="https://www.youtube.com/watch?v=...")

        if st.button("🚀 Lancer l'analyse (via Clio)"):
            if url_to_learn and "http" in url_to_learn and sio.connected:
                sio.emit('dashboard_add_url_to_knowledge', {
                    'url': url_to_learn,
                    'domain': 'user_added_link'
                })
                st.success(f"Demande d'analyse envoyée à Clio pour : {url_to_learn}")
                st.info("Clio traitera cela en arrière-plan. Cela peut prendre quelques minutes.")
            elif not url_to_learn or "http" not in url_to_learn:
                st.warning("Veuillez coller une URL valide avant de lancer l'analyse.")
            else:
                st.error("Échec de l'envoi : Connexion à Clio perdue.")


        st.markdown("---")
        st.subheader("📊 Comparaison avec les meilleurs VTubers")
        comparison_query = st.text_input("Phrase ou style à comparer")
        if st.button("🔍 Comparer"):
            st.session_state.compare_results = []
            if sio.connected:
                sio.emit('dashboard_compare_streamers', comparison_query)
                st.info("Comparaison envoyée à Clio...")
            else:
                st.error("Échec de l'envoi : Connexion à Clio perdue.")

        for res in st.session_state.compare_results:
            st.markdown(f"- **{res.get('text')}** ({res.get('emotion')}, {res.get('source')})")

    st.markdown("---")
    st.subheader("📺 CLIO parle et réagit")

    col3, col4, col5 = st.columns(3)

    with col3:
        st.caption("🔊 Parole directe")
        spoken_text = st.text_area("Texte à prononcer", key='spoken_text_area')
        spoken_style = st.selectbox("Style vocal", ["chat", "cheerful", "sad", "angry", "excited", "calm"], key='spoken_style_select')

        if st.button("🗣️ Faire parler CLIO"):
            if sio.connected:
                sio.emit('dashboard_speak', {'text': spoken_text, 'style': spoken_style})
                st.success("Ordre 'Parler' envoyé à Clio 💙")
            else:
                st.error("Échec de l'envoi : Connexion à Clio perdue.")

    with col4:
        st.caption("🎛️ Réactions rapides")
        if st.button("💙 Bonjour Ambre"):
            if sio.connected:
                sio.emit('dashboard_speak', {'text': "Bonjour Ambre 💙", 'style': 'chat'})
            else:
                st.error("Échec de l'envoi : Connexion à Clio perdue.")

        if st.button("😱 Fail détecté"):
            if sio.connected:
                sio.emit('dashboard_speak', {'text': "Oh non... tu viens de rater ton saut 💙", 'style': 'sad'})
            else:
                st.error("Échec de l'envoi : Connexion à Clio perdue.")

        if st.button("🎉 Bravo !"):
            if sio.connected:
                sio.emit('dashboard_speak', {'text': "Bravo ! Tu gères 💙", 'style': 'cheerful'})
            else:
                st.error("Échec de l'envoi : Connexion à Clio perdue.")

        if st.button("🫂 Présence douce"):
            if sio.connected:
                sio.emit('dashboard_speak', {'text': "Je suis là, toujours 💙", 'style': 'calm'})
            else:
                st.error("Échec de l'envoi : Connexion à Clio perdue.")

    with col5:
        st.caption("🎬 Montage & YouTube")
        if st.button("📺 Télécharger depuis Elroth_Tomias"):
            try:
                download_channel_videos()
                st.success("Vidéos téléchargées dans le dossier 'downloads/' 💙")
            except NameError:
                st.error("La fonction 'download_channel_videos' n'a pas pu être importée.")

        st.caption("🎭 Réaction Transcript")
        raw_transcript = st.text_area("Transcript complet (pour réaction)", key='raw_transcript_area')
        if st.button("💬 Générer réaction CLIO"):
            try:
                bad_parts = filter_bad_segments(raw_transcript)
                reaction = generate_reaction_script(bad_parts)
                st.markdown(reaction)
            except NameError:
                 st.error("Les fonctions 'filter_bad_segments' ou 'generate_reaction_script' n'ont pas pu être importées.")

        st.caption("📺 Réagir à ce que tu regardes")
        live_transcript = st.text_area("Dialogue en cours", key='live_transcript_area')
        reaction_style = st.selectbox("Style de réaction", ["gentle", "mocking", "happy", "sad", "angry", "neutral"], key='reaction_style_select')

        if st.button("🎭 Réagir à ce contenu"):
            if sio.connected:
                sio.emit('dashboard_speak', {'text': f"CLIO ({reaction_style}) : {live_transcript}", 'style': reaction_style})
                st.success("Réaction vocale envoyée à Clio 💙")
            else:
                st.error("Échec de l'envoi : Connexion à Clio perdue.")