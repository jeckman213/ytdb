"""Discord bot main script
"""

import os

import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from youtube import download


class YoutubeDiscordPlayer:
    """Class for keeping track of youtube music/sound queue"""

    def __init__(self):
        self.queue = []
        self.is_playing = False
        self.is_stopping = False
        self.skip_song = False

    def _can_play(self, queue_item) -> bool:
        if (
            "channel" in queue_item
            and "download_data" in queue_item
            and "file" in queue_item["download_data"]
        ):
            return True

        return False

    def add(self, url, context, channel, download_data):
        """Add song to queue

        Args:
            url (str): The url of the youtube video
            context (_type_): Discord context
            channel (_type_): Discord channel object
            download_data (_type_): Data that came from the youtube download
        """
        self.queue.append(
            {
                "url": url,
                "context": context,
                "channel": channel,
                "download_data": download_data,
            }
        )

    def skip(self):
        """Sets skip_song which gets checked while song is running"""
        self.skip_song = True

    async def start(self):
        """Starts playing from the queue. Ends once the queue is empty"""
        self.is_playing = True
        self.is_stopping = False

        while len(self.queue) != 0:
            next_video = self.queue[0]
            if self._can_play(next_video):
                await self.play_and_pop(next_video)

        self.is_playing = False

    async def stop(self):
        """Stops the queue and resets"""
        self.queue = []
        self.is_stopping = True
        self.is_playing = False
        self.skip_song = True

    async def play_and_pop(self, play_info):
        """Plays audio file from play_info and then removes from the queue

        Args:
            play_info (dict): Dictionary holding information about what to play
        """
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
            files = [
                item["download_data"]["file"]
                for item in self.queue
                if self._can_play(item)
            ]
            if not file in files:
                os.remove(file)

            await vc.disconnect()


class YoutubeCommands(commands.Cog):
    """Youtube Bot Cog

    Args:
        commands (_type_): Cog base class
    """

    def __init__(
        self, bot: commands.Bot, environment: str
    ):
        self.bot = bot
        self.players = {}
        self.environment = environment

    @commands.command(
        name="play",
        help="Play Youtube audio through url and optional target channel",
        usage="!steve play <url> <target_channel?>",
    )
    async def play(
        self, context, url: str, *, channel_name: commands.clean_content = None
    ):
        """
        1. Determines channel to play audio in
        2. Downloads sound from youtube video
        3. Adds to player queue
        4?. Starts player queue if its not playing

        Args:
            context (_type_): Discord context
            url (str): Url to youtube video
            channel_name (commands.clean_content, optional):
                The name of the target channel to play audio in. Defaults to None.
        """
        guild_id = context.author.guild.id
        
        try:
            if channel_name is None:
                channel = context.author.voice.channel
            else:
                channels = context.guild.channels
                channel = next(
                    c
                    for c in channels
                    if c.name == channel_name and isinstance(c, discord.VoiceChannel)
                )
        except Exception as e:
            print(e)
            embed = discord.Embed(title="Failed to add to queue")
            embed.set_author(
                name=context.author.display_name,
                icon_url=context.author.display_avatar.url,
            )
            embed.add_field(
                name="Failure",
                value="Either join a channel or specify one after the url...",
            )
            await context.send(embed=embed)
            return

        download_data = await download(url, str(guild_id))

        embed = discord.Embed(title="Adding to queue")
        embed.set_author(
            name=context.author.display_name, icon_url=context.author.display_avatar.url
        )
        embed.add_field(name=download_data["title"], value=download_data["url"])
        await context.send(embed=embed)

        if guild_id not in self.players:
            self.players[guild_id] = YoutubeDiscordPlayer()

        self.players[guild_id].add(download_data["url"], context, channel, download_data)
        if not self.players[guild_id].is_playing:
            await self.players[guild_id].start()

    @commands.command(name="stop", help="Stops steve completely and clears queue")
    async def stop(self, context):
        """Stops all and clears queue

        Args:
            context (_type_): Discord context
        """
        embed = discord.Embed(title="Stopping Queue")
        embed.set_author(
            name=context.author.display_name, icon_url=context.author.display_avatar.url
        )
        await context.send(embed=embed)

        guild_id = context.author.guild.id
        if guild_id in self.players:
            await self.players[guild_id].stop()

    @commands.command(name="skip", help="Skips current audio")
    async def skip(self, context):
        """Skips current audio playing in the queue

        Args:
            context (_type_): Discord context
        """
        guild_id = context.author.guild.id
        
        if guild_id not in self.players or len(self.players[guild_id].queue) == 0:
            await context.send("Nothing to skip :D")
            return

        current = self.players[guild_id].queue[0]
        context = current["context"]
        download_data = current["download_data"]
        url = current["url"]

        embed = discord.Embed(title="Skipping")
        embed.set_author(
            name=context.author.display_name, icon_url=context.author.display_avatar.url
        )
        embed.add_field(name=download_data["title"], value=url)
        await context.send(embed=embed)

        self.players[guild_id].skip()

    @commands.command(name="queue", help="Shows current youtube queue")
    async def queue(self, context: commands.Context):
        """Gets current queue

        Args:
            context (_type_): Discord context
        """
        guild_id = context.author.guild.id
        
        if guild_id not in self.players or len(self.players[guild_id].queue) == 0:
            embed = discord.Embed(title="Queue")
            embed.add_field(name="Empty", value="No items in queue")
            await context.send(embed=embed)
        else:
            for index, item in enumerate(self.players[guild_id].queue):
                embed = discord.Embed(title=f"Queue Item {index}")
                embed.set_author(
                    name=context.author.display_name,
                    icon_url=context.author.display_avatar.url,
                )
                embed.add_field(
                    name="Title", value=item["download_data"]["title"], inline=False
                )
                embed.add_field(name="Url", value=item["url"], inline=False)
                embed.add_field(
                    name="Voice Channel",
                    value="`{channel}`".format(channel=item["channel"].name),
                )
                await context.send(embed=embed)


if __name__ == "__main__":
    # Get envs
    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")
    ENV = os.getenv("ENV", "dev")

    # Create Intents for bot
    intents = discord.Intents.default()
    intents.message_content = True

    # Determine command prefix based on ENV
    COMMAND_PREFIX = "!steve "
    if ENV == "dev":
        COMMAND_PREFIX = "!dsteve "

    # Create bot
    main_bot = commands.Bot(
        command_prefix=COMMAND_PREFIX,
        intents=intents,
        activity=discord.Game("some music!"),
    )
    # Create cog(s)
    cog = YoutubeCommands(main_bot, ENV)

    # Add cog(s)
    asyncio.run(main_bot.add_cog(cog))

    @main_bot.event
    async def on_ready():
        """On Ready for bot"""
        print(f"{main_bot.user} has connected to Discord!")

    main_bot.run(TOKEN)
