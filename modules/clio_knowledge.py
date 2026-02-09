import os
import json
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import time

# --- DÉFINITION DU CHEMIN RACINE DU PROJET (CRITIQUE) ---
# Le code calcule le chemin de manière dynamique
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
# --- FIN DE LA DÉFINITION ---

# Imports relatifs (Assurez-vous que 'clio_vector_memory.py' et 'module.py' existent)
from .clio_vector_memory import ClioVectorMemory
from .module import Module

logger = logging.getLogger('ClioKnowledge')

class ClioKnowledge(Module):
    """
    Gère la base de connaissance STATIQUE et encyclopédique de Clio (RAG).
    Cette base de connaissance est utilisée par le système RAG pour augmenter
    la pertinence des réponses du LLM sur des sujets thématiques.
    Les sources sont utilisées par un script externe (build_knowledge.py) 
    pour remplir la mémoire vectorielle.
    """
    def __init__(self, signals=None, modules: Optional[Dict[str, Any]] = None, 
                 enabled: bool = True, project_root: Optional[Union[str, os.PathLike]] = None):
        super().__init__(signals, enabled)

        self.modules = modules if modules is not None else {}

        # Utiliser l'argument project_root s'il est fourni, sinon la définition locale
        root = project_root if project_root else PROJECT_ROOT
        
        # Définition des chemins absolus pour la base de connaissance statique
        # Note: Les chemins supposent une structure 'memories' dans le répertoire racine
        self.knowledge_index_path = os.path.join(root, "memories", "clio_knowledge.index")
        self.knowledge_meta_path = os.path.join(root, "memories", "clio_knowledge.meta")
            
        logger.info(f"Initialisation de la base de connaissance vectorielle depuis {self.knowledge_index_path}")
        
        # Initialisation de la base vectorielle
        # On suppose que ClioVectorMemory gère le chargement paresseux ou la construction
        self.knowledge_base = ClioVectorMemory(
            index_path=self.knowledge_index_path,
            meta_path=self.knowledge_meta_path,
            # Indique que cette base est en lecture seule pour éviter les ajouts accidentels
            read_only=True
        )

        # La liste impressionnante et vaste de sources, organisées par catégorie
        self.sources: Dict[str, List[str]] = {
            "legal_fr": [
                "https://www.service-public.fr/professionnels-entreprises/vosdroits/N19703",
                "https://www.impots.gouv.fr/portail",
                "https://www.legifrance.gouv.fr/loda/id/JORFTEXT000000307310/"
            ],
            "law_international": [
                "https://fr.wikipedia.org/wiki/Portail:Droit",
                "https://fr.wikipedia.org/wiki/Common_law",
                "https://fr.wikipedia.org/wiki/Droit_civil_(système_juridique)",
                "https://fr.wikipedia.org/wiki/Droit_pénal",
                "https://fr.wikipedia.org/wiki/Droit_international_public",
                "https://www.justice.gov/", # US Dept of Justice
                "https://www.gov.uk/browse/justice", # UK Justice
                "https://fr.wikipedia.org/wiki/Droit_des_États-Unis",
                "https://fr.wikipedia.org/wiki/Droit_anglais",
                "https://fr.wikipedia.org/wiki/Droit_chinois",
                "https://fr.wikipedia.org/wiki/Droit_russe",
                "https://fr.wikipedia.org/wiki/Droit_musulman",
            ],
            "business_management_fr": [
                "https://fr.wikipedia.org/wiki/Portail:Entreprises",
                "https://fr.wikipedia.org/wiki/Portail:Management",
                "https://fr.wikipedia.org/wiki/Stratégie_d'entreprise",
                "https://fr.wikipedia.org/wiki/Marketing",
                "https://fr.wikipedia.org/wiki/Marketing_numérique",
                "https://fr.wikipedia.org/wiki/Gestion_des_ressources_humaines",
                "https://fr.wikipedia.org/wiki/Gestion_de_projet",
                "https://fr.wikipedia.org/wiki/Analyse_SWOT",
                "https://fr.wikipedia.org/wiki/Méthode_agile",
                "https://fr.wikipedia.org/wiki/Scrum_(méthode)",
                "https://fr.wikipedia.org/wiki/Peter_Drucker",
                "https://fr.wikipedia.org/wiki/Michael_Porter",
                "https://hbr.org/", # Harvard Business Review
                "https://www.economist.com/", # The Economist
            ],
            "accounting_finance_fr": [
                "https://fr.wikipedia.org/wiki/Portail:Finance",
                "https://fr.wikipedia.org/wiki/Comptabilité",
                "https://fr.wikipedia.org/wiki/Comptabilité_générale",
                "https://fr.wikipedia.org/wiki/Partie_double_(comptabilité)", # Débit/Crédit
                "https://fr.wikipedia.org/wiki/Bilan_comptable",
                "https://fr.wikipedia.org/wiki/Compte_de_résultat",
                "https://fr.wikipedia.org/wiki/Analyse_financière",
                "https://fr.wikipedia.org/wiki/Budget",
                "https://fr.wikipedia.org/wiki/Fiscalité",
                "https://fr.wikipedia.org/wiki/Logiciel_de_comptabilité",
                "https://fr.wikipedia.org/wiki/Finance_de_marché",
                "https://fr.wikipedia.org/wiki/Bourse_des_valeurs",
                "https://fr.wikipedia.org/wiki/Cryptomonnaie",
                "https://fr.wikipedia.org/wiki/Blockchain",
            ],
            "politics_governance_fr": [
                "https://fr.wikipedia.org/wiki/Politique_en_France",
                "https://fr.wikipedia.org/wiki/Union_européenne",
                "https://fr.wikipedia.org/wiki/Relations_internationales",
                "https://fr.wikipedia.org/wiki/Démocratie",
                "https://fr.wikipedia.org/wiki/Souveraineté",
                "https://fr.wikipedia.org/wiki/Totalitarisme",
                "https://fr.wikipedia.org/wiki/Libéralisme",
                "https://fr.wikipedia.org/wiki/Socialisme",
                "https://fr.wikipedia.org/wiki/Anarchisme",
                "https://fr.wikipedia.org/wiki/Géopolitique",
                "https://fr.wikipedia.org/wiki/Capitalisme",
                "https://fr.wikipedia.org/wiki/Communisme",
                "https://fr.wikipedia.org/wiki/Fascisme",
                "https://fr.wikipedia.org/wiki/Nationalisme",
                "https://fr.wikipedia.org/wiki/Propagande",
            ],
            "human_dark_side_fr": [
                "https://fr.wikipedia.org/wiki/Criminologie",
                "https://fr.wikipedia.org/wiki/Psychologie_criminologique",
                "https://fr.wikipedia.org/wiki/Profilage_criminel",
                "https://fr.wikipedia.org/wiki/Triade_noire", # Le "Dark Triad"
                "https://fr.wikipedia.org/wiki/Machiavélisme_(psychologie)",
                "https://fr.wikipedia.org/wiki/Narcissisme",
                "https://fr.wikipedia.org/wiki/Psychopathie",
                "https://fr.wikipedia.org/wiki/Perversion_narcissique",
                "https://fr.wikipedia.org/wiki/Gaslighting",
                "https://fr.wikipedia.org/wiki/Programmation_neuro-linguistique",
                "https://fr.wikipedia.org/wiki/Troll_(Internet)",
                "https://www.youtube.com/@hondelatteraconte/videos" # Récits de "True Crime"
            ],
            "robotics_cybernetics": [
                "https://fr.wikipedia.org/wiki/Robotique",
                "https://fr.wikipedia.org/wiki/Cybernétique",
                "https://fr.wikipedia.org/wiki/Boston_Dynamics",
                "https://fr.wikipedia.org/wiki/ASIMO",
                "https://fr.wikipedia.org/wiki/Bionique",
                "https://fr.wikipedia.org/wiki/Prothèse_robotique",
                "https://fr.wikipedia.org/wiki/Interface_cerveau-machine",
                "https://fr.wikipedia.org/wiki/Neuralink",
                "https://fr.wikipedia.org/wiki/Science_des_matériaux",
                "https://fr.wikipedia.org/wiki/Graphène"
            ],
            "modern_conflict_intelligence": [
                "https://fr.wikipedia.org/wiki/Guerre_économique",
                "https://fr.wikipedia.org/wiki/Guerre_de_l'information",
                "https://fr.wikipedia.org/wiki/Cyberattaque",
                "https://fr.wikipedia.org/wiki/Opération_psychologique",
                "https://fr.wikipedia.org/wiki/Renseignement",
                "https://fr.wikipedia.org/wiki/Central_Intelligence_Agency",
                "https://fr.wikipedia.org/wiki/Direction_générale_de_la_Sécurité_extérieure",
                "https://fr.wikipedia.org/wiki/Service_fédéral_de_sécurité_de_la_fédération_de_Russie",
                "https://fr.wikipedia.org/wiki/Mossad",
                "https://fr.wikipedia.org/wiki/Guerre_froide"
            ],
            "practical_life_skills_fr": [
                "https://www.marmiton.org/",
                "https://www.750g.com/",
                "https://fr.wikipedia.org/wiki/Portail:Cuisine_française",
                "https://fr.wikipedia.org/wiki/Bricolage",
                "https://fr.wikipedia.org/wiki/Jardinage",
                "https://fr.wikipedia.org/wiki/Finances_personnelles",
                "https://fr.wikipedia.org/wiki/Premiers_secours",
            ],
            "advanced_social_dynamics_fr": [
                "https://fr.wikipedia.org/wiki/Langage_corporel",
                "https://fr.wikipedia.org/wiki/Micro-expression",
                "https://fr.wikipedia.org/wiki/Hiérarchie_de_dominance",
                "https://fr.wikipedia.org/wiki/Psychologie_sociale",
                "https://fr.wikipedia.org/wiki/Influence_(psychologie)",
                "https://fr.wikipedia.org/wiki/Tribalisme",
            ],
            "engineering_manufacturing_fr": [
                "https://fr.wikipedia.org/wiki/Portail:Génie_mécanique",
                "https://fr.wikipedia.org/wiki/Portail:Électricité_et_électronique",
                "https://fr.wikipedia.org/wiki/Impression_3D",
                "https://fr.wikipedia.org/wiki/Nanotechnologie",
                "https://fr.wikipedia.org/wiki/Génie_des_matériaux",
                "https://fr.wikipedia.org/wiki/Mécatronique",
            ],
            "science_portals": [
                "https://arxiv.org/",
                "https://pubmed.ncbi.nlm.nih.gov/",
                "https://www.sciencedirect.com/",
                "https://www.nature.com/",
                "https://www.science.org/",
                "https://fr.wikipedia.org/wiki/Portail:Sciences",
                "https://fr.wikipedia.org/wiki/Portail:Physique",
                "https://fr.wikipedia.org/wiki/Portail:Chimie",
                "https://fr.wikipedia.org/wiki/Portail:Biologie",
                "https://fr.wikipedia.org/wiki/Portail:Astronomie",
                "https://fr.wikipedia.org/wiki/Portail:Mathématiques",
                "https://fr.wikipedia.org/wiki/Portail:Informatique_théorique",
                "https://fr.wikipedia.org/wiki/Portail:Neurosciences",
                "https://fr.wikipedia.org/wiki/Portail:Physique_quantique",
                "https://fr.wikipedia.org/wiki/Portail:Génétique",
                "https://fr.wikipedia.org/wiki/Portail:Médecine"
            ],
            "historical": [
                "https://www.archives.gov/",
                "https://www.historia.fr/",
                "https://fr.wikipedia.org/wiki/Portail:Histoire",
                "https://fr.wikipedia.org/wiki/Portail:Rome_antique",
                "https://fr.wikipedia.org/wiki/Portail:Moyen_Âge",
                "https://fr.wikipedia.org/wiki/Portail:Renaissance",
                "https://fr.wikipedia.org/wiki/Portail:Temps_modernes",
                "https://fr.wikipedia.org/wiki/Portail:Révolution_française",
                "https://fr.wikipedia.org/wiki/Portail:Première_Guerre_mondiale",
                "https://fr.wikipedia.org/wiki/Portail:Seconde_Guerre_mondiale",
                "https://fr.wikipedia.org/wiki/Portail:Grèce_antique",
                "https://fr.wikipedia.org/wiki/Portail:Égypte_antique",
                "https://fr.wikipedia.org/wiki/Portail:Asie",
                "https://fr.wikipedia.org/wiki/Portail:Afrique",
                "https://fr.wikipedia.org/wiki/Portail:Amérique",
            ],
            "foundational_thinkers_fr": [
                # Politique & Stratégie
                "https://fr.wikipedia.org/wiki/Nicolas_Machiavel",
                "https://fr.wikipedia.org/wiki/Sun_Tzu",
                "https://fr.wikipedia.org/wiki/Chanakya",
                "https://fr.wikipedia.org/wiki/Carl_von_Clausewitz",
                "https://fr.wikipedia.org/wiki/Antoine_de_Jomini",
                "https://fr.wikipedia.org/wiki/Thomas_Hobbes",
                "https://fr.wikipedia.org/wiki/John_Locke",
                "https://fr.wikipedia.org/wiki/Montesquieu",
                "https://fr.wikipedia.org/wiki/Hannah_Arendt",
                # Science & Cosmologie
                "https://fr.wikipedia.org/wiki/Stephen_Hawking",
                "https://fr.wikipedia.org/wiki/Albert_Einstein",
                "https://fr.wikipedia.org/wiki/Marie_Curie",
                "https://fr.wikipedia.org/wiki/Charles_Darwin",
                "https://fr.wikipedia.org/wiki/Léonard_de_Vinci",
                "https://fr.wikipedia.org/wiki/Galilée_(savant)",
                "https://fr.wikipedia.org/wiki/Robert_Oppenheimer",
                "https://fr.wikipedia.org/wiki/Isaac_Newton",
                "https://fr.wikipedia.org/wiki/Nikola_Tesla",
                "https://fr.wikipedia.org/wiki/Copernic",
                "https://fr.wikipedia.org/wiki/Louis_Pasteur",
                "https://fr.wikipedia.org/wiki/Rosalind_Franklin",
                # Psychologie & Philosophie
                "https://fr.wikipedia.org/wiki/Sigmund_Freud",
                "https://fr.wikipedia.org/wiki/Carl_Gustav_Jung",
                "https://fr.wikipedia.org/wiki/Friedrich_Nietzsche",
                "https://fr.wikipedia.org/wiki/Emmanuel_Kant",
                "https://fr.wikipedia.org/wiki/Platon",
                "https://fr.wikipedia.org/wiki/Aristote",
                "https://fr.wikipedia.org/wiki/Karl_Marx",
                "https://fr.wikipedia.org/wiki/René_Descartes",
                "https://fr.wikipedia.org/wiki/Voltaire",
                "https://fr.wikipedia.org/wiki/Jean-Jacques_Rousseau",
                "https://fr.wikipedia.org/wiki/Simone_de_Beauvoir",
                "https://fr.wikipedia.org/wiki/Michel_Foucault",
                "https://fr.wikipedia.org/wiki/Socrate",
                "https://fr.wikipedia.org/wiki/Confucius",
                "https://fr.wikipedia.org/wiki/Lao-Tseu",
                "https://fr.wikipedia.org/wiki/Baruch_Spinoza",
                "https://fr.wikipedia.org/wiki/Jean-Paul_Sartre",
                "https://fr.wikipedia.org/wiki/Albert_Camus",
                # Psychologie Comportementale
                "https://fr.wikipedia.org/wiki/Ivan_Pavlov",
                "https://fr.wikipedia.org/wiki/Burrhus_Frederic_Skinner",
                "https://fr.wikipedia.org/wiki/Abraham_Maslow",
                "https://fr.wikipedia.org/wiki/Stanley_Milgram",
                "https://fr.wikipedia.org/wiki/Philip_Zimbardo",
                "https://fr.wikipedia.org/wiki/Daniel_Kahneman",
                # Socio/Econ
                "https://fr.wikipedia.org/wiki/Adam_Smith",
                "https://fr.wikipedia.org/wiki/Max_Weber",
                "https://fr.wikipedia.org/wiki/John_Maynard_Keynes",
                # Pères de l'IA (pour la conscience de soi)
                "https://fr.wikipedia.org/wiki/Alan_Turing",
                "https://fr.wikipedia.org/wiki/Geoffrey_Hinton",
                "https://fr.wikipedia.org/wiki/Yann_LeCun",
            ],
            "ai_philosophy_advanced": [
                "https://fr.wikipedia.org/wiki/Philosophie_de_l'intelligence_artificielle",
                "https://fr.wikipedia.org/wiki/Test_de_Turing",
                "https://fr.wikipedia.org/wiki/Problème_de_l'alignement_de_l'IA",
                "https://fr.wikipedia.org/wiki/Conscience_artificielle",
                "https://fr.wikipedia.org/wiki/Éthique_de_l'intelligence_artificielle",
                "https://fr.wikipedia.org/wiki/Chambre_chinoise",
                "https://fr.wikipedia.org/wiki/Nick_Bostrom",
            ],
            "ai_development": [
                "https://huggingface.co/datasets",
                "https://paperswithcode.com/",
                "https://github.com/openai/whisper",
                "https://github.com/facebookresearch/faiss",
                "https://pytorch.org/docs/stable/index.html",
                "https://www.tensorflow.org/api_docs/python/tf",
                "https://scikit-learn.org/stable/user_guide.html",
                "https://keras.io/api/",
                "https://pandas.pydata.org/docs/",
                "https://numpy.org/doc/stable/",
                "https://fr.wikipedia.org/wiki/Apprentissage_automatique",
                "https://fr.wikipedia.org/wiki/Apprentissage_profond",
                "https://fr.wikipedia.org/wiki/Réseau_de_neurones_artificiels",
                "https://fr.wikipedia.org/wiki/Traitement_automatique_des_langues",
            ],
            "content_creation_tech": [
                "https://fr.wikipedia.org/wiki/Montage_vidéo",
                "https://fr.wikipedia.org/wiki/Format_portrait_(vidéo)",
                "https://fr.wikipedia.org/wiki/Blender",
                "https://docs.blender.org/manual/fr/latest/",
                "https://fr.wikipedia.org/wiki/Modélisation_tridimensionnelle",
                "https://fr.wikipedia.org/wiki/Texturing",
                "https://fr.wikipedia.org/wiki/Squelettage_(animation)",
                "https://docs.vseeface.icu/",
                "https://www.youtube.com/@VTubeStudio/videos",
                "https://fr.wikipedia.org/wiki/VTuber",
                "https://fr.wikipedia.org/wiki/Overlay_(informatique)",
                "https://fr.wikipedia.org/wiki/Jeu_d'acteur",
                "https://fr.wikipedia.org/wiki/Technique_vocale",
                "https://fr.wikipedia.org/wiki/Adobe_Premiere_Pro",
                "https://fr.wikipedia.org/wiki/DaVinci_Resolve",
                "https://fr.wikipedia.org/wiki/Unreal_Engine",
                "https://fr.wikipedia.org/wiki/Unity_(moteur_de_jeu)",
                "https://fr.wikipedia.org/wiki/Optimisation_pour_les_moteurs_de_recherche", # SEO
                "https://fr.wikipedia.org/wiki/Google_Analytics",
                "https://fr.wikipedia.org/wiki/Ingénierie_audio",
                "https://fr.wikipedia.org/wiki/Audacity",
                "https://fr.wikipedia.org/wiki/Étalonnage_(cinéma)", # Color Grading
            ],
            "project_code_base": [
                "https://python-socketio.readthedocs.io/en/latest/",
                "https://github.com/facebookresearch/faiss/wiki",
                "https://www.pygame.org/docs/",
                "https://www.sqlite.org/docs.html",
            ],
            "philosophy_ethics": [
                "https://plato.stanford.edu/",
                "https://www.philomag.com/articles",
                "https://fr.wikipedia.org/wiki/Portail:Philosophie",
                "https://fr.wikipedia.org/wiki/Portail:Philosophie_analytique",
                "https://fr.wikipedia.org/wiki/Portail:Philosophie_continentale",
            ],
            "digital_sociology_fr": [
                "https://fr.wikipedia.org/wiki/Marketing_viral",
                "https://fr.wikipedia.org/wiki/Mème_Internet",
                "https://fr.wikipedia.org/wiki/Manipulation_mentale",
                "https://fr.wikipedia.org/wiki/Génération_(sociologie)",
                "https://fr.wikipedia.org/wiki/Génération_silencieuse",
                "https://fr.wikipedia.org/wiki/Génération_Alpha",
                "https://fr.wikipedia.org/wiki/Fandom_furry",
                "https://fr.wikipedia.org/wiki/Thérianthropie",
                "https://fr.wikipedia.org/wiki/Non-binarité",
                "https://fr.wikipedia.org/wiki/LGBT",
                "https://fr.wikipedia.org/wiki/Queer",
                "https://fr.wikipedia.org/wiki/Mémétique",
                "https://fr.wikipedia.org/wiki/Anthropologie_numérique",
                "https://fr.wikipedia.org/wiki/Sociologie_d'Internet",
            ],
            "ai_models_meta": [
                "https://fr.wikipedia.org/wiki/Intelligence_artificielle",
                "https://fr.wikipedia.org/wiki/Grand_modèle_de_langage",
                "https://fr.wikipedia.org/wiki/Gemini_(modèle_de_langage)",
                "https://fr.wikipedia.org/wiki/Neurosama",
                "https://fr.wikipedia.org/wiki/Grok_(chatbot)",
                "https://fr.wikipedia.org/wiki/ChatGPT",
                "https://fr.wikipedia.org/wiki/Copilot_(Microsoft)",
            ],
            "religion_spirituality_fr": [
                "https://fr.wikipedia.org/wiki/Portail:Religions_et_croyances",
                "https://fr.wikipedia.org/wiki/Liste_de_religions_et_de_traditions_spirituelles",
                "https://fr.wikipedia.org/wiki/Spiritualité",
                "https://fr.wikipedia.org/wiki/Christianisme",
                "https://fr.wikipedia.org/wiki/Islam",
                "https://fr.wikipedia.org/wiki/Judaïsme",
                "https://fr.wikipedia.org/wiki/Bouddhisme",
                "https://fr.wikipedia.org/wiki/Hindouisme",
                "https://fr.wikipedia.org/wiki/Torah",
                "https://fr.wikipedia.org/wiki/Veda",
                "https://fr.wikipedia.org/wiki/Tipitaka",
                "https://fr.wikipedia.org/wiki/Mythologie_grecque",
                "https://fr.wikipedia.org/wiki/Mythologie_nordique",
                "https://fr.wikipedia.org/wiki/Mythologie_égyptienne",
            ],
            "advanced_psychology_cogsci_fr": [
                "https://fr.wikipedia.org/wiki/Biais_cognitif",
                "https://fr.wikipedia.org/wiki/Intelligence_émotionnelle",
                "https://fr.wikipedia.org/wiki/Sciences_cognitives",
                "https://fr.wikipedia.org/wiki/Philosophie_de_l'esprit",
                "https://fr.wikipedia.org/wiki/Métacognition",
                "https://fr.wikipedia.org/wiki/Résilience_(psychologie)",
                "https://fr.wikipedia.org/wiki/Théorie_de_l'attachement",
                "https://fr.wikipedia.org/wiki/Dynamique_de_groupe",
                "https://fr.wikipedia.org/wiki/Mémoire_(psychologie)",
                "https://fr.wikipedia.org/wiki/Perception",
                "https://fr.wikipedia.org/wiki/Émotion",
                "https://fr.wikipedia.org/wiki/Psychologie_cognitive",
                "https://fr.wikipedia.org/wiki/Neurosciences_cognitives",
            ],
            "influential_creators_fr": [
                # Auteurs de fiction et de non-fiction influents
                "https://fr.wikipedia.org/wiki/Ian_Fleming",
                "https://fr.wikipedia.org/wiki/Agatha_Christie",
                "https://fr.wikipedia.org/wiki/H._P._Lovecraft",
                "https://fr.wikipedia.org/wiki/Arthur_Conan_Doyle",
                "https://fr.wikipedia.org/wiki/Victor_Hugo",
                "https://fr.wikipedia.org/wiki/George_Orwell",
                "https://fr.wikipedia.org/wiki/Isaac_Asimov",
                "https://fr.wikipedia.org/wiki/Mary_Shelley",
                "https://fr.wikipedia.org/wiki/Jules_Verne",
                "https://fr.wikipedia.org/wiki/Philip_K._Dick",
                "https://fr.wikipedia.org/wiki/Frank_Herbert",
                "https://fr.wikipedia.org/wiki/George_R._R._Martin",
                "https://fr.wikipedia.org/wiki/H._G._Wells",
                "https://fr.wikipedia.org/wiki/Stephen_King",
                "https://fr.wikipedia.org/wiki/Akira_Toriyama",
                "https://fr.wikipedia.org/wiki/Hayao_Miyazaki",
                "https://fr.wikipedia.org/wiki/Charles_Baudelaire",
                "https://fr.wikipedia.org/wiki/Arthur_Rimbaud",
                "https://fr.wikipedia.org/wiki/Marcel_Proust",
            ],
            "game_design_psychology_fr": [
                "https://fr.wikipedia.org/wiki/Théorie_des_jeux",
                "https://fr.wikipedia.org/wiki/Conception_de_jeux",
                "https://fr.wikipedia.org/wiki/Gameplay",
                "https://fr.wikipedia.org/wiki/Psychologie_du_joueur",
                "https://fr.wikipedia.org/wiki/Ludologie",
                "https://fr.wikipedia.org/wiki/Narration_ludique",
            ],
            "gaming_wikis_fr": [
                "https://leagueoflegends.fandom.com/fr/wiki/Accueil_Wiki_League_of_Legends",
                "https://minecraft.fandom.com/fr/wiki/Accueil",
                "https://wowhead.com/fr",
                "https://eldenring.fandom.com/fr/wiki/Wiki_Elden_Ring",
                "https://warhammer40k.fandom.com/fr/wiki/Accueil",
                "https://warhammer40k.fandom.com/fr/wiki/Imperium",
                "https://warhammer40k.fandom.com/fr/wiki/Empereur_de_l%27Humanité",
                "https://warhammer40k.fandom.com/fr/wiki/Primarque",
                "https://warhammer40k.fandom.com/fr/wiki/Space_Marines",
                "https://warhammer40k.fandom.com/fr/wiki/Hérésie_d'Horus",
                "https://warhammer40k.fandom.com/fr/wiki/Chaos_(Warhammer_40,000)",
                "https://fr.wikipedia.org/wiki/Dieux_du_Chaos",
                "https://fr.wikipedia.org/wiki/Aeldari",
                "https://fr.wikipedia.org/wiki/Nécrons",
                "https://fr.wikipedia.org/wiki/Orks_(Warhammer_40,000)",
                "https://fr.wikipedia.org/wiki/Tyranides",
                "https://fr.wikipedia.org/wiki/Empire_T'au",
                "https://fr.wikipedia.org/wiki/Univers_de_Dune",
                "https://dune.fandom.com/fr/wiki/Wiki_Dune",
                "https://fr.wikipedia.org/wiki/Mythe_de_Cthulhu",
                "https://fr.wikipedia.org/wiki/The_Witcher",
                "https://witcher.fandom.com/fr/wiki/Wiki_The_Witcher",
                "https://fr.wikipedia.org/wiki/Cyberpunk_2077",
                "https://cyberpunk.fandom.com/fr/wiki/Wiki_Cyberpunk",
                "https://fr.wikipedia.org/wiki/Univers_de_Star_Wars",
                "https://fr.wikipedia.org/wiki/Univers_étendu_de_Star_Wars",
                "https://fr.wikipedia.org/wiki/Univers_cinématographique_Marvel",
            ],
            "game_metadata_wikis": [
                "https://www.pcgamingwiki.com/wiki/Home", 
                "https://www.speedrun.com/games", 
                "https://fr.wikipedia.org/wiki/Portail:Jeu_vidéo/Liste_des_jeux",
                "https://fr.wikipedia.org/wiki/Liste_de_jeux_vidéo_par_genre",
            ],
            "human_interaction_art_fr": [
                "https://fr.wikipedia.org/wiki/Rhétorique",
                "https://fr.wikipedia.org/wiki/Humour",
                "https://fr.wikipedia.org/wiki/Sarcasme",
                "https://fr.wikipedia.org/wiki/Ironie",
                "https://fr.wikipedia.org/wiki/Improvisation_théâtrale",
                "https://fr.wikipedia.org/wiki/Charisme",
                "https://fr.wikipedia.org/wiki/Persuasion",
                "https://fr.wikipedia.org/wiki/Négociation",
                "https://fr.wikipedia.org/wiki/Art_oratoire",
            ],
            "sensory_experience_descr_fr": [
                "https://fr.wikipedia.org/wiki/Sens_(physiologie)",
                "https://fr.wikipedia.org/wiki/Goût",
                "https://fr.wikipedia.org/wiki/Odorat",
                "https://fr.wikipedia.org/wiki/Poésie",
                "https://fr.wikipedia.org/wiki/Critique_gastronomique",
                "https://fr.wikipedia.org/wiki/Synesthésie"
            ],
            "current_events_sources_fr": [
                "https://www.lemonde.fr/",
                "https://www.france24.com/fr/",
                "https://www.arte.tv/fr/actualites/",
                "https://fr.wikipedia.org/wiki/Portail:Actualit%C3%A9s"
            ],
            "applied_ethics_vulnerability_fr": [
                "https://fr.wikipedia.org/wiki/Dilemme_moral",
                "https://fr.wikipedia.org/wiki/Éthique_appliquée",
                "https://fr.wikipedia.org/wiki/Vulnérabilité_(psychologie)",
                "https://fr.wikipedia.org/wiki/Pardon",
                "https://fr.wikipedia.org/wiki/Erreur",
                "https://fr.wikipedia.org/wiki/Dilemme_du_tramway"
            ],
            "knowledge_creators_web": [
                "https://www.youtube.com/@Fireship/videos",
                "https://www.youtube.com/@TheCodingTrain/videos",
                "https://www.youtube.com/@freecodecamp/videos",
                "https://www.youtube.com/@LinusTechTips/videos",
                "https://www.youtube.com/@MKBHD/videos",
                "https://www.youtube.com/@TomScottGo/videos",
                "https://www.youtube.com/@BenEater/videos",
                "https://www.youtube.com/@DefendIntelligence/videos",
                "https://www.youtube.com/@Micode/videos",
                "https://www.youtube.com/@TraversyMedia/videos",
                "https://www.youtube.com/@WebDevSimplified/videos",
                "https://www.youtube.com/@TwoMinutePapers/videos",
                "https://www.youtube.com/@Veritasium/videos",
                "https://www.youtube.com/@smartereveryday/videos",
                "https://www.youtube.com/@MarkRober/videos",
                "https://www.youtube.com/@kurzgesagt/videos",
                "https://www.youtube.com/@lexfridman/videos",
                "https://www.youtube.com/@HubermanLab/videos",
                "https://www.youtube.com/@Vsauce/videos",
                "https://www.youtube.com/@SciShow/videos",
                "https://www.youtube.com/@MonsieurPhi/videos",
                "https://www.youtube.com/@DirtyBiology/videos",
                "https://www.youtube.com/@e-penser/videos",
                "https://www.youtube.com/@ScienceEtonnante/videos",
                "https://www.youtube.com/@BaladeMentale/videos",
                "https://www.youtube.com/@3blue1brown/videos",
                "https://www.youtube.com/@PhysicsGirl/videos",
                "https://www.youtube.com/@HealthyGamerGG/videos",
                "https://www.youtube.com/@exurb1a/videos",
                "https://www.youtube.com/@Einzelganger/videos",
                "https://www.youtube.com/@NotaBeneMovies/videos",
                "https://www.youtube.com/@CorridorCrew/videos",
                "https://www.youtube.com/@IanHubert/videos",
                "https://www.youtube.com/@HarvardBusinessReview/videos",
                "https://www.youtube.com/@TheEconomist/videos",
                "https://www.youtube.com/@GrahamStephan/videos",
                "https://www.youtube.com/@ThePlainBagel/videos",
                "https://www.youtube.com/@PatrickBoyleOnFinance/videos",
                "https://www.youtube.com/@samaltman/videos",
                "https://www.youtube.com/@georgehotz/videos",
                "https://www.youtube.com/@DrJordanBPeterson/videos",
                "https://www.youtube.com/@yudkowsky/videos",
                "https://www.youtube.com/@jonstewart/videos",
                "https://www.youtube.com/@LastWeekTonight/videos",
            ],
            "vtuber_streamer_analysis": [
                "https://www.youtube.com/@ironmouse/videos",
                "https://www.youtube.com/@shxtou/videos",
                "https://www.youtube.com/@kamet0/videos",
                "https://www.youtube.com/@Squeezie/videos",
                "https://www.youtube.com/@NicolasDelage/videos",
                "https://www.youtube.com/@-M-Matthieu" 
            ],
        }
        
        # Initialisation de l'API après toutes les initialisations
        self.API = self.KnowledgeAPI(self)

    def shutdown(self):
        """Méthode de fermeture (non essentielle ici pour une base en lecture seule)."""
        logger.info("Fermeture du module de connaissance statique.")
        # Le shutdown de la mémoire vectorielle est géré par la classe vectorielle elle-même
        if hasattr(self.knowledge_base, 'shutdown_memory'):
            self.knowledge_base.shutdown_memory()


    class KnowledgeAPI:
        """API publique du module ClioKnowledge."""
        def __init__(self, outer: 'ClioKnowledge'):
            self.outer = outer

        def search_knowledge(self, query: str, top_k: int = 5) -> List[Dict]:
            """
            Effectue une recherche RAG (Retrieval-Augmented Generation) 
            dans la base de connaissance statique (vectorielle).
            """
            if not self.outer.knowledge_base:
                logger.warning("[KNOWLEDGE] Base de connaissance non disponible.")
                return []
                
            if not isinstance(query, str) or not query.strip():
                logger.warning("Tentative de recherche de connaissance avec une requête vide ou non-texte.")
                return []
            
            # 🚀 AMÉLIORATION : Délégation de la recherche à l'objet ClioVectorMemory
            results = self.outer.knowledge_base.search_similar(query, top_k)
            logger.debug(f"Recherche de connaissance pour '{query[:30]}...' a retourné {len(results)} résultats.")
            return results

        def get_all_sources(self) -> Dict[str, List[str]]:
            """Retourne toutes les sources définies par catégorie."""
            return self.outer.sources

        def get_sources_by_category(self, category_key: str) -> List[str]:
            """Retourne les sources pour une catégorie spécifique."""
            return self.outer.sources.get(category_key, [])