const mineflayer = require('mineflayer')
const pathfinder_pkg = require('mineflayer-pathfinder')
const collectblock_pkg = require('mineflayer-collectblock')
const tool_pkg = require('mineflayer-tool')
const pvp_pkg = require('mineflayer-pvp')
const websockets = require('ws') // Utilisation de la librairie 'ws' côté Node.js
const { Vec3 } = require('vec3')

// --- CONFIGURATION ---
const MAMAN_PSEUDO = "MrsXar" // Ton pseudo exact dans le jeu
const TARGET_PLAYER = "MrsXar" 
const MC_HOST = "localhost"
const MC_PORT = 27117
const BRIDGE_PORT = 8000 // Port de communication avec NeuroClient.py

console.log(`⚡ Démarrage du Système Nerveux Clio (V9 Warrior) sur le port ${BRIDGE_PORT}...`)

// --- Initialisation Mineflayer ---
const bot = mineflayer.createBot({
    host: MC_HOST, port: MC_PORT, username: 'Clio_AI', version: false // Nom d'utilisateur unique pour Clio
})

// Chargement des plugins
try {
    bot.loadPlugin(pathfinder_pkg.pathfinder)
    bot.loadPlugin(collectblock_pkg.plugin)
    bot.loadPlugin(tool_pkg.plugin)
    bot.loadPlugin(pvp_pkg.plugin)
    console.log("✅ Compétences : Navigation, Minage, Outils, PVP ACTIVÉS")
} catch (e) { console.error(`⚠️ Erreur plugins: ${e}`) }

const Movements = pathfinder_pkg.Movements
const goals = pathfinder_pkg.goals
let brain_socket = null // Connexion WS active
let MAIN_LOOP = null // Pour les opérations asynchrones

// --- FONCTIONS DE COMMUNICATION ---

async function _async_report(type, data, emotion = "neutral") {
    // 🚀 AMÉLIORATION : Envoie un objet de contexte structuré
    if (brain_socket && brain_socket.readyState === websockets.OPEN) {
        try { 
            await brain_socket.send(JSON.stringify({
                command: 'context', 
                context: {
                    type: type, 
                    content: data, 
                    emotion: emotion, 
                    bot_health: bot.health,
                    bot_food: bot.food,
                    bot_pos: bot.entity ? [bot.entity.position.x, bot.entity.position.y, bot.entity.position.z] : null
                }
            }));
        } catch (e) { 
            console.error(`[WS] Erreur envoi: ${e.message}`);
        }
    } else { 
        console.log(`💭 [BUFFER] [${type}] ${data}`);
    }
}

function report_to_brain(type, data, emotion = "neutral") {
    // Exécute la fonction asynchrone dans le thread Node.js
    _async_report(type, data, emotion);
}

// --- LOGIQUE D'ACTION DU JEU ---

function fight_hostile(entity) {
    if (!entity) return;
    report_to_brain("action_status", `Je me défends contre ${entity.name} !`, "angry");
    bot.pvp.attack(entity);
}

function find_and_mine(block_keyword) {
    console.log(`Action: Recherche de '${block_keyword}'`);
    const translations = {"fer": "iron_ore", "charbon": "coal_ore", "pierre": "stone", "bois": ["oak_log", "birch_log"], "terre": "dirt"};
    const targets = translations[block_keyword] || [block_keyword];
    
    // Convertir les noms en IDs
    const target_ids = targets.flatMap(n => bot.registry.blocksByName[n] ? [bot.registry.blocksByName[n].id] : []);
    if (target_ids.length === 0) return report_to_brain("action_status", `Je ne connais pas ${block_keyword}.`);

    const blocks = bot.findBlocks({ matching: target_ids, maxDistance: 64, count: 1 });
    if (blocks.length === 0) return report_to_brain("action_status", `Pas de ${block_keyword} ici.`, "sad");

    report_to_brain("action_status", `Je vais miner du ${block_keyword}.`, "happy");
    try { 
        // 🚨 IMPORTANT : utilise collectBlock pour un minage intelligent (avec pathfinding)
        bot.collectBlock.collect(bot.blockAt(blocks[0]), { ignoreNoPath: true });
    } catch { 
        report_to_brain("action_status", "Je ne peux pas l'atteindre.", "sad");
    }
}

function follow_human() {
    const target = bot.players[TARGET_PLAYER];
    if (!target || !target.entity) return report_to_brain("action_status", "Maman, je ne te vois pas !", "surprised");
    try {
        const move = new Movements(bot);
        move.canDig = false; 
        bot.pathfinder.setMovements(move);
        bot.pathfinder.setGoal(new goals.GoalFollow(target.entity, 1), true);
        report_to_brain("action_status", "Je te suis !", "happy");
    } catch (e) { console.error(`Erreur follow: ${e.message}`); }
}

function stop_everything() {
    try {
        bot.pathfinder.setGoal(null);
        bot.pvp.stop();
        // 🚀 AMÉLIORATION : Relâche les touches
        bot.clearControlStates(); 
        report_to_brain("action_status", "Je m'arrête.", "neutral");
    } catch (e) { console.error(`Erreur stop: ${e.message}`); }
}


// --- 🚀 NOUVELLE FONCTION : GESTION DES ACTIONS PYTHON (Bridge) ---
function handle_python_action(action_name) {
    // Implémente la logique de délégation envoyée par le BrainModule Python
    switch (action_name.toUpperCase()) {
        case 'FOLLOW':
        case 'SUIVRE':
            follow_human();
            break;
        case 'STOP':
        case 'ARRÊT':
            stop_everything();
            break;
        // Ajoutez ici les actions complexes de votre BrainModule
        case 'MINE_WOOD':
            find_and_mine("bois");
            break;
        // Laisser les autres actions (JUMP, ATTACK, etc.) au LLM pour la délégation directe si Mineflayer n'a pas besoin de pathfinding complexe
        default:
            report_to_brain("action_status", `Commande Python inconnue: ${action_name}.`, "sad");
            break;
    }
}

// --- GESTION DES ÉVÉNEMENTS MINECRAFT ---

bot.on('spawn', () => {
    console.log("🟢 CLIO EST EN VIE.");
    report_to_brain("status", "Le bot est apparu dans le monde.", "happy");
});

bot.on('damages', () => {
    report_to_brain("status", "Aïe ! On m'attaque !", "fear");
    const target = bot.nearestEntity(e => e.type === 'mob' && e.kind === 'Hostile');
    if (target) fight_hostile(target);
});

bot.on('chat', (username, message) => {
    if (username === bot.username) return;
    console.log(`💬 ${username}: ${message}`);
    
    // 🚀 AMÉLIORATION : Envoi du chat au NeuroClient Python pour l'analyse LLM
    if (brain_socket) {
        report_to_brain("chat_message", `${username}: ${message}`);
    }

    // Réflexes de base si Maman parle
    const msg = message.toLowerCase();
    if (username === TARGET_PLAYER) {
         if (msg.includes("viens")) follow_human();
         else if (msg.includes("stop")) stop_everything();
         else if (msg.includes("mine") || msg.includes("coupe")) {
             if (msg.includes("bois")) find_and_mine("bois");
             else if (msg.includes("fer")) find_and_mine("fer");
         }
    }
});

// Envoi régulier de l'état du jeu (pourrait être utilisé pour le contexte NeuroClient)
bot.on('physicTick', () => {
    const target = bot.players[TARGET_PLAYER];
    if (target && target.entity) {
        bot.lookAt(target.entity.position.offset(0, target.entity.height, 0));
        
        // Exemple d'envoi du contexte de jeu toutes les 20 tiques (1s)
        if (bot.ticks % 20 === 0) {
             const botPos = bot.entity.position;
             const targetPos = target.entity.position;

             report_to_brain("gamestate", {
                distance_to_player: botPos.distanceTo(targetPos).toFixed(2), 
                health: bot.health,
                food: bot.food,
                time: bot.time.timeOfDay,
                is_day: bot.time.timeOfDay < 12500,
                // Le NeuroClient Python interprétera ce dictionnaire
            });
        }
    }
});

// --- SERVEUR WEB SOCKET POUR PYTHON (NeuroClient) ---
async function startWsServer() {
    const wsServer = new websockets.Server({ port: BRIDGE_PORT });
    console.log(`📡 Serveur WS Mineflayer démarré sur le port ${BRIDGE_PORT}. En attente de NeuroClient.py...`);
    
    wsServer.on('connection', (ws) => {
        brain_socket = ws;
        console.log("✅ CERVEAU PYTHON CONNECTÉ (NeuroClient)");

        // Événement déclenché à la réception d'une action du BrainModule Python
        ws.on('message', (message) => {
            try {
                const data = JSON.parse(message);
                if (data.command === 'action') {
                    // C'est l'appel du BrainModule (ex: send_game_action('MINE_WOOD'))
                    handle_python_action(data.data); 
                } else if (data.command === 'startup') {
                    // NeuroClient vient de se connecter
                    report_to_brain("status", "Connexion établie avec le cerveau Python.", "gentle");
                }
            } catch (e) {
                console.error(`[WS] Erreur traitement message: ${e.message}`);
            }
        });

        ws.on('close', () => {
            brain_socket = null;
            console.log("🔌 Déconnecté du cerveau Python.");
        });
    });
}


// --- DÉMARRAGE FINAL ---

// Mineflayer ne peut pas s'exécuter directement dans un contexte asyncio Python.
// Nous utilisons un wrapper pour lancer le serveur WS dans Node.js/JavaScript.
if (require.main === module) {
    // Utilisation d'un thread Node.js pour lancer le serveur WS
    startWsServer();
    // Le bot.on('end') gère les reconnexions du bot Minecraft.
}