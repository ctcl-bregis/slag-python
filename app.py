# SLAG - CTCL 2024
# File: app.py
# Purpose: Main application
# Created: January 24, 2024
# Modified: January 27, 2024

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

from lib import csv_log, logger_resetup, logger_setup

if not os.path.exists("logs"):
    os.mkdir("logs/")

if not os.path.exists("logs/dm/"):
    os.mkdir("logs/dm/")

sys_logger = logger_setup("sys_logger", "logs/sys_log.log")

msg_log_header = ["time", "id", "content", "author", "channel", "channelid"]

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
    cogs = os.listdir("cogs/")
    # Get files only with .py
    cogs = [fname[:-3] for fname in cogs if fname.endswith(".py")]
    # Check whitelist
    cogs = [cog for cog in cogs if cog in config["cog_whitelist"]]
    # Add "cogs." to each cog
    cogs = ["cogs." + cog for cog in cogs]

    return cogs

@client.event
async def on_ready():
    sys_logger.info(f"SLAG active as {client.user}")
    sys_logger.info("SLAG present in guilds:")
    for guild in client.guilds:
        sys_logger.info(f"{guild.name} - {guild.id}")

    for cog in get_cogs():
        await client.load_extension(cog)

@client.event
async def on_guild_join(guild):
    sys_logger.info(f"SLAG joined guild named {guild.name} with ID {guild.id}")

@client.event
async def on_message(message):
    message_data = {}

    message_data["id"] = message.id
    message_data["content"] = message.content
    message_data["author"] = message.author.name
    try: 
        message_data["channel"] = message.channel.name
    except:
        message_data["channel"] = ""
    message_data["channelid"] = message.channel.id

    # Check and create directories
    # This is done with on_message so the bot does not have to be restarted on guild join
    # TODO: Having this in on_message is inefficient, figure out how to automatically restart the bot on guild join
    if not os.path.exists("logs/"):
        sys_logger.info("logs directory does not exist. Creating one now.")
        os.mkdir("logs/")

    if not message.author.bot:
        if message.guild:
            for guild in client.guilds:
                if not os.path.exists(f"logs/{message.guild.id}"):
                    sys_logger.info(f"Directory for guild \"{message.guild.id}\" does not exist. Creating one now.")
                    os.mkdir(f"logs/{message.guild.id}")
    
            csv_log(message_data, msg_log_header, f"logs/{str(message.guild.id)}/{str(message.author.id)}_msg_log.csv")
        else:
            csv_log(message_data, msg_log_header, f"logs/dm/{message.author.name}_msg_log.csv")

    ctx = await client.get_context(message)
    if ctx.valid:
        if message.guild:
            sys_logger.info(f"User \"{message.author.name}\" ({message.author.id}) in channel {message_data['channel']} in guild {message.guild.id} invoked command: {message.content}")
            await client.process_commands(message)
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

