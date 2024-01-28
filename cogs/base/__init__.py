# SLAG - CTCL 2024
# File: cogs/base.py
# Purpose: Base command definitions
# Created: January 26, 2024
# Modified: January 27, 2024

import psutil
import socket
import platform
from discord.ext import commands
from discord.ext.commands.errors import MemberNotFound
from discord.ext.commands import has_permissions
from discord.errors import NotFound
import discord
import subprocess
import re
import multiprocessing
import time
import sys
import requests

from lib import kb2hsize

# Display online status
status = {
    "online": "Online",
    "offline": "Offline or invisible",
    "idle": "Idle",
    "dnd": "Do Not Disturb",
    "do_not_disturb": "Do Not Distrub"
}

class Base(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name = "help")
    async def _help(self, ctx):
        help_text_user = """
    $help - Lists commands
    $sysinfo - Reports information about the host system
    $userinfo - Reports information about a specific user
    """
        embed = discord.Embed(title = "Commands", color = 0xf0d000)
        embed.add_field(name = "User Commands", value = help_text_user, inline = False)
     
        await ctx.send(embed = embed)
    
    @commands.command()
    async def userinfo(self, ctx, *, user: discord.User = None):
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("Command must be used in a guild")
            return
            
        date_format = "%B %d, %Y %I:%M %p"

        # Default to the user that invoked the command
        if user is None:
            user = ctx.author
            fetched_user = await self.client.fetch_user(ctx.author.id)
        else:
            try:
                user = await ctx.guild.fetch_member(user.id)
                fetched_user = await self.client.fetch_user(user.id)
            except (MemberNotFound, NotFound):
                try:
                    user = await self.client.fetch_user(user.id)
                    fetched_user = user
                except MemberNotFound:
                    await ctx.send(f"User {user} not found")

        if fetched_user.accent_colour:
            user_color = fetched_user.accent_colour
        else:
            user_color = fetched_user.color

        
        embed = discord.Embed(title = f"User Information for {user}", color = user_color)
        embed.set_author(name = str(user), icon_url = user.default_avatar)
        embed.set_thumbnail(url = user.display_avatar)
      
        embed.add_field(name = "Username", value = user.name, inline = True)
        embed.add_field(name = "Global Name", value = user.global_name, inline = True)
        if isinstance(user, discord.Member):
            embed.add_field(name = "Nickname", value = user.display_name, inline = True)

        embed.add_field(name = "User ID", value = user.id, inline = True)
        embed.add_field(name = "Is bot", value = user.bot, inline = True)

        if isinstance(user, discord.Member):
            embed.add_field(name = "Joined", value = user.joined_at.strftime(date_format), inline = False)
        embed.add_field(name = "Registered", value = user.created_at.strftime(date_format), inline = False)
        if isinstance(user, discord.Member):
            if user in ctx.guild.members:
                members = sorted(ctx.guild.members, key=lambda m: m.joined_at)
                embed.add_field(name = "Join position", value = str(members.index(user) + 1), inline = False)
            else:
                embed.add_field(name = "Join position", value = "N/A", inline = False)

        # Display roles
        if isinstance(user, discord.Member):
            if len(user.roles) > 1:
                role_string = ' '.join([r.mention for r in user.roles][1:])
                embed.add_field(name = "Roles [{}]".format(len(user.roles) - 1), value = role_string, inline = False)

        if isinstance(user, discord.Member):
            embed.add_field(name = "Status on Mobile", value = status[str(user.mobile_status)], inline = True)
            embed.add_field(name = "Status on Desktop", value = status[str(user.desktop_status)], inline = True)
            embed.add_field(name = "Status on Web", value = status[str(user.web_status)], inline = True)

        # Avoiding the use of flag bits here since it overcomplicates things and Python endianness depends on the CPU which could cause problems if this is hosted on a CPU arch other than x86(-64) such as a Raspberry Pi
        user_flags = ""
        user_flags += f"User is a Discord Employee: {user.public_flags.staff}\n"
        user_flags += f"User is a Discord Partner: {user.public_flags.partner}\n"
        user_flags += f"User is a HypeSquad Events member: {user.public_flags.hypesquad}\n"
        user_flags += f"User is a Bug Hunter: {user.public_flags.bug_hunter}\n"
        user_flags += f"User is a Bug Hunter Level 2: {user.public_flags.bug_hunter_level_2}\n"
        user_flags += f"User is a HypeSquad Bravery Member: {user.public_flags.hypesquad_bravery}\n"
        user_flags += f"User is a HypeSquad Brilliance Member: {user.public_flags.hypesquad_brilliance}\n"
        user_flags += f"User is a HypeSquad Balance Member: {user.public_flags.hypesquad_balance}\n"
        user_flags += f"User is an Early Supporter (Nitro before Oct 10 2018): {user.public_flags.early_supporter}\n"
        user_flags += f"User is a Team User: {user.public_flags.team_user}\n"
        user_flags += f"User is a System User: {user.public_flags.system}\n"
        user_flags += f"User is a Verified Bot: {user.public_flags.verified_bot}\n"
        user_flags += f"User is an Early Verified Bot Developer: {user.public_flags.verified_bot_developer}\n"
        user_flags += f"User is a Discord Certified Moderator: {user.public_flags.discord_certified_moderator}\n"
        user_flags += f"User is flagged as a spammer by Discord: {user.public_flags.spammer}\n"
        user_flags += f"User is an Active Developer: {user.public_flags.active_developer}\n"

        embed.add_field(name = "User Flags", value = user_flags, inline = False)
        
        await ctx.send(embed = embed)

    @commands.command()
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
     
        meminfo = subprocess.check_output("cat /proc/meminfo", shell = True).decode().strip()
        for line in meminfo.split("\n"):
            if 'MemTotal' in line: 
                x = line.split()
                memTotal = x[1]
        
            if 'MemFree' in line: 
                x = line.split()
                memFree = x[1]
     
        embed.add_field(name = "Host Memory Total", value = kb2hsize(memTotal), inline = True)
        embed.add_field(name = "Host Memory Free", value = kb2hsize(memFree), inline = True)
     
        await ctx.send(embed = embed)

    #@commands.command()
    #async def botinfo(self, ctx):
    #    self

    # Admin only for now since this can send a message in any channel
    @commands.command()
    @has_permissions(administrator=True)
    async def attach2msg(self, ctx, *, channel: str = None):
        if channel == None:
            await ctx.send("Missing argument: Channel")
            return

        if len(ctx.message.attachments) > 0:
            att_url = ctx.message.attachments[0].url
            r = requests.get(att_url, stream = True)
            r.raw.decode_content = True
            if r.headers["content-type"] in ["text/markdown; charset=utf-8", "text/plain; charset=utf-8"]:
                if len(r.text) > 2000:
                    for split in (r.text[0+i:2000+i] for i in range(0, len(r.text), 2000)):
                        await ctx.send(split)
                else:
                    await ctx.send(r.text)
            else:
                await ctx.send("File appears to not be markdown or text")
        elif len(ctx.message.attachments) > 1:
            await ctx.send("Too many attachements.\nUsage: mdmsg <channel> + .md or .txt file attachement")

        else:
            await ctx.send("No attachments found.\nUsage: mdmsg <channel> + .md ot .txt file attachement")

    # Admin only for now since this could be spammed
    @commands.command()
    @has_permissions(administrator=True)
    async def channellist(self, ctx):
        msg = ""
        channeldict = {}
        nocategory = []
        categorynames = []

        for category in ctx.guild.categories:
            channeldict[category.name] = []
            categorynames = []


        # Get channels that are not categorized first
        # This might be inefficient
        for channel in ctx.guild.channels:
            if channel.category == None:
                nocategory.append(channel)
            elif channel.category in categorynames:
                channeldict[channel.category.name].append(channel)    

async def setup(client):
    await client.add_cog(Base(client))