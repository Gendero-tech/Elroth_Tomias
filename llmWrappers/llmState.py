import os
from typing import List
import time
import logging

logger = logging.getLogger('LLMState')

class LLMState:
    """
    Conteneur d'état global pour le module de langage (LLM).
    Gère l'état activé/désactivé, l'interruption, et la liste noire de sécurité.
    """
    def __init__(self):
        self.enabled = True
        self.next_cancelled = False
        self.is_ready = False
        self.blacklist: List[str] = []

        # 🚀 AMÉLIORATION : Utilisation de la méthode de rechargement pour l'initialisation
        self.reload_blacklist(initial_load=True)
        
        # Le statut 'is_ready' est maintenant défini à l'intérieur de reload_blacklist
        if self.is_ready:
            logger.info(f"LLMState initialisé. {len(self.blacklist)} mots dans la liste noire.")
        else:
            logger.error("LLMState initialisé avec ERREUR. Vérifiez le statut de la liste noire.")

    def reload_blacklist(self, initial_load: bool = False):
        """
        Recharge la liste noire depuis 'blacklist.txt'.
        Peut être appelée à chaud (runtime) pour mettre à jour la sécurité.
        """
        try:
            # 1. Lecture avec encodage UTF-8
            with open('blacklist.txt', 'r', encoding='utf-8') as file:
                # Filtrer les lignes vides et les espaces pour obtenir une liste propre
                new_blacklist = [line.strip().lower() for line in file.read().splitlines() if line.strip()]
                self.blacklist = new_blacklist
                
            # Marquer comme prêt UNIQUEMENT après une lecture réussie
            self.is_ready = True
                
            if not initial_load:
                logger.info(f"Liste noire rechargée à chaud. {len(self.blacklist)} mots actifs.")
            
        except FileNotFoundError:
            if initial_load:
                logger.warning("Fichier blacklist.txt non trouvé. Création avec une liste vide.")
                self.blacklist = []
                self._create_empty_blacklist_file()
                self.is_ready = True # Prêt, car nous avons créé le fichier
            else:
                # Si non trouvé à chaud, nous ne marquons pas comme non prêt, mais nous avertissons.
                logger.warning("Tentative de rechargement à chaud : Fichier blacklist.txt non trouvé. Statut inchangé.")
                # self.is_ready reste True si le chargement initial était réussi.
                
        except Exception as e:
            logger.error(f"ERREUR CRITIQUE lors de la lecture de blacklist.txt : {e}")
            self.blacklist = []
            self.is_ready = False # Non prêt si une erreur de lecture/encodage survient

    def _create_empty_blacklist_file(self):
        """ Crée le fichier de liste noire s'il n'existe pas. """
        try:
            with open('blacklist.txt', 'w', encoding='utf-8') as file:
                file.write("")
        except Exception as e:
            logger.error(f"ERREUR: Impossible de créer le fichier blacklist.txt : {e}")
            
# --- EXÉCUTION DE TEST ---
if __name__ == '__main__':
    # Test simple de la classe
    state = LLMState()
    # Testez la modification manuelle du fichier, puis appelez :
    # state.reload_blacklist()
    pass