const mineflayer = require('mineflayer');
const WebSocket = require('ws'); // Nécessite npm install ws
const { Vec3 } = require('vec3');

// --- CONFIGURATION ---
const MAMAN_PSEUDO = "MrsXar"; // Remplacer par votre pseudo exact en jeu
const SERVER_HOST = "localhost";
const SERVER_PORT = 27117;
const WS_SERVER_URL = "ws://localhost:8000"; // Doit correspondre à NeuroClient.py

// --- ÉTAT GLOBAL ET CONNEXION WS ---
let ws;
let wsConnected = false;
let gameGoal = null; // Objectif donné par l'IA Python

function connectWebSocket() {
    console.log(`[WS] Tentative de connexion au cerveau sur ${WS_SERVER_URL}...`);
    ws = new WebSocket(WS_SERVER_URL);

    ws.on('open', () => {
        wsConnected = true;
        console.log('[WS] Connecté au NeuroClient Python.');
        // Envoi du signal de démarrage (similaire à NeuroClient.py)
        ws.send(JSON.stringify({ command: 'startup', game: 'Minecraft_Mineflayer' }));
    });

    ws.on('message', (data) => {
        const message = JSON.parse(data);
        if (message.command === 'action') {
            handleActionFromPython(message.data);
        } else if (message.command === 'set_goal') {
            gameGoal = message.data;
            bot.chat(`[IA] Objectif mis à jour : ${gameGoal}`);
        }
    });

    ws.on('close', () => {
        wsConnected = false;
        console.log('[WS] Déconnecté du NeuroClient Python. Tentative de reconnexion dans 5s...');
        setTimeout(connectWebSocket, 5000); // Tentative de reconnexion
    });

    ws.on('error', (err) => {
        console.error(`[WS] Erreur : ${err.message}`);
        // La tentative de reconnexion est gérée par l'événement 'close'
    });
}

// Lancement de la connexion WebSocket au démarrage
connectWebSocket();


// --- CRÉATION DU BOT MINECRAFT ---
const bot = mineflayer.createBot({
    host: SERVER_HOST,
    port: SERVER_PORT,
    username: 'Clio_AI',
    version: false 
});

console.log(`Tentative de connexion au monde sur ${SERVER_HOST}:${SERVER_PORT}...`);


// --- FONCTIONS D'ACTION DU JEU (Réponses aux commandes Python) ---

function handleActionFromPython(action) {
    console.log(`[ACTION] Commande reçue : ${action}`);
    switch (action.toUpperCase()) {
        case 'JUMP':
            bot.setControlState('jump', true);
            bot.setControlState('jump', false);
            bot.chat("Hop ! (Commande Python)");
            break;
        case 'FOLLOW_MAMAN':
            // Ici, vous intégreriez un pathfinder (Mineflayer n'a pas cette fonction par défaut)
            // bot.pathfinder.goto(bot.players[MAMAN_PSEUDO].entity.position);
            bot.chat("Je commence à te suivre ! (Pathfinder non implémenté)");
            break;
        case 'STOP':
            bot.clearControlStates();
            bot.chat("Je m'arrête.");
            break;
        default:
            // Peut être une commande de chat directe non reconnue comme action
            bot.chat(`[Action Inconnue] Je ne peux pas faire "${action}", mais merci de l'ordre !`);
            break;
    }
}


// --- GESTION DES ÉVÉNEMENTS MINECRAFT ---

bot.on('spawn', () => {
    console.log("Je suis apparue dans le monde !");
    bot.chat(`Bonjour ${MAMAN_PSEUDO} ! Je suis connectée à mon cerveau Python.`);
});

bot.on('chat', (username, message) => {
    if (username === bot.username) return; 

    // 🚀 ENVOI DU CHAT À PYTHON via WebSocket
    if (wsConnected) {
        ws.send(JSON.stringify({ 
            command: 'context', 
            // On peut envoyer un objet complexe pour l'analyse
            context: {
                type: 'chat',
                sender: username,
                text: message
            } 
        }));
    }
    
    // Répétition de la logique de base si MAMAN parle
    if (username === MAMAN_PSEUDO) {
        if (message.toLowerCase().includes("saute")) {
             // On utilise la fonction d'action pour la cohérence
             handleActionFromPython('JUMP');
        }
    }
});

// 🚀 ENVOI RÉGULIER DE L'ÉTAT DU JEU (20 fois par seconde)
bot.on('physicTick', () => {
    const target = bot.players[MAMAN_PSEUDO];
    
    if (target && target.entity) {
        // 1. Regarder Maman
        bot.lookAt(target.entity.position.offset(0, target.entity.height, 0));
        
        // 2. ENVOI DE L'ÉTAT DU JEU à PYTHON toutes les 5 tiques (0.25s)
        if (bot.ticks % 5 === 0 && wsConnected) {
            const botPos = bot.entity.position;
            const targetPos = target.entity.position;
            
            ws.send(JSON.stringify({
                command: 'context',
                context: {
                    type: 'gamestate',
                    player_name: MAMAN_PSEUDO,
                    // Distance est un indicateur clé de Warframe/MMO
                    distance_to_player: botPos.distanceTo(targetPos).toFixed(2), 
                    health: bot.health,
                    food: bot.food,
                    game_time: bot.time.timeOfDay,
                    current_goal: gameGoal
                }
            }));
        }
    }
});

bot.on('end', (reason) => {
    console.log(`Déconnecté du monde : ${reason}`);
    // Tente de reconnecter le bot Minecraft après un court délai
    // (Cette logique doit être gérée par un système de redémarrage externe pour la production)
});

// Le Mineflayer est asynchrone, donc le process reste en vie tant que le bot est connecté.
// Le `while True` en JavaScript n'est pas nécessaire ici.