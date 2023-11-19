"""Main Bot Start Script
"""
import os

import asyncio
import json
from dotenv import load_dotenv
import discord
from discord.ext import commands
from ytdb.yt_player import YoutubeCommands


def main():
    """Main"""
    print("Starting YTDB...")

    # Get envs
    print("Loading dotenv")
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")

    env = os.getenv("ENV", "dev")
    print("environment: {env}".format(env=env))

    command_prefix = json.loads(os.getenv("COMMAND_PREFIX", '["!steve "]'))
    print("command_prefix(es): {command_prefix}".format(command_prefix=command_prefix))

    # Create Intents for bot
    print("Creating intents...")
    intents = discord.Intents.default()
    intents.message_content = True

    # Create bot
    print("Creating main bot...")
    main_bot = commands.Bot(
        command_prefix=command_prefix,
        intents=intents,
        activity=discord.Game("some music!"),
    )

    @main_bot.event
    async def on_ready():
        """On Ready for bot"""
        print(f"{main_bot.user} has connected to Discord!")

    asyncio.run(main_bot.load_extension("ytdb.yt_player"))
    main_bot.run(token)


if __name__ == "__main__":
    main()
