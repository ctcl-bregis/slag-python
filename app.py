# SLAG - CTCL 2024
# File: app.py
# Purpose: Main application
# Created: January 24, 2024
# Modified: January 25, 2024

import discord
from discord.ext import commands
from discord.ext.commands import Bot
import logging
import os
from datetime import datetime
import csv
from lib import logger_setup, logger_resetup, csv_log, kb2hsize
import asyncio
import platform
import subprocess
import re
import socket
import multiprocessing
import psutil

if not os.path.exists("logs"):
    os.mkdir("logs/")

sys_logger = logger_setup("sys_logger", "logs/sys_log.log")

msg_log_header = ["time", "id", "content", "author", "authorid", "channel", "channelid"]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = commands.Bot(command_prefix = "$", intents = intents, help_command = None, activity = discord.Activity(type=discord.ActivityType.watching, name="$help"))

@client.event
async def on_ready():
    sys_logger.info(f"SLAG active as {client.user}")
    sys_logger.info("SLAG present in guilds:")
    for guild in client.guilds:
        sys_logger.info(f"{guild.name} - {guild.id}")

@client.event
async def on_guild_join(guild):
    sys_logger.info(f"SLAG joined guild named {guild.name} with ID {guild.id}")

@client.event
async def on_message(message):
    message_data = {}

    message_data["id"] = message.id
    message_data["content"] = message.content
    message_data["author"] = message.author.name
    message_data["authorid"] = message.author.id
    try: 
        message_data["channel"] = message.channel.name
    except:
        message_data["channel"] = ""
    message_data["channelid"] = message.channel.id

    if message.guild:
        csv_log(message_data, msg_log_header, f"logs/{str(message.guild.id)}_msg_log.csv")
    else:
        csv_log(message_data, msg_log_header, "logs/other_msg_log.csv")

    await client.process_commands(message)

@client.command(name = "help")
async def _help(ctx):
    help_text_user = """
$help - Lists commands
$sysinfo - Reports information about the host system
"""
    embedVar = discord.Embed(title="Commands", color=0xf0d000)
    embedVar.add_field(name="User Commands", value="", inline=False)

    await ctx.send(embed = embedVar)

@client.command()
async def userinfo(ctx):


@client.command()
async def sysinfo(ctx):
    embedVar = discord.Embed(title="Host System Information", color=0xf0d000)

    hostname = socket.gethostname()
    embedVar.add_field(name = "System Host Name", value = hostname, inline = False)

    uname = subprocess.check_output("uname -a", shell = True).decode().strip()
    embedVar.add_field(name = "uname -a output", value = uname, inline = False)

    cpuinfo = subprocess.check_output("cat /proc/cpuinfo", shell = True).decode().strip()
    for line in cpuinfo.split("\n"):
        if "model name" in line:
            cpumodel = re.sub( ".*model name.*:", "", line,1)
    embedVar.add_field(name = "Host CPU", value = cpumodel, inline = False)

    embedVar.add_field(name = "CPU thread count", value = multiprocessing.cpu_count(), inline = False)

    count = 0
    for freq in psutil.cpu_freq(True):

        embedVar.add_field(name = f"CPU frequency - Core {count}", value = str(freq.current * 1000) + " MHz", inline = True)
        count += 1

    meminfo = subprocess.check_output("cat /proc/meminfo", shell = True).decode().strip()
    for line in meminfo.split("\n"):
        if 'MemTotal' in line: 
            x = line.split()
            memTotal = x[1]
    
        if 'MemFree' in line: 
            x = line.split()
            memFree = x[1]

    embedVar.add_field(name="Host Memory Total", value = kb2hsize(memTotal), inline = True)
    embedVar.add_field(name="Host Memory Free", value = kb2hsize(memFree), inline = True)

    await ctx.send(embed = embedVar)

# Redirect all of the discord.py logs into sys_log
logger_resetup(logging.getLogger("asyncio"), "logs/sys_log.log")
logger_resetup(logging.getLogger("discord.http"), "logs/sys_log.log")
logger_resetup(logging.getLogger("discord.client"), "logs/sys_log.log")
logger_resetup(logging.getLogger("discord.gateway"), "logs/sys_log.log")

if os.path.exists("token.txt"):
    with open("token.txt") as f:
        token = f.read()

    client.run(token)

