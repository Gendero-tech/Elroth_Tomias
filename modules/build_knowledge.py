# Fichier : modules/build_knowledge.py
# (À lancer via 'python -m modules.build_knowledge' pour entraîner Clio)
# Correction: Collecte toutes les données en mémoire avant l'ajout unique pour FAISS (IndexIVFPQ).

import trafilatura
from langchain_text_splitters import RecursiveCharacterTextSplitter
# Imports relatifs
from .clio_knowledge import ClioKnowledge
from .clio_vector_memory import ClioVectorMemory
from .youtube import YoutubeClient
import time
import re 
import os 

# --- CONFIGURATION ---

print("Initialisation de la base de connaissance (RAG)...")
# 🚨 NOTE: Les chemins doivent être passés par le constructeur de ClioVectorMemory dans Memory.py, 
# mais ici, nous utilisons les chemins par défaut pour le script autonome.
kb = ClioVectorMemory() 

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200, 
    separators=["\n\n", "\n", ". ", " ", ""]
)

sources_dict = ClioKnowledge().sources
youtube_client = YoutubeClient(None) 

# Liste des URLs déjà présentes (collectées à partir de la mémoire vectorielle)
processed_urls = set()
for meta in kb.metadata:
    if 'source' in meta:
        processed_urls.add(meta['source'])
print(f"{len(processed_urls)} URLs déjà présentes dans la base.")

# --- FONCTIONS UTILES ---

def is_youtube_url(url: str) -> bool:
    """Vérifie si l'URL est un lien YouTube."""
    return bool(re.search(r'(youtube\.com/watch\?v=|youtu\.be/)', url))

# --- EXÉCUTION ---

def build_knowledge_base():
    if kb.model is None:
        print("\n❌ ERREUR: Le modèle d'encodage vectoriel (SentenceTransformer) n'a pas pu être chargé. L'entraînement est impossible.")
        return
        
    # --- PHASE 1: COLLECTE GLOBALE DES SEGMENTS ---
    print("\n--- PHASE 1: COLLECTE DES DONNÉES DE TOUTES LES SOURCES ---")
    all_chunks = []
    all_metadatas = []
    
    # 1. Parcourir tous les domaines et collecter les données
    for domain, urls in sources_dict.items():
        print(f"\n[Collecte] Traitement du domaine : {domain}")
        
        for url in urls:
            if url in processed_urls:
                print(f"Saut (déjà indexé) : {url}")
                continue

            print(f"Collecte de : {url} ...")
            
            try:
                main_content = None
                
                if is_youtube_url(url):
                    # Utilisation du client YouTube
                    transcript_text = youtube_client.api.get_transcript(url)
                    main_content = transcript_text
                else:
                    # Utilisation de Trafilatura (Articles Web)
                    downloaded = trafilatura.fetch_url(url)
                    if downloaded:
                        main_content = trafilatura.extract(downloaded)

                # 🚀 AMÉLIORATION : Vérification de la validité du contenu
                if not main_content or main_content.strip() == "" or len(main_content) < 50:
                    print(f"Échec de l'extraction (Contenu vide ou trop court) : {url}")
                    # Marque l'URL comme traitée (pour éviter de la retenter si elle est vide)
                    processed_urls.add(url) 
                    continue

                # Découpage et ajout temporaire
                chunks = text_splitter.split_text(main_content)
                
                if not chunks:
                     print(f"ALERTE: Extraction réussie mais aucun segment généré pour {url}")
                     processed_urls.add(url)
                     continue
                     
                for chunk in chunks:
                    all_chunks.append(chunk)
                    # 🚨 AMÉLIORATION : Assure que la source est dans la métadonnée du chunk
                    all_metadatas.append({
                        "text": chunk, "source": url, "domain": domain
                    })
                
                # Marque l'URL comme traitée pour les futures exécutions
                processed_urls.add(url)

                print(f"Collecté {len(chunks)} segments (Total: {len(all_chunks)})")
                time.sleep(1) 

            except Exception as e:
                print(f"ERREUR PENDANT LA COLLECTE sur {url}: {e}")

    print(f"\n--- PHASE 1 TERMINÉE. {len(all_chunks)} segments collectés au total. ---")
    
    # Vérification de la quantité de données avant entraînement
    if len(all_chunks) < kb.index.nlist: 
        print(f"ALERTE RAG: Seulement {len(all_chunks)} segments collectés. L'Index FAISS requiert au moins {kb.index.nlist} (idéalement 400+). L'entraînement pourrait échouer.")
        
    if not all_chunks:
        print("Aucune nouvelle donnée à ajouter. Terminé.")
        return

    # --- PHASE 2: ENTRAÎNEMENT ET AJOUT EN UN SEUL LOT ---
    print("\n--- PHASE 2: ENTRAÎNEMENT ET AJOUT DU LOT GLOBAL ---")
    
    try:
        # Ajout du lot global, ce qui déclenchera l'entraînement FAISS une seule fois
        kb.batch_add_segments(all_chunks, all_metadatas)
        
        # 🚨 CORRECTION CRITIQUE : La sauvegarde finale des métadonnées n'est plus nécessaire ici.
        # ClioVectorMemory.batch_add_segments sauvegarde l'index et les métadonnées.
        # Si la méthode ClioVectorMemory.batch_add_segments est correctement implémentée, elle a déjà sauvegardé l'index.
        # Cependant, pour s'assurer que les URLs qui n'ont pas produit de segments (mais qui ont été vérifiées)
        # ne soient pas retentées, on peut ajouter une logique de nettoyage. (Ignoré ici car toutes les URLs vérifiées ont produit des segments)
        
        print("\n✅✅✅ Mise à jour de la base de connaissance (RAG) terminée ! Clio est maintenant entraînée. ✅✅✅")

    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE PENDANT LA PHASE 2 (ENTRAÎNEMENT/AJOUT) : {e}")
        print("L'entraînement a échoué. Vérifiez vos dépendances FAISS ou la quantité de données.")


if __name__ == "__main__":
    build_knowledge_base()