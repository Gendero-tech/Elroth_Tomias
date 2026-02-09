import os
import pickle
import faiss
import numpy as np
import requests  # On utilise requests pour parler à Ollama
from typing import List, Dict, Union, Optional
import logging

logger = logging.getLogger('ClioVectorMemory')

# --- CONFIGURATION OPTIMISÉE ---
# mxbai-embed-large a une dimension de 1024 (contre 384 pour MiniLM)
MODEL_DIMENSION = 1024  
NLIST = 100 
M = 8       
MIN_TRAINING_SAMPLES = 4 * NLIST 

class ClioVectorMemory:
    def __init__(self, index_path: str = "clio_user.index", meta_path: str = "clio_user.meta", read_only: bool = False):
        self.read_only = read_only
        self.d = MODEL_DIMENSION
        self.ollama_url = "http://localhost:11434/api/embeddings"
        self.model_name = "mxbai-embed-large" # Modèle local via Ollama
        
        # Gestion des chemins
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir) 
        memory_dir = os.path.join(project_root, "memories")
        if not os.path.exists(memory_dir): os.makedirs(memory_dir)

        self.index_path = os.path.join(memory_dir, index_path) 
        self.meta_path = os.path.join(memory_dir, meta_path)
        
        self.index = None
        self.metadata: List[Dict] = []
        
        # Chargement initial
        self.load_memory()
        if self.index is None:
            self._create_new_index()
        
        logger.info(f"🧠 Mémoire vectorielle via Ollama ({self.model_name}) prête.")

    def _create_new_index(self):
        quantizer = faiss.IndexFlatL2(self.d) 
        # IVFPQ est excellent pour gérer tes 20k+ vecteurs avec rapidité
        self.index = faiss.IndexIVFPQ(quantizer, self.d, NLIST, M, 8)
        logger.info("🆕 Nouvel index IVFPQ (1024-dim) initialisé.")

    def _encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Envoie les textes à Ollama pour obtenir les vecteurs"""
        if isinstance(texts, str): texts = [texts]
        embeddings = []
        
        for text in texts:
            try:
                response = requests.post(
                    self.ollama_url,
                    json={"model": self.model_name, "prompt": text},
                    timeout=10
                )
                response.raise_for_status()
                embeddings.append(response.json()["embedding"])
            except Exception as e:
                logger.error(f"❌ Erreur Ollama Embedding: {e}")
                # Vecteur nul en cas d'erreur pour ne pas crash
                embeddings.append(np.zeros(self.d))
        
        return np.array(embeddings).astype(np.float32)

    def add_segment(self, metadata: Dict):
        if self.read_only: return
        text = metadata.get("text", "")
        if "category" not in metadata:
            metadata["category"] = "GENERAL_MEMORY"

        vector = self._encode(text)
        self._add_vectors(vector, [metadata], save=True)

    def _add_vectors(self, vectors: np.ndarray, metadatas: List[Dict], save: bool = False):
        if self.index is None: return

        if not self.index.is_trained:
            # FAISS a besoin d'un petit échantillon pour apprendre à classer les vecteurs
            if vectors.shape[0] < MIN_TRAINING_SAMPLES:
                logger.warning("⚠️ Entraînement sur échantillon réduit (IVFPQ).")
            self.index.train(vectors)
        
        self.index.add(vectors)
        self.metadata.extend(metadatas)
        if save: self.save_memory()

    def search_similar(self, query: str, top_k: int = 5, category_filter: Optional[str] = None) -> List[Dict]:
        if self.index is None or self.index.ntotal == 0: return []
        
        self.index.nprobe = 20 
        vector = self._encode(query)
        D, I = self.index.search(vector, top_k * 2)
        
        results = []
        for idx in I[0]:
            if 0 <= idx < len(self.metadata):
                meta = self.metadata[idx]
                if category_filter and meta.get("category") != category_filter:
                    continue
                results.append(meta)
                if len(results) >= top_k: break
        return results

    def save_memory(self):
        if self.read_only or self.index is None: return
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.metadata, f)
        logger.info(f"💾 Mémoire sauvegardée ({self.index.ntotal} vecteurs).")

    def load_memory(self):
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.meta_path, "rb") as f:
                    self.metadata = pickle.load(f)
                
                # Vérification de la dimension (si tu changes de modèle, l'ancien index crash)
                if self.index.d != self.d:
                    logger.warning("⚠️ Dimension d'index incompatible. Recréation de la mémoire...")
                    self.index = None
                else:
                    logger.info(f"📜 Mémoire chargée : {self.index.ntotal} vecteurs.")
            except Exception as e:
                logger.error(f"❌ Erreur chargement mémoire : {e}")

    class API:
        def __init__(self, outer: 'ClioVectorMemory'): self.outer = outer
        def create_memory(self, metadata: Dict): self.outer.add_segment(metadata)
        def search(self, query: str, limit: int = 5, category: str = None):
            return self.outer.search_similar(query, limit, category)