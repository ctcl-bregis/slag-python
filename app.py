# SLAG - CTCL 2024
# File: app.py
# Purpose: Main application
# Created: January 24, 2024
# Modified: January 26, 2024

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
import time

if not os.path.exists("logs"):
    os.mkdir("logs/")

if not os.path.exists("logs/dm/"):
    os.mkdir("logs/dm/")

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

    # Check and create directories
    # This is done with on_message so the bot does not have to be restarted on guild join
    # TODO: Having this in on_message is inefficient, figure out how to automatically restart the bot on guild join
    if message.guild:
        for guild in client.guilds:
            if os.path.exists(f"logs/{message.guild.id}"):
                csv_log(message_data, msg_log_header, f"logs/{str(message.guild.id)}/{str(message.author.id)}_msg_log.csv")
            else:
                sys_logger.info(f"Directory for guild \"{message.guild.id}\" does not exist. Creating one now.")
                os.mkdir(f"logs/{message.guild.id}")
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

@client.command(name = "help")
async def _help(ctx):
    help_text_user = """
$help - Lists commands
$sysinfo - Reports information about the host system
$userinfo - Reports information about a specific user
"""
    embed = discord.Embed(title="Commands", color = 0xf0d000)
    embed.add_field(name="User Commands", value = help_text_user, inline = False)

    await ctx.send(embed = embed)

@client.command()
async def userinfo(ctx, *, user: discord.Member = None):
    if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("Command must be used in a guild")
        return

    unixtime = int(time.time())
    date_format = "%a, %d %b %Y %I:%M %p"

    if user is None:
        user = ctx.author
    
    embed = discord.Embed(title = f"User Information for {user}", color = 0xf0d000)
    embed.set_author(name = str(user), icon_url = user.avatar)
    embed.set_thumbnail(url = user.avatar)

    embed.add_field(name="Joined", value = user.joined_at.strftime(date_format), inline = True)
    embed.add_field(name="Registered", value = user.created_at.strftime(date_format), inline = True)

    # Display roles
    if len(user.roles) > 1:
        role_string = ' '.join([r.mention for r in user.roles][1:])
        embed.add_field(name = "Roles [{}]".format(len(user.roles) - 1), value = role_string, inline = False)

    # Display online status
    status = {
        "online": "Online",
        "offline": "Offline or invisible",
        "idle": "Idle",
        "dnd": "Do Not Disturb",
        "do_not_disturb": "Do Not Distrub"
    }

    embed.add_field(name = "Status on Mobile", value = status[user.mobile_status], inline = True)
    embed.add_field(name = "Status on Desktop", value = status[user.desktop_status], inline = True)
    embed.add_field(name = "Status on Web", value = status[user.web_status], inline = True)




    
    #embed.add_field(name="Joined", value=user.joined_at.strftime(date_format))
    #members = sorted(ctx.guild.members, key=lambda m: m.joined_at)
    #embed.add_field(name="Join position", value=str(members.index(user)+1))
    
    
    #perm_string = ', '.join([str(p[0]).replace("_", " ").title() for p in user.guild_permissions if p[1]])
    #embed.set_footer(text='ID: ' + str(user.id))

    await ctx.send(embed = embed)

@client.command()
async def sysinfo(ctx):
    embed = discord.Embed(title="Host System Information", color=0xf0d000)

    hostname = socket.gethostname()
    embed.add_field(name = "System Host Name", value = hostname, inline = False)

    uname = subprocess.check_output("uname -a", shell = True).decode().strip()
    embed.add_field(name = "uname -a output", value = uname, inline = False)

    cpuinfo = subprocess.check_output("cat /proc/cpuinfo", shell = True).decode().strip()
    for line in cpuinfo.split("\n"):
        if "model name" in line:
            cpumodel = re.sub( ".*model name.*:", "", line,1)
    embed.add_field(name = "Host CPU", value = cpumodel, inline = False)

    embed.add_field(name = "CPU thread count", value = multiprocessing.cpu_count(), inline = False)

    count = 0
    for freq in psutil.cpu_freq(True):
        # For some reason, psutil would either return GHz or MHz depending on the CPU(?)
        if freq.current < 10:
            corefreq = str(int(freq.current * 1000)) + " MHz"
        else:
            corefreq = str(int(freq.current)) + " MHz"

        embed.add_field(name = f"CPU frequency - Processor {count}", value = corefreq, inline = True)
        count += 1

    meminfo = subprocess.check_output("cat /proc/meminfo", shell = True).decode().strip()
    for line in meminfo.split("\n"):
        if 'MemTotal' in line: 
            x = line.split()
            memTotal = x[1]
    
        if 'MemFree' in line: 
            x = line.split()
            memFree = x[1]

    embed.add_field(name="Host Memory Total", value = kb2hsize(memTotal), inline = True)
    embed.add_field(name="Host Memory Free", value = kb2hsize(memFree), inline = True)

    await ctx.send(embed = embed)

# Redirect all of the discord.py logs into sys_log
logger_resetup(logging.getLogger("asyncio"), "logs/sys_log.log")
logger_resetup(logging.getLogger("discord.http"), "logs/sys_log.log")
logger_resetup(logging.getLogger("discord.client"), "logs/sys_log.log")
logger_resetup(logging.getLogger("discord.gateway"), "logs/sys_log.log")

if os.path.exists("token.txt"):
    with open("token.txt") as f:
        token = f.read()

    client.run(token)

