'''
Represents some text to be injected into the LLM prompt.
Injections are added to the prompt from lowest to highest priority, with the highest being at the end.
Text is the text to be injected.
Priority is a positive integer. Injections with negative priority will be ignored.
System Prompt Priority: 10
Message History: 50
Twitch Chat: 100
'''


class Injection:
    def __init__(self, text: str, priority: int):
        self.text = text
        self.priority = priority

    def __str__(self):
        """Retourne le texte pour une utilisation directe."""
        return self.text

    # 🚀 AMÉLIORATION : Méthode de comparaison pour le tri
    def __lt__(self, other):
        """
        Définit la comparaison 'inférieur à' basée sur la priorité.
        Ceci permet à Python de trier facilement les objets Injection.
        """
        if not isinstance(other, Injection):
            # Fallback si la comparaison n'est pas avec un autre objet Injection
            return self.priority < other 
        return self.priority < other.priority