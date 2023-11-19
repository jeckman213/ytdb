"""Discord-Youtube player and discord bot cog housing script
"""

import os

import asyncio
import discord
from discord.ext import commands
from .yt_utils import download


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

    # TODO: Maybe make what this takes to be more concise...
    def add(self, url, channel, download_data, context=None, interaction=None):
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
                "interaction": interaction,
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

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players = {}
        # self.environment = environment

    async def _get_channel_by_context(
        self, context: commands.Context, channel_name: commands.clean_content = None
    ):
        try:
            # Determine whether to get channel by author or by channel_name arg(s)
            if channel_name is None:
                channel = context.author.voice.channel
            else:
                channels = context.guild.channels
                channel = next(
                    c
                    for c in channels
                    if c.name == channel_name and isinstance(c, discord.VoiceChannel)
                )

            return channel
        except StopIteration:
            # StopIteration embed
            embed = discord.Embed(title="Failed to add to queue")
            embed.set_author(
                name=context.author.display_name,
                icon_url=context.author.display_avatar.url,
            )
            embed.add_field(
                name="Failure",
                value="Failed to find voice channel named `{channel}`".format(
                    channel=channel_name
                ),
            )
            await context.send(embed=embed)
            return None
        except AttributeError:
            # AttributeError embed
            embed = discord.Embed(title="Failed to add to queue")
            embed.set_author(
                name=context.author.display_name,
                icon_url=context.author.display_avatar.url,
            )
            embed.add_field(
                name="Failure",
                value="Either join a channel or specify one after the url",
            )
            await context.send(embed=embed)
            return None
        except Exception as ex:
            print(type(ex))
            print(ex.args)
            print(ex)

            # Exception embed
            embed = discord.Embed(title="Failed to add to queue")
            embed.set_author(
                name=context.author.display_name,
                icon_url=context.author.display_avatar.url,
            )
            embed.add_field(
                name="Failure",
                value="UNKNOWN ISSUE",
            )
            await context.send(embed=embed)
            return None

    async def _get_channel_by_interaction(
        self, interaction: discord.Interaction, channel_name: str = None
    ):
        try:
            # Determine whether to get channel by author or by channel_name arg(s)
            if channel_name is None:
                channel = interaction.user.voice.channel
            else:
                channels = interaction.guild.channels
                channel = next(
                    c
                    for c in channels
                    if c.name == channel_name and isinstance(c, discord.VoiceChannel)
                )

            return channel
        except StopIteration:
            # StopIteration embed
            embed = discord.Embed(title="Failed to add to queue")
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url,
            )
            embed.add_field(
                name="Failure",
                value="Failed to find voice channel named `{channel}`".format(
                    channel=channel_name
                ),
            )
            await interaction.followup.send(embed=embed)
            return None
        except AttributeError:
            # AttributeError embed
            embed = discord.Embed(title="Failed to add to queue")
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url,
            )
            embed.add_field(
                name="Failure",
                value="Either join a channel or specify one after the url",
            )
            await interaction.followup.send(embed=embed)
            return None
        except Exception as ex:
            print(type(ex))
            print(ex.args)
            print(ex)

            # Exception embed
            embed = discord.Embed(title="Failed to add to queue")
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url,
            )
            embed.add_field(
                name="Failure",
                value="UNKNOWN ISSUE",
            )
            await interaction.followup.send(embed=embed)
            return None

    ### SYNC SECTION ###

    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context, sync_type: str) -> None:
        """Sync the application commands"""

        async with ctx.typing():
            if sync_type == "guild":
                self.bot.tree.copy_global_to(guild=ctx.guild)
                await self.bot.tree.sync(guild=ctx.guild)
                await ctx.reply(f"Synced guild !")
                return

            await self.bot.tree.sync()
            await ctx.reply(f"Synced global !")

    @commands.command()
    @commands.is_owner()
    async def unsync(self, ctx: commands.Context, unsync_type: str) -> None:
        """Unsync the application commands"""

        async with ctx.typing():
            if unsync_type == "guild":
                self.bot.tree.clear_commands(guild=ctx.guild)
                await self.bot.tree.sync(guild=ctx.guild)
                await ctx.reply(f"Un-Synced guild !")
                return

            self.bot.tree.clear_commands()
            await self.bot.tree.sync()
            await ctx.reply(f"Un-Synced global !")

    ### PLAY SECTION ###

    @commands.command(
        name="play",
        description="Play Youtube audio through url and optional target channel",
        help="Play Youtube audio through url and optional target channel",
        usage="!steve play <url> <target_channel?>",
    )
    async def play(
        self, context: commands.Context, url: str, *, channel_name: str = None
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

        # Get channel or return out
        # NOTE: _get_channel sends back an embed based on exception
        channel = await self._get_channel_by_context(context, channel_name)
        if channel is None:
            return

        download_data = await download(url, str(guild_id))

        # Create embed for adding to queue
        embed = discord.Embed(title="Adding to queue")
        embed.set_author(
            name=context.author.display_name, icon_url=context.author.display_avatar.url
        )
        embed.add_field(name=download_data["title"], value=download_data["url"])
        await context.send(embed=embed)

        # Add guild_id if it doesn't exist yet
        if guild_id not in self.players:
            self.players[guild_id] = YoutubeDiscordPlayer()

        self.players[guild_id].add(
            url=download_data["url"],
            channel=channel,
            download_data=download_data,
            context=context,
            interaction=None,
        )
        if not self.players[guild_id].is_playing:
            await self.players[guild_id].start()

    @discord.app_commands.command(
        name="p",
        description="Play Youtube audio through url and optional target channel",
    )
    @discord.app_commands.describe(url="url", channel_name="channel name")
    async def qplay(
        self, interaction: discord.Interaction, url: str, channel_name: str = None
    ):
        """
        1. Determines channel to play audio in
        2. Downloads sound from youtube video
        3. Adds to player queue
        4?. Starts player queue if its not playing

        Args:
            interaction (_type_): Discord interaction
            url (str): Url to youtube video
            channel_name (commands.clean_content, optional):
                The name of the target channel to play audio in. Defaults to None.
        """
        await interaction.response.defer()

        guild_id = interaction.guild.id

        # Get channel or return out
        # NOTE: _get_channel sends back an embed based on exception
        channel = await self._get_channel_by_interaction(interaction, channel_name)
        if channel is None:
            return

        download_data = await download(url, str(guild_id))

        # Create embed for adding to queue
        embed = discord.Embed(title="Adding to queue")
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )
        embed.add_field(name=download_data["title"], value=download_data["url"])
        await interaction.followup.send(embed=embed)

        # Add guild_id if it doesn't exist yet
        if guild_id not in self.players:
            self.players[guild_id] = YoutubeDiscordPlayer()

        self.players[guild_id].add(
            url=download_data["url"],
            channel=channel,
            download_data=download_data,
            context=None,
            interaction=interaction,
        )
        if not self.players[guild_id].is_playing:
            await self.players[guild_id].start()

    ### STOP SECTION ###

    @commands.command(name="stop", help="Stops steve completely and clears queue")
    async def stop(self, context: commands.Context):
        """Stops all and clears queue

        Args:
            context (_type_): Discord context
        """
        # Create embed
        embed = discord.Embed(title="Stopping Queue")
        embed.set_author(
            name=context.author.display_name, icon_url=context.author.display_avatar.url
        )
        await context.send(embed=embed)

        # Reset player
        guild_id = context.author.guild.id
        if guild_id in self.players:
            await self.players[guild_id].stop()

    @discord.app_commands.command(
        name="st", description="Stops steve completely and clears queue"
    )
    async def qstop(self, interaction: discord.Interaction):
        """Stops all and clears queue

        Args:
            interaction (_type_): Discord interaction
        """
        await interaction.response.defer()
        # Create embed
        embed = discord.Embed(title="Stopping Queue")
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )
        await interaction.followup.send(embed=embed)

        # Reset player
        guild_id = interaction.user.guild.id
        if guild_id in self.players:
            await self.players[guild_id].stop()

    ### SKIP SECTION ###

    @commands.command(name="skip", help="Skips current audio")
    async def skip(self, context: commands.Context):
        """Skips current audio playing in the queue

        Args:
            context (_type_): Discord context
        """
        guild_id = context.author.guild.id

        if guild_id not in self.players or len(self.players[guild_id].queue) == 0:
            # Nothing in queue
            embed = discord.Embed(title="Nothing in Queue")
            embed.set_author(
                name=context.author.display_name,
                icon_url=context.author.display_avatar.url,
            )
            await context.send(embed=embed)
            return

        # Get needed information
        current = self.players[guild_id].queue[0]
        download_data = current["download_data"]
        url = current["url"]
        if current["context"] is None:
            interaction = current["interaction"]

            # Create embed
            embed = discord.Embed(title="Skipping")
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url,
            )
            embed.add_field(name=download_data["title"], value=url)
            await context.send(embed=embed)
        else:
            item_context = current["context"]

            # Create embed
            embed = discord.Embed(title="Skipping")
            embed.set_author(
                name=item_context.author.display_name,
                icon_url=item_context.author.display_avatar.url,
            )
            embed.add_field(name=download_data["title"], value=url)
            await context.send(embed=embed)

        # Skip
        self.players[guild_id].skip()

    @discord.app_commands.command(name="sk", description="Skips current audio")
    async def qskip(self, interaction: discord.Interaction):
        """Skips current audio playing in the queue

        Args:
            interaction (_type_): Discord interaction
        """
        await interaction.response.defer()
        guild_id = interaction.user.guild.id

        if guild_id not in self.players or len(self.players[guild_id].queue) == 0:
            # Nothing in queue
            embed = discord.Embed(title="Nothing in Queue")
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url,
            )
            await interaction.followup.send(embed=embed)
            return

        # Get needed information
        current = self.players[guild_id].queue[0]
        download_data = current["download_data"]
        url = current["url"]
        if current["context"] is None:
            item_iteration = current["interaction"]

            # Create embed
            embed = discord.Embed(title="Skipping")
            embed.set_author(
                name=item_iteration.user.display_name,
                icon_url=item_iteration.user.display_avatar.url,
            )
            embed.add_field(name=download_data["title"], value=url)
            await interaction.followup.send(embed=embed)
        else:
            context = current["context"]

            # Create embed
            embed = discord.Embed(title="Skipping")
            embed.set_author(
                name=context.author.display_name,
                icon_url=context.author.display_avatar.url,
            )
            embed.add_field(name=download_data["title"], value=url)
            await interaction.followup.send(embed=embed)

        # Skip
        self.players[guild_id].skip()

    ### QUEUE SECTION ###

    @commands.command(name="queue", help="Shows current youtube queue")
    async def queue(self, context: commands.Context):
        """Gets current queue

        Args:
            context (_type_): Discord context
        """
        guild_id = context.author.guild.id

        if guild_id not in self.players or len(self.players[guild_id].queue) == 0:
            # Nothing in queue
            embed = discord.Embed(title="Queue")
            embed.add_field(name="Empty", value="No items in queue")
            await context.send(embed=embed)
        else:
            for index, item in enumerate(self.players[guild_id].queue):
                # Create embed for each item in queue
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

    @discord.app_commands.command(name="q", description="Shows current youtube queue")
    async def qqueue(self, interaction: discord.Interaction):
        """Gets current queue

        Args:
            interaction (_type_): Discord interaction
        """
        await interaction.response.defer()
        guild_id = interaction.user.guild.id

        if guild_id not in self.players or len(self.players[guild_id].queue) == 0:
            # Nothing in queue
            embed = discord.Embed(title="Queue")
            embed.add_field(name="Empty", value="No items in queue")
            await interaction.response.send_message(embed=embed)
        else:
            embeds = []
            for index, item in enumerate(self.players[guild_id].queue):
                # Create embed for each item in queue
                embed = discord.Embed(title=f"Queue Item {index}")
                embed.set_author(
                    name=interaction.user.display_name,
                    icon_url=interaction.user.display_avatar.url,
                )
                embed.add_field(
                    name="Item {index}".format(index=index),
                    value=item["download_data"]["title"],
                    inline=False,
                )
                embed.add_field(name="Url", value=item["url"], inline=False)
                embed.add_field(
                    name="Voice Channel",
                    value="`{channel}`".format(channel=item["channel"].name),
                )
                embeds.append(embed)
            await interaction.followup.send(embeds=embeds)


async def setup(bot: commands.Bot) -> None:
    """_summary_

    Args:
        bot (commands.Bot): _description_
    """
    await bot.add_cog(YoutubeCommands(bot))
