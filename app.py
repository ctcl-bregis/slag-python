# SLAG - CTCL 2024
# File: app.py
# Purpose: Main application
# Created: January 24, 2024
# Modified: January 28, 2024

import asyncio
import csv
import json
import logging
import os
import sys
import time
import socket
from datetime import datetime

import discord
from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext.commands.errors import MissingRequiredArgument, ExtensionNotFound

from lib import logger_resetup, logger_setup

sys_logger = logger_setup("sys_logger", "logs/sys_log.log")

intents = discord.Intents.all()
intents.presences = True
intents.members = True
intents.message_content = True

client = commands.Bot(command_prefix = "$", intents = intents, help_command = None, activity = discord.Activity(type=discord.ActivityType.watching, name=f"$help from {socket.gethostname()}"))

try:
    with open("config.json") as f:
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

    cogs = get_cogs()
    sys_logger.info(f"Cogs found in \"cogs/\": {cogs}")
    for cog in cogs:
        sys_logger.info(f"Cog {cog} registered")
        try:
            await client.load_extension(cog)
        except ExtensionNotFound:
            sys_logger.warn(f"Cog {cog} not found")


@client.event
async def on_guild_join(guild):
    sys_logger.info(f"SLAG joined guild named {guild.name} with ID {guild.id}")

@client.event
async def on_message(message):
    ctx = await client.get_context(message)
    if ctx.valid:
        if message.guild:
            sys_logger.info(f"User \"{message.author.name}\" ({message.author.id}) in channel {message.channel.id} in guild {message.guild.id} invoked command: {message.content}")
            try:
                await client.process_commands(message)
            except MissingRequiredArgument:
                await ctx.send("Missing arguments")
        else:
            sys_logger.info(f"User \"{message.author.name}\" in DMs invoked command: {message.content}")
            await client.process_commands(message)
    else:
        pass


# Redirect all of the discord.py logs into sys_log
logger_resetup(logging.getLogger("asyncio"), "logs/sys_log.log")
logger_resetup(logging.getLogger("discord.http"), "logs/sys_log.log")
logger_resetup(logging.getLogger("discord.client"), "logs/sys_log.log")
logger_resetup(logging.getLogger("discord.gateway"), "logs/sys_log.log")

if os.path.exists("token.txt"):
    with open("token.txt") as f:
        token = f.read()

    client.run(token)

