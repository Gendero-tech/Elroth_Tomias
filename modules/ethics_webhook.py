from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class ClioVectorMemory:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.IndexFlatL2(384)
        self.metadata = []

    def add_segment(self, text, metadata):
        vector = self.model.encode([text])[0]
        self.index.add(np.array([vector]))
        self.metadata.append(metadata)

    def search_similar(self, query, top_k=5):
        vector = self.model.encode([query])[0]
        D, I = self.index.search(np.array([vector]), top_k)
        return [self.metadata[i] for i in I[0]]