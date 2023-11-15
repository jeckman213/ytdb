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
        
    def _can_play(self, queue_item) -> bool:
        if "channel" in queue_item and "download_data" in queue_item and "file" in queue_item["download_data"]:
            return True
        
        return False
        
    def add(self, url, context, channel, download_data):
        self.queue.append({
            "url": url,
            "context": context,
            "channel": channel,
            "download_data": download_data
        })
        
    def skip(self):
        self.skip_song = True
    
    async def start(self):
        self.is_playing = True
        self.is_stopping = False
        
        while len(self.queue) != 0:            
            next_video = self.queue[0]
            if self._can_play(next_video):
                await self.playAndPop(next_video)
        
        self.is_playing = False
        
    async def stop(self):
        self.queue = []
        self.is_stopping = True
        self.is_playing = False
        self.skip_song = True
        
        
    async def playAndPop(self, play_info):
        # Safe guard just incase something happens to the file
        file = play_info["download_data"]["file"]
        if not os.path.exists(file):
            download_data = await download(play_info["url"])
            file = download_data["file"]
        
        # Channel connect and Source creation
        vc = await play_info["channel"].connect()
        source = discord.FFmpegPCMAudio(file)
        
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
            files = [item["download_data"]["file"] for item in self.queue if self._can_play(item)]
            if not file in files:
                os.remove(file)
            
            await vc.disconnect()

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
ENV = os.getenv("ENV", "dev")

intents = discord.Intents.default()
intents.message_content = True

command_prefix = "!steve "
if ENV == "dev":
    command_prefix = "!dsteve "

bot = commands.Bot(command_prefix=command_prefix, intents=intents, activity=discord.Game("some music!"))
player = YoutubeDiscordPlayer(bot)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    

@bot.command(name="play")
async def play(context, url: str, *, channel_name: commands.clean_content = None):
    try:
        if channel_name == None:
            channel = context.author.voice.channel
        else:
            channels = context.guild.channels
            channel = next(c for c in channels if c.name == channel_name and isinstance(c, discord.VoiceChannel))
    except:
        embed = discord.Embed(title="Failed to add to queue")
        embed.set_author(name=context.author.display_name, icon_url=context.author.display_avatar.url)
        embed.add_field(name="Failure", value="Either join a channel or specify one after the url...")
        await context.send(embed=embed)
        return
    
    download_data = await download(url)
    
    embed = discord.Embed(title="Adding to queue")
    embed.set_author(name=context.author.display_name, icon_url=context.author.display_avatar.url)
    embed.add_field(name=download_data["title"], value=url)
    await context.send(embed=embed)
    
    player.add(url, context, channel, download_data)
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
    # urls = [item["url"] for item in player.queue]
    embed = discord.Embed(title="Queue")
    
    if len(player.queue) == 0:
        embed.add_field(name="Empty", value="No items in queue")
    else:
        for item in player.queue:
            embed.add_field(name=item["download_data"]["title"], value=f"{item["url"]} requested by {item["context"].author.display_name}", inline=False)
    
    await context.send(embed=embed)

if __name__ == "__main__":
    bot.run(TOKEN)
