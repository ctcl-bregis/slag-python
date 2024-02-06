# SLAG - CTCL 2024
# File: app.py
# Purpose: Main application
# Created: January 24, 2024
# Modified: February 6, 2024

import asyncio
import csv
import json
import logging
import os
import sys
import time
import socket
import subprocess
import re
from datetime import datetime

import discord
from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext.commands.errors import MissingRequiredArgument

from lib import logger_resetup, logger_setup

if not os.path.exists("logs/"):
    os.mkdir("logs/")

sys_logger = logger_setup("sys_logger", "logs/sys_log.log")

intents = discord.Intents.all()
intents.presences = True
intents.members = True
intents.message_content = True

client = commands.Bot(command_prefix = "$", intents = intents, help_command = None, activity = discord.Activity(type=discord.ActivityType.watching, name = f"$help from {socket.gethostname()}"))

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

@client.event
async def on_guild_join(guild):
    sys_logger.info(f"SLAG joined guild named {guild.name} with ID {guild.id}")

# Redirect all of the discord.py logs into sys_log
logger_resetup(logging.getLogger("asyncio"), "logs/sys_log.log")
logger_resetup(logging.getLogger("discord.http"), "logs/sys_log.log")
logger_resetup(logging.getLogger("discord.client"), "logs/sys_log.log")
logger_resetup(logging.getLogger("discord.gateway"), "logs/sys_log.log")

if os.path.exists("token.txt"):
    with open("token.txt") as f:
        token = f.read()

    if not os.path.exists("data/"):
        os.mkdir("data/")

    cogs = get_cogs()
    sys_logger.info(f"Cogs found in \"cogs/\": {cogs}")
    for cog in cogs:
        if client.load_extension(cog):
            sys_logger.info(f"Cog {cog} registered")
        
    client.run(token)

