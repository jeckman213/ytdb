import os
import json

import discord
from discord.ext import commands
from dotenv import load_dotenv
from youtube import download
import asyncio

class YoutubeDiscordPlayer:
    def __init__(self, bot):
        self.queue = []
        self.is_playing = False
        self.is_stopping = False
        self.skip_song = False
        
    def add(self, url, context, channel, file):
        self.queue.append({
            "url": url,
            "context": context,
            "channel": channel,
            "file": file
        })
        
    def skip(self):
        self.skip_song = True
    
    async def start(self):
        self.is_playing = True
        self.is_stopping = False
        
        while len(self.queue) != 0:            
            next_video = self.queue[0]
            if "channel" not in next_video and "file" not in next_video:
                continue
            
            await self.playAndPop(next_video)
        
        self.is_playing = False
        
    async def stop(self):
        self.queue = []
        self.is_stopping = True
        self.is_playing = False
        self.skip_song = True
        
        
    async def playAndPop(self, play_info):
        # Safe guard just incase something happens to the file
        if not os.path.exists(play_info["file"]):
            await download(play_info["url"])
        
        # Channel connect and Source creation
        vc = await play_info["channel"].connect()
        source = discord.FFmpegPCMAudio(play_info["file"])
        
        # PLAY
        try:
            vc.play(source)
            while vc.is_playing():
                if self.skip_song:
                    vc.stop()
                    self.skip_song = False
                await asyncio.sleep(1.0)
        except Exception as e:
            print(e)
        finally:
            if not self.is_stopping:
                self.queue.pop(0)
            
            # Only remove files that aren't in the queue for future use
            files = [item["file"] for item in self.queue]
            if not play_info["file"] in files:
                os.remove(play_info["file"])
            
            await vc.disconnect()

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!steve ", intents=intents, activity=discord.Game("some music!"))
player = YoutubeDiscordPlayer(bot)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    

@bot.command(name="play")
async def play(context, url: str):
    try:
        channel = context.author.voice.channel
    except:
        await context.send("you are not currently in a voice channel")
        return
    
    file = await download(url)
    
    await context.send(f"Adding video: {url} to the queue")
    
    player.add(url, context, channel, file)
    if not player.is_playing:
        await player.start()
        
@bot.command(name="playInChannel")
async def play_in_channel(context, url: str, *, channel_name: commands.clean_content):
    try:
        print(channel_name)
        channels = context.guild.channels
        print([c.name for c in channels])
        channel = next(c for c in channels if c.name == channel_name and isinstance(c, discord.VoiceChannel))
    except:
        await context.send(f"Could not find channel {channel_name}")
        return
    
    file = await download(url)
    
    await context.send(f"Adding video: {url} to the queue")
    
    player.add(url, context, channel, file)
    if not player.is_playing:
        await player.start()
        
@bot.command(name="stop")
async def stop(context):
    await context.send("Stopping...")
    await player.stop()

@bot.command(name="skip")
async def skip(context):
    await context.send("Skipping...")
    player.skip()
        
@bot.command(name="queue")
async def queue(context):
    urls = [item["url"] for item in player.queue]
    await context.send(f"Current Queue: {json.dumps(urls, indent=4)}")

if __name__ == "__main__":
    bot.run(TOKEN)
