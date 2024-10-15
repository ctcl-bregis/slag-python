# SLAG-python - CTCL 2024
# File: app.py
# Purpose: Application entry point
# Created: January 24, 2024
# Modified: October 5, 2024

from pydantic import BaseModel, PositiveInt
import json
import logging
import os
import socket

import discord
from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext.commands.errors import MissingRequiredArgument

from lib import logger_resetup, logger_setup, mkerrembed

class CogDef(BaseModel):
    enabled: bool
    name: str
    displayname: str
    desc: str

class Config(BaseModel):
    token: str
    cogpath: str
    cogs: list[CogDef]

with open("./config.json") as f:
    config_raw = f.read()

config_dict = json.loads(config_raw)
config = Config(**config_dict)

intents = discord.Intents.all()
client = commands.Bot(command_prefix = "$", auto_sync_commands = False, intents = intents, help_command = None, activity = discord.Activity(type=discord.ActivityType.watching, name = f"from {socket.gethostname()}"))


if not os.path.exists("log"):
    os.mkdir("log/")

sys_logger = logger_setup("sys_logger", "log/sys_log.log")

# Redirect all of the discord.py logs into sys_log
logger_resetup(logging.getLogger("asyncio"), "log/sys_log.log")
logger_resetup(logging.getLogger("discord.http"), "log/sys_log.log")
logger_resetup(logging.getLogger("discord.client"), "log/sys_log.log")
logger_resetup(logging.getLogger("discord.gateway"), "log/sys_log.log")

@client.event
async def on_ready():
    sys_logger.info(f"Bot logged in as: {client.user}")
    
    for cog in config.cogs:
        try: 
            if client.load_extension(f"cogs.{cog.name}"):
               sys_logger.info(f"Cog {cog.name} registered")
            else:
                sys_logger.warning(f"Cog {cog.name} failed to load")
        except:
            sys_logger.warning(f"Cog {cog.name} failed to load")

    await client.sync_commands()

if __name__ == "__main__":
    client.run(config.token)