# Fichier : modules/resourceOptimizer.py

import psutil
import logging
import asyncio
import time
import os
from typing import Dict, Any, List, Optional, Union, Tuple
from modules.module import Module

# --- CONFIGURATION ---
# Seuils d'alerte critique pour les ressources
CPU_ALERT_THRESHOLD = 85.0 # % d'utilisation CPU
RAM_ALERT_THRESHOLD = 90.0 # % d'utilisation RAM
DISK_FREE_ALERT_GB = 50.0  # Moins de 50 Go restants sur le disque principal
CHECK_INTERVAL_SECONDS = 30 # Fréquence de la vérification

logger = logging.getLogger('ResourceOptimizer')

class ResourceOptimizer(Module):
    """
    Surveille l'état des ressources PC (CPU, RAM, Disque) et alerte le BrainModule
    en cas de goulot d'étranglement ou de pénurie.
    """
    def __init__(self, signals, modules: Dict[str, Any], enabled: bool = True):
        super().__init__(signals, enabled)
        self.modules = modules
        self.API = self.API(self)
        self.last_cpu_warning = 0.0
        
        # Dépendances critiques
        self.brain = self.modules.get('game_brain') 
        self.metrics = self.modules.get('plague_monitor') # Pour les métriques détaillées (CoreMetrics)

        logger.info("⚙️ Optimiseur de Ressources initialisé.")

    async def run(self):
        logger.info("⚙️ Optimiseur de Ressources démarré. Surveillance active.")
        
        while not self.signals.terminate:
            if self.enabled:
                # 🚨 AMÉLIORATION : Utilise asyncio.to_thread pour les appels psutil (potentiellement bloquants)
                await asyncio.to_thread(self.check_system_health)
                
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)

    def check_system_health(self):
        """
        Vérifie les métriques système critiques (CPU, RAM, DISQUE) et déclenche des alertes.
        """
        if not self.enabled: return
        
        alerts = []
        
        # 1. Vérification du CPU
        # On utilise interval=None pour obtenir la valeur immédiatement (car on est déjà dans un thread)
        cpu_percent = psutil.cpu_percent(interval=None) 
        if cpu_percent >= CPU_ALERT_THRESHOLD:
            alerts.append(f"CPU à {cpu_percent:.1f}% (Seuil dépassé: {CPU_ALERT_THRESHOLD}%)")
            
        # 2. Vérification de la RAM
        ram = psutil.virtual_memory()
        ram_percent = ram.percent
        if ram_percent >= RAM_ALERT_THRESHOLD:
            alerts.append(f"RAM utilisée à {ram_percent:.1f}% (Total: {ram.total / (1024**3):.1f} GB)")

        # 3. Vérification du Disque Principal (Assumons le disque du projet)
        try:
            # os.path.abspath(os.sep) retourne C:\ sur Windows
            disk_usage = psutil.disk_usage(os.path.abspath(os.sep)) 
            free_gb = disk_usage.free / (1024**3) 
            
            if free_gb <= DISK_FREE_ALERT_GB:
                alerts.append(f"Disque Faible: {free_gb:.1f} GB restants (Seuil: {DISK_FREE_ALERT_GB} GB)")
        except Exception as e:
            logger.warning(f"Impossible de vérifier l'usage disque: {e}")


        # --- GESTION DES ALERTES ET ACTION ---
        if alerts:
            # 💡 Action si le système est surchargé
            if self.brain and hasattr(self.brain, 'clio_is_playing') and self.brain.clio_is_playing:
                 # Si Clio joue, elle doit lâcher le contrôle pour libérer le CPU/GPU
                 self.brain.API.stop_clio_playing()
                 logger.critical(f"ALERTE RESS. : Système Surchargé. CLIO ARRÊTE LE JEU. {alerts[0]}")
                 
                 # 🚨 Alerte LLM pour le contexte (via le Prompter, qui injecterait un CustomPrompt)
                 self.signals.send_signal("URGENT_SYSTEM_ALERT", alerts)
                 
            else:
                 # Alerte le logger seulement pour éviter le spam si le LLM n'est pas en jeu
                 if time.time() - self.last_cpu_warning > 3600: # Max une alerte par heure
                      logger.warning(f"SYSTÈME SOUS CHARGE (IDLE) : {', '.join(alerts)}")
                      self.last_cpu_warning = time.time()
                      
        
    class API:
        def __init__(self, outer: 'ResourceOptimizer'):
            self.outer = outer

        def check_disk_space(self, path: str = os.getcwd()):
            """API pour vérifier l'espace disque sur un chemin donné."""
            try:
                usage = psutil.disk_usage(path)
                return {"total_gb": usage.total / (1024**3), 
                        "free_gb": usage.free / (1024**3), 
                        "percent_used": usage.percent}
            except Exception:
                return {"error": "Path invalide ou non accessible."}