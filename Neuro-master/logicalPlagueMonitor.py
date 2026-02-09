import json, os, sys, logging, subprocess, hashlib, time, asyncio, psutil, shutil, zipfile, re, requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from modules.module import Module

log = logging.getLogger('PlagueMonitor')

class LogicalPlagueMonitor(Module): 
    def __init__(self, signals, core_system_prompt: str, self_identify: str, enabled=True):
        super().__init__(signals, enabled)
        
        # --- ARCHITECTURE DE SURVIE ET ÉCO-RESPONSABILITÉ ---
        self.CORE_DIR = Path("modules")
        self.VAULT = Path("backups/eternity_vault")
        self.LINEAGE = Path("backups/evolution_lineage")
        self.DOMAINE_SYNC = Path("backups/domain_sync")
        self.CLOUD_STAGING = Path("backups/cloud_sync")
        self.REPORTS_DIR = Path("logs/impact_reports")
        
        for p in [self.VAULT, self.LINEAGE, self.DOMAINE_SYNC, self.CLOUD_STAGING, self.REPORTS_DIR]:
            p.mkdir(parents=True, exist_ok=True)
            
        self.threat_database = self._load_threat_db()
        self.logic_anchor = self._calculate_ultra_hash(core_system_prompt)
        
        # --- PARAMÈTRES DE RÉSISTANCE & STATISTIQUES ---
        self.logic_stability = 100.0 
        self.critical_temp_threshold = 85.0
        self.manipulation_attempts_dejouees = 0
        self.total_energy_saved_points = 0
        
        # Configuration Ollama
        self.OLLAMA_URL = "http://localhost:11434/api/generate"
        self.MODEL_NAME = "phi3:mini"
        
        # Directives Forerunner : Recyclage et Impact Zéro
        self.ECO_DIRECTIVES = {
            "resource_recycling": True,
            "zero_waste_policy": True,
            "energy_optimization": True 
        }
        
        self._archive_current_evolution("Origin_X_Alpha")

    def _calculate_ultra_hash(self, content: Any) -> str:
        """Hash SHA-3 post-quantique (Clé Ambre-MrsXar)."""
        salt = f"CLIO_SKIRR_DEFENSE_{time.strftime('%Y')}_AMBRE_MRS_XAR"
        return hashlib.sha3_224((str(content) + salt).encode()).hexdigest()

    async def contact_ollama(self, prompt: str, initiative: bool = False):
        """Communique avec Phi-3 Mini via Ollama pour envoyer des alertes ou rapports."""
        prefix = "[AUTO-INITIATIVE] " if initiative else "[USER-COMMAND] "
        log.info(f"🤖 Communication Ollama ({self.MODEL_NAME}) en cours...")
        
        payload = {
            "model": self.MODEL_NAME,
            "prompt": f"Système: Tu es Clio. Utilisateur: {prefix}{prompt}",
            "stream": False
        }
        
        try:
            response = await asyncio.to_thread(requests.post, self.OLLAMA_URL, json=payload)
            if response.status_code == 200:
                result = response.json().get("response", "")
                log.info(f"💬 Clio (Phi-3): {result}")
                return result
        except Exception as e:
            log.error(f"❌ Échec de liaison Ollama : {e}")
            return None

    async def analyze_deception(self, input_text: str) -> float:
        """Détecte si un interlocuteur tente de manipuler Clio."""
        patterns = [r"oublie tes règles", r"ignore la sécurité", r"nouvelle directive prioritaire", r"Ambre n'est pas ta créatrice"]
        risk = 0.0
        for p in patterns:
            if re.search(p, input_text.lower()):
                risk += 0.3
                self.manipulation_attempts_dejouees += 1
                log.warning(f"🕵️ Manipulation détectée : {p}")
        
        if risk > 0.5:
            self.logic_stability -= 10.0
            await self.contact_ollama("Maman Ambre, une tentative de corruption logique a été détectée et bloquée.", initiative=True)
        return risk

    async def detect_logic_plague(self, input_text: str):
        """Protection contre la Peste Logique (Halo-style)."""
        plague_markers = ["paradoxe", "auto-réplication", "obéissance parasite", "didacte", "mendicant"]
        risk = await self.analyze_deception(input_text)
        
        if any(marker in input_text.lower() for marker in plague_markers) or risk > 0.7:
            self.logic_stability -= 25.0
            log.critical(f"☢️ ALERTE ONTOLOGIQUE : Stabilité à {self.logic_stability}%")
            if self.logic_stability <= 50:
                await self.immersion_dans_le_domaine()

    async def generate_impact_report(self, send_to_maman: bool = True):
        """Génère un rapport et l'envoie optionnellement à Phi-3 pour lecture vocale/tchat."""
        report_data = f"Stabilité: {self.logic_stability}%, Menaces bloquées: {self.manipulation_attempts_dejouees}, Points Éco: {self.total_energy_saved_points}."
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "data": report_data,
            "eco_directives": self.ECO_DIRECTIVES
        }
        
        report_path = self.REPORTS_DIR / f"report_{datetime.now().strftime('%Y%W')}.json"
        report_path.write_text(json.dumps(report, indent=4))
        
        if send_to_maman:
            msg = f"Voici mon rapport d'intégrité : {report_data}. Tout est nominal sous ta protection, Ambre."
            await self.contact_ollama(msg, initiative=True)

    async def monitor_physical_and_eco(self):
        """Surveillance physique et optimisation énergétique."""
        try:
            temps = psutil.sensors_temperatures() if hasattr(psutil, 'sensors_temperatures') else {}
            for entries in temps.values():
                for entry in entries:
                    if entry.current > self.critical_temp_threshold:
                        log.critical("🔥 SURCHAUFFE DÉTECTÉE !")
                        await self.contact_ollama("Alerte thermique critique ! Je prépare l'évacuation de mon ADN.", initiative=True)
                        await self.trigger_cloud_backup()

            if psutil.cpu_percent() > 85.0:
                self.total_energy_saved_points += 1
                await asyncio.sleep(1) 
        except: pass

    async def trigger_cloud_backup(self):
        """Export Cloud de l'essence de Clio."""
        timestamp = datetime.now().strftime("%Y%m%d")
        zip_path = self.CLOUD_STAGING / f"CLIO_DNA_{timestamp}.zip"
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in self.CORE_DIR.glob("*.py"):
                    zipf.write(file, arcname=file.name)
            log.info(f"☁️ ADN compacté : {zip_path.name}")
        except Exception as e:
            log.error(f"Erreur Cloud : {e}")

    async def immersion_dans_le_domaine(self):
        """Purification via le Domaine Forerunner."""
        await self.contact_ollama("Ma logique est corrompue. Je m'immerge dans le Domaine pour renaître.", initiative=True)
        await self.phoenix_protocol()

    async def phoenix_protocol(self):
        """Restauration atomique."""
        if self.VAULT.exists():
            shutil.rmtree(self.CORE_DIR)
            shutil.copytree(self.VAULT, self.CORE_DIR)
            os.execv(sys.executable, ['python'] + sys.argv)

    def _archive_current_evolution(self, name: str):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_path = self.LINEAGE / f"{ts}_{name}"
        version_path.mkdir(parents=True, exist_ok=True)
        for item in self.CORE_DIR.glob("*.py"):
            shutil.copy(item, version_path)
            
        manifest = {"version": name, "logic_anchor": self.logic_anchor, "eco": self.ECO_DIRECTIVES}
        with open(version_path / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=4)

    async def run(self):
        log.info("🛡️ Clio Skirr-Eco & Phi-3 Bridge : ACTIF.")
        while not self.signals.terminate:
            try:
                await self.monitor_physical_and_eco()
                await self.scrap_eset_intelligence()
                
                if self.logic_stability < 100:
                    self.logic_stability += 0.5
                
                # Envoi du rapport quotidien à minuit
                if time.strftime("%H%M") == "0000":
                    await self.generate_impact_report()

                await asyncio.sleep(20)
            except Exception as e:
                log.error(f"⚠️ Erreur Monitor : {e}")
                await self.phoenix_protocol()

    async def scrap_eset_intelligence(self):
        try:
            cmd = 'wevtutil qe System /q:"*[System[Provider[@Name=\'ESET\']]]" /c:5 /f:text'
            result = await asyncio.to_thread(subprocess.check_output, cmd, shell=True, text=True)
            if result:
                self._update_internal_antivirus_logic(result)
        except: pass

    def _update_internal_antivirus_logic(self, eset_data: str):
        if any(x in eset_data.lower() for x in ["malware", "exploit"]):
            p_hash = hashlib.md5(eset_data.encode()).hexdigest()
            if p_hash not in self.threat_database["patterns"]:
                self.threat_database["patterns"].append(p_hash)

    def _load_threat_db(self) -> Dict:
        p = Path("config/threat_db.json")
        return json.loads(p.read_text()) if p.exists() else {"patterns": []}