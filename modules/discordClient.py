import os
import asyncio
from dotenv import load_dotenv
import discord
from modules.module import Module
from streamingSink import StreamingSink
from typing import Optional, Dict, Any, List

# --- CONFIGURATION UTILISATEUR ---
# 1. Colle ton token entre les guillemets ci-dessous
# 🚨 ATTENTION : Laisser vide si tu utilises DISCORD_TOKEN dans .env
HARDCODED_TOKEN = "MTQ0MTQxNDExMDY1NzkwNDY1MA.GE-Zsx._yNDkTq64gAgh30EPYOFi9Z4EJ4nmcF6JSbhgU"

# 2. ID du SALON VOCAL pour la connexion automatique (Taverne tchat vocale)
# L'erreur 403 est souvent due à un problème de permissions (vérifier Discord).
TARGET_VOICE_CHANNEL_ID = 1145339731475955785 

# 3. ID du SALON TEXTE par défaut (Taverne tchat écrit)
# Utilisé par l'API pour envoyer des messages du bot.
DEFAULT_TEXT_CHANNEL_ID = 1145339731475955784
# ---------------------------------

class DiscordClient(Module):

    # --- API (Pour que les autres modules interagissent) ---
    class API:
        def __init__(self, outer: 'DiscordClient'):
            self.outer = outer

        def get_discord_status(self):
            return self.outer.enabled

        def send_text_to_channel(self, message: str, channel_id: Optional[int] = None):
            """Envoie un message texte à un canal donné (thread-safe)."""
            
            # Utilise l'ID par défaut si aucun n'est spécifié
            target_id = channel_id if channel_id is not None else self.outer.DEFAULT_TEXT_CHANNEL_ID

            async def send_message_task():
                if not self.outer.bot.is_ready():
                    return
                
                try:
                    text_channel = self.outer.bot.get_channel(target_id)
                    
                    if text_channel and isinstance(text_channel, discord.TextChannel):
                        await text_channel.send(message)
                    else:
                        # Si le canal n'est pas trouvé ou n'est pas un salon texte
                        print(f"DISCORD API ERROR: Salon texte ID {target_id} non trouvé ou invalide.")

                except Exception as e:
                    print(f"DISCORD API ERROR: Échec envoi texte: {e}")
                    
            # Exécute la tâche dans la boucle événementielle du bot
            if self.outer.bot.loop:
                asyncio.run_coroutine_threadsafe(send_message_task(), self.outer.bot.loop)
            else:
                print("DISCORD API ERROR: Boucle bot indisponible.")


    def __init__(self, signals, stt, enabled=True):
        super().__init__(signals, enabled)
        self.stt = stt
        
        # Configuration des IDs directement dans la classe pour l'API
        self.TARGET_VOICE_CHANNEL_ID = TARGET_VOICE_CHANNEL_ID
        self.DEFAULT_TEXT_CHANNEL_ID = DEFAULT_TEXT_CHANNEL_ID

        intents = discord.Intents.default()
        intents.members = True
        intents.voice_states = True
        intents.message_content = True

        self.bot = discord.Bot(intents=intents)
        self.connections: Dict[int, discord.VoiceClient] = {}
        self.API = self.API(self)
        
        # 🚨 NOUVEAU DRAPEAU : Évite de retenter la connexion vocale après un échec au démarrage
        self.voice_connect_attempted = False

    async def _auto_connect_to_voice(self):
        """Tente de se connecter au salon vocal cible."""
        if self.voice_connect_attempted:
            print("DISCORD: Tentative de connexion vocale déjà effectuée (attente).")
            return

        self.voice_connect_attempted = True
        
        channel_id = self.TARGET_VOICE_CHANNEL_ID

        if channel_id == 0 or channel_id == 123456789012345678: 
            return # ID non configuré

        # Petite pause pour laisser le temps au cache de charger
        await asyncio.sleep(2)

        try:
            print(f"DISCORD: Recherche du salon {channel_id}...")
            # Utilisation de get_channel (plus rapide si le cache est à jour)
            channel = self.bot.get_channel(channel_id)
            
            # Si get_channel échoue, on essaie fetch_channel
            if not channel:
                 channel = await self.bot.fetch_channel(channel_id)

            if channel and isinstance(channel, discord.VoiceChannel):
                print(f"DISCORD: Tentative de connexion auto à {channel.name}...")
                
                # 🚨 IMPORTANT : On se déconnecte avant de retenter pour éviter un spam de requêtes de connexion
                if self.connections.get(channel.guild.id):
                    await self.connections[channel.guild.id].disconnect()

                vc = await channel.connect()
                self.connections[channel.guild.id] = vc
                print(f"DISCORD: Connecté avec succès à {channel.name} !")
                
                # 💡 Démarrer l'enregistrement ici
                vc.start_recording(StreamingSink(self.signals, self.stt), self.finished_callback, channel)
                return # Succès
                
            else:
                print(f"DISCORD: L'ID {channel_id} n'est pas un salon vocal valide ou est introuvable.")
        except discord.Forbidden:
             # Attrape spécifiquement l'erreur 403 Forbidden
             print(f"DISCORD: Impossible de se connecter au salon {channel_id} : 403 Forbidden (Vérifiez les permissions du bot !)")
        except Exception as e:
            print(f"DISCORD: Impossible de se connecter au salon {channel_id} : {e}")
            
        print("DISCORD: Échec de la connexion vocale au salon cible.")


    async def run(self):
        # 1. Gestion du Token
        load_dotenv()
        token = HARDCODED_TOKEN if HARDCODED_TOKEN else os.getenv('DISCORD_TOKEN')

        if not token:
            print("DISCORD ERROR: Token manquant. Module désactivé.")
            self.enabled = False
            return
            
        bot = self.bot
        
        # --- ÉVÉNEMENTS ---
        @bot.event
        async def on_ready():
            print(f"DISCORD: Bot {bot.user} est en ligne (Clio).")
            self.signals.sio_queue.put(('discord_status', True))
            
            # Tente de se connecter au salon vocal UNE SEULE FOIS au démarrage
            await self._auto_connect_to_voice()

        @bot.slash_command(name="ping", description="Vérifier le statut")
        async def ping(ctx):
            await ctx.respond(f"Pong! Latence: {bot.latency*1000:.2f}ms")

        # 🚨 FONCTION DE CALLBACK DE FIN D'ENREGISTREMENT
        self.finished_callback = self._finished_callback
        
        # --- COMMANDES VOCALES ---
        @bot.slash_command(name="start", description="Clio rejoint le vocal et écoute")
        async def start(ctx: discord.ApplicationContext):
            voice = ctx.author.voice
            if not voice:
                return await ctx.respond("Tu n'es pas dans un salon vocal.", ephemeral=True)
            if ctx.guild.id in self.connections:
                return await ctx.respond("Je suis déjà connectée ici.", ephemeral=True)

            try:
                vc = await voice.channel.connect()
                self.connections[ctx.guild.id] = vc
                vc.start_recording(
                    StreamingSink(self.signals, self.stt),
                    self.finished_callback,
                    ctx.channel,
                )
                await ctx.respond("Clio t'écoute.", ephemeral=True)
            except discord.Forbidden:
                 await ctx.respond("Erreur de permission : Clio n'a pas accès à ce salon vocal.", ephemeral=True)
            except Exception as e:
                print(f"DISCORD ERROR: {e}")
                await ctx.respond("Erreur de connexion.", ephemeral=True)
                if ctx.guild.id in self.connections: del self.connections[ctx.guild.id]

        @bot.slash_command(name="stop", description="Clio arrête d'écouter")
        async def stop(ctx: discord.ApplicationContext):
            if ctx.guild.id in self.connections:
                vc = self.connections[ctx.guild.id]
                vc.stop_recording()
                # La déconnexion est gérée par le callback après l'arrêt de l'enregistrement
                await ctx.respond("Arrêt de l'écoute.", ephemeral=True)
            else:
                await ctx.respond("Rien à arrêter.", ephemeral=True)

        # --- GESTION DU DÉMARRAGE ET DE LA RECONNEXION ---
        try:
            print("DISCORD: Tentative de connexion du bot...")
            # 🚨 Utilisation de bot.start (non bloquant)
            await bot.start(token)
        except Exception as e:
            # Cette erreur est souvent liée au token ou à la connexion initiale
            print(f"ERREUR CRITIQUE DISCORD: Échec de la boucle principale du bot : {e}")
            self.enabled = False
        finally:
            # Ne pas appeler bot.close si le bot n'a jamais démarré, mais le faire si le signal terminate est là.
            if self.bot.is_ready() and self.signals.terminate:
                await self.bot.close()
        
    async def _finished_callback(self, sink, channel: discord.TextChannel, *args):
        """Callback appelé après l'arrêt de l'enregistrement."""
        print("DISCORD: Enregistrement terminé, déconnexion du salon.")
        
        if sink.vc and sink.vc.guild.id in self.connections:
            guild_id = sink.vc.guild.id
            
            if sink.vc.is_connected():
                await sink.vc.disconnect()
            
            del self.connections[guild_id]
            
            # Utilise l'API interne pour envoyer le message de fin dans le salon texte par défaut
            self.API.send_text_to_channel("Clio est de retour en veille après l'enregistrement.")