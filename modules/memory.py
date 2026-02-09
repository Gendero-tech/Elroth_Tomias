import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import logging

logger = logging.getLogger('MemoryModule')

# --- DÉFINITION DES CHEMINS D'ACCÈS DU PROJET ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# PROJECT_ROOT est supposé être le répertoire parent de 'modules'
PROJECT_ROOT = os.path.dirname(CURRENT_DIR) 

MEMORY_FOLDER = os.path.join(PROJECT_ROOT, "memories")
MEMORY_FILE = os.path.join(MEMORY_FOLDER, "clio_memory.json")
VECTOR_INDEX_FILE = os.path.join(MEMORY_FOLDER, "clio_user.index")
VECTOR_META_FILE = os.path.join(MEMORY_FOLDER, "clio_user.meta")
# --- FIN DE LA DÉFINITION DES CHEMINS D'ACCÈS ---

# Assurez-vous que ces modules existent dans votre structure :
from modules.module import Module
# L'importation relative fonctionne ici si memory.py est dans un sous-dossier
from .clio_vector_memory import ClioVectorMemory 

EVENTS_LOG_KEY = "events"
MAX_EVENTS_COUNT = 500 # Limite le journal d'événements pour éviter les fichiers JSON massifs

# --- FONCTIONS DE BASE (MOYENNE MÉMOIRE) ---

def prune_events_log(data: Dict[str, Any]):
    """Limiter la taille du journal d'événements pour des performances optimales."""
    events = data.get(EVENTS_LOG_KEY, [])
    if len(events) > MAX_EVENTS_COUNT:
        # Garde uniquement les N événements les plus récents
        data[EVENTS_LOG_KEY] = events[-MAX_EVENTS_COUNT:]
        logger.info(f"Journal d'événements nettoyé : {len(events) - MAX_EVENTS_COUNT} entrées supprimées.")

def load_memory() -> Dict[str, Any]:
    """Charge la mémoire persistée du fichier JSON."""
    if not os.path.exists(MEMORY_FOLDER):
        os.makedirs(MEMORY_FOLDER)

    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if EVENTS_LOG_KEY not in data: data[EVENTS_LOG_KEY] = []
                # Exécute un nettoyage après le chargement pour vérifier si trop gros
                prune_events_log(data) 
                return data
        except json.JSONDecodeError:
            logger.error("Fichier clio_memory.json corrompu. Réinitialisation.")
        except Exception as e:
            logger.error(f"Échec du chargement du fichier : {e}")
            
    return {EVENTS_LOG_KEY: []}

def save_memory(data: Dict[str, Any]):
    """Sauvegarde la mémoire persistée dans le fichier JSON avec gestion d'erreur."""
    try:
        # Nettoyage avant la sauvegarde pour s'assurer que seuls les événements récents sont écrits
        prune_events_log(data) 
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.critical(f"ALERTE GRAVE MEMORY: Échec de la sauvegarde du fichier JSON: {e}")

# --- CLASSE MODULE ET API (INTÉGRATION) ---

class Memory(Module):
    # 🟢 LIGNE CORRIGÉE : Ajout de project_root à la signature (pour ne pas lever d'erreur)
    def __init__(self, signals, enabled: bool = True, project_root: Optional[Union[str, os.PathLike]] = None):
        super().__init__(signals, enabled)
        
        # Le project_root passé n'est pas utilisé directement pour redéfinir les chemins
        # globaux ci-dessus, mais il est maintenant accepté.
        
        self.persistent_memory = load_memory() 
        self.session_memory: Dict[str, Any] = {
            "last_topic": None, 
            "last_emotion": None, 
            "last_segment_text": None
        }
        
        # Initialisation de la mémoire vectorielle (chemins absolus corrigés)
        self.vector_memory = ClioVectorMemory(
            index_path=VECTOR_INDEX_FILE, 
            meta_path=VECTOR_META_FILE
        )
        self.API = self.API(self)

    def update_persistent_memory(self, key: str, value: Any):
        """Met à jour une clé spécifique dans la mémoire persistée (en RAM)."""
        self.persistent_memory[key] = value

    def log_event(self, event_type: str, description: Dict[str, Any]):
        """Enregistre un événement horodaté dans la mémoire (en RAM)."""
        timestamp = datetime.now().isoformat()
        if not isinstance(description, dict): description = {"message": str(description)} 
            
        self.persistent_memory[EVENTS_LOG_KEY].append({
            "type": event_type, "description": description, "timestamp": timestamp
        })
    
    def shutdown(self):
        """Sauvegarde la mémoire persistante en RAM sur le disque."""
        logger.info("Sauvegarde de la mémoire persistante sur disque...")
        
        # Séquence de sauvegarde : Vectoriel, puis JSON
        if hasattr(self.vector_memory, 'shutdown_memory'):
            self.vector_memory.shutdown_memory()
            
        save_memory(self.persistent_memory)

    class API:
        def __init__(self, outer: 'Memory'): self.outer = outer
            
        def create_memory(self, data: Dict[str, Any]):
            segment_text = data.get('text', 'segment_vide')
            
            self.outer.log_event("dashboard_input", data)
            self.outer.update_persistent_memory("last_dashboard_segment", segment_text)
            
            if self.outer.vector_memory and self.outer.vector_memory.model:
                metadata_for_vector = {
                    "text": segment_text, "source": data.get('source', 'dashboard'), "emotion": data.get('emotion', 'neutral'),
                    "status": data.get('status', 'accepted')
                }
                self.outer.vector_memory.add_segment(segment_text, metadata_for_vector)
                logger.info(f"Segment ajouté à la mémoire vectorielle: '{segment_text[:30]}...'")
            elif self.outer.vector_memory:
                 logger.warning("[ALERTE MEMORY] Segment non ajouté. Le modèle d'encodage vectoriel n'est pas actif.")
            else:
                 logger.warning("[ALERTE MEMORY] Segment non ajouté. La mémoire vectorielle est indisponible.")

        def search_similar(self, query: str, top_k: int = 5) -> List[Dict]:
            # Utilise désormais le logging au lieu du print
            if not isinstance(query, str) or not query.strip():
                logger.warning("Tentative de recherche vectorielle avec une requête vide ou non-texte.")
                return []
                
            if self.outer.vector_memory and self.outer.vector_memory.model:
                # 🚀 AMÉLIORATION : Récupération réelle de la mémoire vectorielle
                return self.outer.vector_memory.search_similar(query, top_k)
            
            return [{"text": "Erreur: La mémoire vectorielle est désactivée. Recherche impossible.", "source": "system"}]

        def get_memories(self, query_data: Optional[Dict[str, Any]] = None) -> List[Dict]:
            # La fonction est simplifiée pour ne retourner que les résultats de recherche.
            query = query_data.get('query') if query_data and isinstance(query_data, dict) else None
            if query and isinstance(query, str) and query.strip():
                logger.debug(f"Requête de mémoire vectorielle reçue: {query}")
                return self.search_similar(query)
            # Retourne un message vide ou les derniers logs si aucune requête n'est fournie
            return self.get_memories_log()

        def get_session_context(self) -> Dict[str, Any]:
            """Fournit le contexte de session complet."""
            return self.outer.session_memory
            
        def get_memories_log(self) -> List[Dict]:
            """Récupère le journal d'événements récent."""
            return self.outer.persistent_memory.get(EVENTS_LOG_KEY, [])

        # --- NOUVELLE MÉTHODE CRITIQUE : SYNTHÈSE DU CONTEXTE POUR LE LLM ---
        def get_synthesized_context(self, user_query: str) -> str:
            """
            Combine les données de session (émotion) et les faits pertinents (vectoriel) 
            pour créer un briefing ciblé pour le LLM.
            """
            context_parts = []
            
            # 1. Injection du Contexte de Session Volatil (Émotion/Sujet)
            session = self.get_session_context()
            context_parts.append("--- CONTEXTE DE SESSION ---")
            if session.get("last_emotion"):
                context_parts.append(f"Émotion utilisateur récente: {session['last_emotion']}")
            if session.get("last_topic"):
                context_parts.append(f"Sujet récent: {session['last_topic']}")

            # 2. Injection des Faits Pertinents (RAG Vectoriel)
            # Recherche top_k=2 faits les plus pertinents pour la requête actuelle
            relevant_facts = self.search_similar(user_query, top_k=2)
            if relevant_facts:
                context_parts.append("\n--- FAITS PERTINENTS (MÉMOIRE LONGUE) ---")
                for i, fact in enumerate(relevant_facts):
                    # S'assure de fournir la source ou le texte directement
                    text = fact.get("text", fact)
                    # Ajout d'une limite de caractères pour la lisibilité
                    context_parts.append(f"Fact {i+1} (Source: {fact.get('source', 'Inconnue')}): {text[:100]}...")
            
            # 3. Injection des Événements Récents (Journal, 5 derniers max)
            recent_logs = self.get_memories_log()[-5:]
            if recent_logs:
                 context_parts.append("\n--- DERNIERS ÉVÉNEMENTS ---")
                 for log in recent_logs:
                     # Formate le log pour qu'il soit compact
                     desc = log.get("description", {}).get("message", log.get("description", ""))
                     context_parts.append(f"[{log.get('type')}] : {desc[:50]}...")
            
            # Joindre et retourner le briefing
            return "\n".join(context_parts)
            
        def clear_short_term(self):
             self.outer.session_memory = { 
                 "last_topic": None, "last_emotion": None, "last_segment_text": None 
             }
             logger.info("[Memory] Mémoire de session (volatile) effacée.")