import os
import gzip
import shutil
import time
import asyncio
import logging
from modules.module import Module
from typing import List, Union

log = logging.getLogger('Maintenance')

# --- CONFIGURATION ---
LOG_DIRS: List[str] = ['.', 'logs/', 'memories/']
MAX_LOG_AGE_DAYS: int = 7 
MAX_GZ_AGE_DAYS: int = 365 

class Maintenance(Module):
    """
    Module responsable du nettoyage des fichiers et de l'optimisation
    de la mémoire vectorielle (FAISS).
    """
    def __init__(self, signals: any, enabled: bool = True, modules: dict = None):
        super().__init__(signals, enabled)
        self.modules = modules or {}
        
    def _get_age_days(self, filepath: str, now: float) -> Union[float, None]:
        try:
            return (now - os.path.getmtime(filepath)) / (60 * 60 * 24)
        except OSError:
            return None

    def optimize_vector_memory(self):
        """
        Analyse la mémoire vectorielle pour fusionner les souvenirs redondants.
        """
        memory = self.modules.get('memory')
        if not memory or not hasattr(memory, 'index'):
            log.info("MAINTENANCE: Mémoire vectorielle non détectée ou inactive.")
            return

        total_vectors = memory.index.ntotal
        if total_vectors < 1000:
            log.info(f"MAINTENANCE: Mémoire ({total_vectors}) trop petite pour optimisation.")
            return

        log.info(f"🧠 MAINTENANCE: Défragmentation de la mémoire ({total_vectors} vecteurs)...")
        # Ici, on pourrait ajouter une logique de déduplication par seuil de distance L2
        # Pour l'instant, on force une sauvegarde propre pour réorganiser l'index IVFPQ
        memory.save_memory()

    def compress_old_logs(self):
        """Procédure de compression et de suppression des logs."""
        log.info("MAINTENANCE: Démarrage du nettoyage des fichiers...")
        now = time.time()
        
        for log_dir in LOG_DIRS:
            if not os.path.isdir(log_dir): continue
                
            for filename in os.listdir(log_dir):
                filepath = os.path.join(log_dir, filename)
                if os.path.isdir(filepath): continue
                
                # 1. NETTOYAGE DES ARCHIVES (.gz)
                if filename.endswith(".gz"):
                    age = self._get_age_days(filepath, now)
                    if age and age > MAX_GZ_AGE_DAYS:
                        os.remove(filepath)
                        log.info(f"Supprimé (Ancien GZ): {filename}")
                    continue
                    
                # 2. COMPRESSION (.log, .json, .txt) - Exclure les fichiers de config
                if not (filename.endswith(".log") or filename.endswith(".json")):
                    continue
                if "config" in filename or "tasks" in filename: # Protection
                    continue
                    
                age = self._get_age_days(filepath, now)
                if age and age > MAX_LOG_AGE_DAYS:
                    try:
                        with open(filepath, 'rb') as f_in, gzip.open(f"{filepath}.gz", 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                        os.remove(filepath)
                        log.info(f"Compressé: {filename}")
                    except Exception as e:
                        log.error(f"Erreur compression {filename}: {e}")

    async def run(self):
        loop = asyncio.get_event_loop()
        
        # Premier passage au démarrage
        await loop.run_in_executor(None, self.compress_old_logs)
        await loop.run_in_executor(None, self.optimize_vector_memory)
        
        while not self.signals.terminate:
            # On attend 24 heures
            await asyncio.sleep(60 * 60 * 24)
            
            if self.enabled:
                log.info("MAINTENANCE: Tâche quotidienne en cours...")
                await loop.run_in_executor(None, self.compress_old_logs)
                await loop.run_in_executor(None, self.optimize_vector_memory)