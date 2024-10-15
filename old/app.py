# SLAG - CTCL 2024
# File: app.py
# Purpose: Main application
# Created: January 24, 2024
# Modified: February 18, 2024

import asyncio
import csv
import json
import logging
import os
import re
import socket
import subprocess
import sys
import time
from datetime import datetime

import discord
from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext.commands.errors import MissingRequiredArgument

from lib import logger_resetup, logger_setup, mkerrembed
from cogs.users import gathermessages

if not os.path.exists("logs/"):
    os.mkdir("logs/")

if not os.path.exists("data/"):
        os.mkdir("data/")

sys_logger = logger_setup("sys_logger", "logs/sys_log.log")

intents = discord.Intents.all()
intents.auto_moderation_configuration = True
intents.auto_moderation_execution = True
intents.bans = True
intents.emojis_and_stickers = True
intents.guilds = True
intents.integrations = True
intents.invites = True
intents.members = True
intents.message_content = True
intents.messages = True
intents.presences = True
intents.reactions = True
intents.scheduled_events = True
intents.typing = True
intents.voice_states = True
intents.webhooks = True

# Disable auto_sync_commands as sync_commands is called after the loading of the cogs
client = commands.Bot(command_prefix = "$", auto_sync_commands = False, intents = intents, help_command = None, activity = discord.Activity(type=discord.ActivityType.watching, name = f"from {socket.gethostname()}"))

try:
    with open("config/config.json") as f:
        config = f.read()
except Exception as err:
    sys_logger.error(f"File read error when processing \"config.json\": {err}")
    sys.exit()

else:
    config = json.loads(config)["config"]

def get_cogs():
    cogs = [x[0][5:] for x in os.walk("cogs/")]
    # Check whitelist
    cogs = [cog for cog in cogs if cog in config["cog_whitelist"] and cog != "__pycache__" and cog != ""]
    # Add "cogs." to each cog
    cogs = ["cogs." + cog for cog in cogs]

    return cogs

@client.event
async def on_ready():
    sys_logger.info(f"SLAG active as {client.user}")
    sys_logger.info("SLAG present in guilds:")
    for guild in client.guilds:
        sys_logger.info(f"{guild.name} - {guild.id}")

    # This has to be called after the bot is ready
    if "cogs.users" in get_cogs():
        if len(sys.argv) == 2:
            if sys.argv[1] == "gathermessages":
                await gathermessages(client)

    cogs = get_cogs()
    sys_logger.info(f"Cogs found in \"cogs/\": {cogs}")
    for cog in cogs:
        if client.load_extension(cog):
            sys_logger.info(f"Cog {cog} registered")

    await client.sync_commands()

@client.event
async def on_guild_join(guild):
    sys_logger.info(f"SLAG joined guild named {guild.name} with ID {guild.id}")

# Redirect all of the discord.py logs into sys_log
logger_resetup(logging.getLogger("asyncio"), "logs/sys_log.log")
logger_resetup(logging.getLogger("discord.http"), "logs/sys_log.log")
logger_resetup(logging.getLogger("discord.client"), "logs/sys_log.log")
logger_resetup(logging.getLogger("discord.gateway"), "logs/sys_log.log")

if len(sys.argv) > 2:
    sys_logger.error("Too many arguments passed")
    sys.exit(1)

if os.path.exists("token.txt"):
    with open("token.txt") as f:
        token = f.read()
            
    client.run(token)

