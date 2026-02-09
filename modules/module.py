import asyncio
import logging
# 🟢 CORRECTION CRITIQUE : Retour à l'importation absolue pour la compatibilité Streamlit/Standalone
# L'importation relative échoue lorsque le script est exécuté directement.
from modules.injection import Injection 

# Configuration du logger pour la classe de base
log = logging.getLogger('ModuleBase')

'''
An extendable class that defines a module that interacts with the main program.
All modules will be run in its own thread with its own event loop.
Do not use this class directly, extend it
'''


class Module:

    def __init__(self, signals, enabled=True):
        self.signals = signals
        self.enabled = enabled

        # L'injection est initialisée par défaut (aucune injection si la classe fille ne l'écrase pas)
        self.prompt_injection = Injection("", -1)

    # 🚀 AMÉLIORATION : Gère l'exécution asynchrone avec gestion des exceptions
    def init_event_loop(self):
        """
        Démarre la boucle d'événements du module, gérant les exceptions.
        C'est le point d'entrée pour les threads Python.
        """
        try:
            # 💡 NOTE : asyncio.run crée et démarre une nouvelle boucle d'événements
            asyncio.run(self.run())
        except asyncio.CancelledError:
            # Normal si le thread est fermé (via self.signals.terminate)
            log.info(f"[{self.__class__.__name__}] loop was cancelled.")
        except Exception as e:
            # ❌ Capture et log des erreurs critiques de la boucle asynchrone
            log.error(f"❌ ERREUR CRITIQUE dans la boucle de {self.__class__.__name__}: {e}", exc_info=True)

    def get_prompt_injection(self):
        """
        Retourne l'objet d'injection de prompt du module (texte et priorité).
        Doit être écrasé par la classe fille pour fournir un contexte dynamique.
        """
        return self.prompt_injection

    # Function that is called after all modules have provided their injections
    def cleanup(self):
        """
        Nettoyage des ressources (ex: vider la file des messages Twitch, nettoyer l'état).
        Cette méthode doit être implémentée dans les classes filles qui possèdent des états temporaires.
        """
        pass

    async def run(self):
        """
        Fonction principale asynchrone du module. Doit être implémentée par les classes filles.
        """
        # Exécuté lorsque le module est démarré.
        # Si non implémenté, la boucle se termine immédiatement.
        pass