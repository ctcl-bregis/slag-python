# SLAG - CTCL 2024
# File: cogs/base.py
# Purpose: Base command definitions
# Created: January 26, 2024
# Modified: February 7, 2024

import multiprocessing
import os
import platform
import re
import socket
import subprocess
import sys
import time

import discord
import psutil
import requests
from discord.errors import NotFound
from discord.ext import commands
from discord.ext.commands import Cog, has_permissions
from discord.ext.commands.errors import MemberNotFound

from lib import kb2hsize, msgsplit

# Display online status
status = {
    "online": "Online",
    "offline": "Offline or invisible",
    "idle": "Idle",
    "dnd": "Do Not Disturb",
    "do_not_disturb": "Do Not Distrub"
}

class Base(Cog):
    def __init__(self, client):
        self.client = client

    @discord.slash_command(name = "help")
    async def _help(self, ctx):
        help_text_user = """
    $help - Lists commands
    $sysinfo - Reports information about the host system
    $userinfo - Reports information about a specific user
    """
        embed = discord.Embed(title = "Commands", color = 0xf0d000)
        embed.add_field(name = "User Commands", value = help_text_user, inline = False)
     
        await ctx.respond(embed = embed)

    @discord.slash_command()
    async def sysinfo(self, ctx):
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
     

        # /proc/memfree is Linux-specific
        if os.name == "posix" and os.path.exists("/proc/memfree"):
            meminfo = subprocess.check_output("cat /proc/meminfo", shell = True).decode().strip()
            for line in meminfo.split("\n"):
                if 'MemTotal' in line: 
                    x = line.split()
                    memtotal = x[1]
        
                if 'MemFree' in line: 
                    x = line.split()
                    memfree = x[1]

                # Get buffers and cache to calculate memory free to applications
                if 'Buffers' in line:
                    x = line.split()
                    membuffers = x[1]

                if 'Cached' in line:
                    x = line.split()
                    memcached = x[1]

                if memcached and membuffers and memfree:
                    actualmemfree = memfree + memcached + membuffers
     
            embed.add_field(name = "Host Memory Total", value = kb2hsize(memtotal), inline = True)
            embed.add_field(name = "Host Memory Free", value = kb2hsize(memfree), inline = True)
            embed.add_field(name = "Actual Host Memory Free", value = kb2hsize(actualmemfree), inline = True)
     
        await ctx.respond(embed = embed)

    #@commands.command()
    #async def botinfo(self, ctx):
    #    self

    # Admin only for now since this can send a message in any channel
    @discord.slash_command()
    @has_permissions(administrator=True)
    async def attach2msg(self, ctx, *, channel: str = None):
        if channel == None:
            await ctx.respond("Missing argument: Channel")
            return

        if len(ctx.message.attachments) > 0:
            att_url = ctx.message.attachments[0].url
            r = requests.get(att_url, stream = True)
            r.raw.decode_content = True
            if r.headers["content-type"] in ["text/markdown; charset=utf-8", "text/plain; charset=utf-8"]:
                if len(r.text) > 2000:
                    for split in (r.text[0+i:2000+i] for i in range(0, len(r.text), 2000)):
                        await ctx.send(split)

                    await ctx.respond("")
                else:
                    await ctx.respond(r.text)
            else:
                await ctx.respond("File appears to not be markdown or text")
        elif len(ctx.message.attachments) > 1:
            await ctx.respond("Too many attachements.\nUsage: mdmsg <channel> + .md or .txt file attachement")

        else:
            await ctx.respond("No attachments found.\nUsage: mdmsg <channel> + .md ot .txt file attachement")

    # Admin only for now since this could be spammed
    @discord.slash_command()
    @has_permissions(administrator=True)
    async def channellist(self, ctx, *, filt = "everyone"):
        msg = "# Channels\n"
        channeldict = {}
        nocategory = []
        categorynames = []

        for category in ctx.guild.categories:
            channeldict[category.name] = []
            categorynames.append(category.name)

        if filt == "everyone":
            for channel in ctx.guild.channels:
                if channel.category == None:
                    if channel.permissions_for(ctx.guild.default_role).view_channel:
                        nocategory.append(channel)
                else:
                    if channel.category.name in categorynames and channel.permissions_for(ctx.guild.default_role).view_channel:
                        channeldict[channel.category.name].append(channel)    
        elif filt == "all":
            for channel in ctx.guild.channels:
                if channel.category == None:
                    nocategory.append(channel)
                else:
                    if channel.category.name in categorynames:
                        channeldict[channel.category.name].append(channel)    

        if nocategory != []:
            for channel in nocategory:
                if channel.type == discord.ChannelType.text:
                    msg += f":speech_balloon:: {channel.jump_url}\n"
                elif channel.type == discord.ChannelType.voice:
                    msg += f":microphone2:: `{channel.name}`\n"
                elif channel.type == discord.ChannelType.news:
                    msg += f":mega:: {channel.jump_url}\n"
                elif channel.type == discord.ChannelType.forum:
                    msg += f":memo:: {channel.jump_url}\n"

        for categoryname in categorynames:
            if channeldict[categoryname] != []:
                msg += f"## {categoryname}\n"
                channeldict[categoryname].sort(key=lambda x: x.position, reverse=False)
                for channel in channeldict[categoryname]:
                    if channel.type == discord.ChannelType.text:
                        msg += f":speech_balloon:: {channel.jump_url}\n"
                    elif channel.type == discord.ChannelType.voice:
                        msg += f":microphone2:: `{channel.name}`\n"
                    elif channel.type == discord.ChannelType.news:
                        msg += f":mega:: {channel.jump_url}\n"
                    elif channel.type == discord.ChannelType.forum:
                        msg += f":memo:: {channel.jump_url}\n"

        if msg == "":
            return

        if len(msg) > 1500:
            splitmsg = msg.split("\n")

            msg = msgsplit(1500, splitmsg)

            for part in msg:
                await ctx.send(part)

            await ctx.respond("")
        else:
            await ctx.respond(msg)


def setup(client):
    client.add_cog(Base(client))