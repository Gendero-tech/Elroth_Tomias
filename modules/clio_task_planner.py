import logging
import json
import os
from datetime import datetime
from modules.module import Module

log = logging.getLogger('TaskPlanner')

class TaskPlanner(Module):
    def __init__(self, signals, modules, enabled=True):
        super().__init__(signals, enabled)
        self.modules = modules
        self.API = self.API(self)
        
        # Chemin vers le fichier de tâches dans ton disque G:
        self.tasks_file = os.path.join("memories", "tasks_list.json")
        self.tasks = self.load_tasks()

    def load_tasks(self):
        if os.path.exists(self.tasks_file):
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"current_project": "Inconnu", "objectifs": []}

    def save_tasks(self):
        os.makedirs(os.path.dirname(self.tasks_file), exist_ok=True)
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, indent=4, ensure_ascii=False)

    def add_task(self, description: str, priority: int = 2):
        task = {
            "id": len(self.tasks["objectifs"]) + 1,
            "desc": description,
            "priority": priority,
            "status": "en_cours",
            "date_added": datetime.now().isoformat()
        }
        self.tasks["objectifs"].append(task)
        self.save_tasks()
        return f"Objectif ajouté : {description}"

    class API:
        def __init__(self, outer):
            self.outer = outer

        def get_pending_tasks(self):
            return [t for t in self.outer.tasks["objectifs"] if t["status"] == "en_cours"]

        def add_objective(self, desc: str):
            return self.outer.add_task(desc)

        def complete_task(self, task_id: int):
            for t in self.outer.tasks["objectifs"]:
                if t["id"] == task_id:
                    t["status"] = "termine"
                    self.outer.save_tasks()
                    return True
            return False