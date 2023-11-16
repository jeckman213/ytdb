"""Main Bot Start Script
"""
import os

import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands
from ytdb.yt_player import YoutubeCommands


def main():
    """Main"""
    # Get envs
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    env = os.getenv("ENV", "dev")

    # Create Intents for bot
    intents = discord.Intents.default()
    intents.message_content = True

    # Determine command prefix based on ENV
    command_prefix = "!steve "
    if env == "dev":
        command_prefix = "!dsteve "

    # Create bot
    main_bot = commands.Bot(
        command_prefix=command_prefix,
        intents=intents,
        activity=discord.Game("some music!"),
    )
    # Create cog(s)
    cog = YoutubeCommands(main_bot, env)

    # Add cog(s)
    asyncio.run(main_bot.add_cog(cog))

    @main_bot.event
    async def on_ready():
        """On Ready for bot"""
        print(f"{main_bot.user} has connected to Discord!")

    main_bot.run(token)


if __name__ == "__main__":
    main()
