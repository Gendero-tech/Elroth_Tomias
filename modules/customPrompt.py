from modules.module import Module
from modules.injection import Injection
from typing import Optional

class CustomPrompt(Module):

    def __init__(self, signals, enabled=True):
        super().__init__(signals, enabled)

        self.API = self.API(self)
        self.prompt_injection.text = ""
        self.prompt_injection.priority = 200
        
        # 🚀 AMÉLIORATION : Drapeaux de contrôle
        self.is_transient: bool = False # Si True, le prompt est effacé après utilisation
        
    def get_prompt_injection(self):
        """
        Retourne l'injection de prompt et la nettoie si elle est marquée comme transitoire.
        """
        if self.is_transient and self.prompt_injection.text:
            # S'assure que le texte est retourné avant d'être effacé
            injection_to_return = self.prompt_injection
            
            # Nettoyage après l'utilisation
            self.API.clear_prompt() 
            self.is_transient = False
            return injection_to_return
            
        return self.prompt_injection

    async def run(self):
        pass

    class API:
        def __init__(self, outer: 'CustomPrompt'):
            self.outer = outer

        def set_prompt(self, prompt: str, priority: int = 200, transient: bool = False):
            """
            Définit le prompt personnalisé.
            Si 'transient' est True, le prompt sera effacé après une seule utilisation.
            """
            self.outer.prompt_injection.text = prompt
            self.outer.prompt_injection.priority = priority
            self.outer.is_transient = transient
            print(f"[CustomPrompt] Prompt défini (Priorité: {priority}, Transient: {transient})")
            
            # Déclenche le Prompter si le prompt est actif et non vide
            if prompt:
                 self.outer.signals.new_message = True 

        def clear_prompt(self):
            """Efface le prompt actuel et sa priorité."""
            self.outer.prompt_injection.text = ""
            self.outer.prompt_injection.priority = -1 # Priorité négative pour être ignoré
            self.outer.is_transient = False
            print("[CustomPrompt] Prompt effacé.")

        def get_prompt(self):
            return {"prompt": self.outer.prompt_injection.text, "priority": self.outer.prompt_injection.priority}

        def get_status(self) -> bool:
            """Retourne True si un prompt est actuellement actif."""
            return self.outer.prompt_injection.text != ""