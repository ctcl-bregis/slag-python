# SLAG - CTCL 2024
# File: cogs/users/__init__.py
# Purpose: User profiling and birthday reminder cog
# Created: January 27, 2024
# Modified: February 7, 2024

import csv
import logging
import os
import sqlite3
import zoneinfo
from datetime import datetime, timedelta, timezone, tzinfo

import discord
from discord.errors import NotFound
from discord.ext import commands
from discord.ext.commands import Cog
from discord.ext.commands.errors import MemberNotFound

from lib import mkerrembed

sys_logger = logging.getLogger("sys_logger")

monthdict = {
    "January": {"num": "1", "days": 31},
    "February": {"num": "2", "days": 29},
    "March": {"num": "3", "days": 31},
    "April": {"num": "4", "days": 30},
    "May": {"num": "5", "days": 31},
    "June": {"num": "6", "days": 30},
    "July": {"num": "7", "days": 31},
    "August": {"num": "8", "days": 31},
    "September": {"num": "9", "days": 30},
    "October": {"num": "10", "days": 31},
    "November": {"num": "11", "days": 30},
    "December": {"num": "12", "days": 31}
}

tzs = zoneinfo.available_timezones()

class Users(Cog):
    def __init__(self, client):
        self.client = client
        self.members = []

        if not os.path.exists("data/users/"):
            os.mkdir("data/users/")


    def refreshusers(self):
        # Store user IDs so the code does not compare the entire member object
        memberids = []

        for guild in self.client.guilds:
            for member in guild.members:
                if member.id not in memberids and member.bot == False:
                    self.members.append(member)

        for member in self.members:
            memberid = member.id
            if not os.path.exists(f"data/users/user_{memberid}.db"):
                dbc = sqlite3.connect(f"data/users/user_{memberid}.db")
                cur = dbc.cursor()



                dbc.close()

    @Cog.listener()
    async def on_ready(self):
        pass
        #self.refreshusers()

    @discord.slash_command(name = "birthdayset", description = "Set your birthday")
    async def birthday_set(self, ctx: discord.ApplicationContext, 
        tz: discord.Option(str, "User Timezone", autocomplete = discord.utils.basic_autocomplete(tzs), required = True),
        day: discord.Option(int, "Day of Birth", min_value = 1, max_value = 31, required = True),
        month: discord.Option(str,"Month of Birth", autocomplete = discord.utils.basic_autocomplete(monthdict.keys()), max_length = 9, required = True),
        year: discord.Option(int, "Year of Birth", min_value = 1900, max_value = (datetime.now().year - 13), required = False)):

        if day > monthdict[month]["days"]:
            ctx.respond(mkerrembed(f"Invalid day parameter: {day}. Day of month must be between 1 and {monthdict[month]['days']}"))
            return

        if not month.lower() in monthdict.keys():
            ctx.respond(mkerrembed(f"Invalid month: {day}"))
            return        

        await ctx.respond("")


    @discord.slash_command(name = "birthdaysetuser", description = "Set the birthday of another user")
    async def birthday_set_user(self, ctx: discord.ApplicationContext):

        await ctx.respond("")

    @discord.slash_command()
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
        if isinstance(user, discord.Member):
            embed.add_field(name = "Nickname", value = user.nick, inline = True)
        else:
            embed.add_field(name = "Global Name", value = user.display_name, inline = True)

        embed.add_field(name = "User ID", value = user.id, inline = True)

        if isinstance(user, discord.Member):
            embed.add_field(name = "Joined", value = user.joined_at.strftime(date_format), inline = False)
        
        embed.add_field(name = "Registered", value = user.created_at.strftime(date_format), inline = False)

        # Display roles
        if isinstance(user, discord.Member):
            if user in ctx.guild.members:
                members = sorted(ctx.guild.members, key=lambda m: m.joined_at)
                embed.add_field(name = "Join position", value = str(members.index(user) + 1), inline = False)
            else:
                embed.add_field(name = "Join position", value = "N/A", inline = False)

            if len(user.roles) > 1:
                role_string = ' '.join([r.mention for r in user.roles][1:])
                embed.add_field(name = "Roles [{}]".format(len(user.roles) - 1), value = role_string, inline = False)

            embed.add_field(name = "Status on Mobile", value = status[str(user.mobile_status)], inline = True)
            embed.add_field(name = "Status on Desktop", value = status[str(user.desktop_status)], inline = True)
            embed.add_field(name = "Status on Web", value = status[str(user.web_status)], inline = True)

        embed.add_field(name = "Is bot", value = user.bot, inline = True)

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
        #user_flags += f"User is flagged as a spammer by Discord: {user.public_flags.spammer}\n"
        user_flags += f"User is an Active Developer: {user.public_flags.active_developer}\n"

        embed.add_field(name = "User Flags", value = user_flags, inline = False)
        
        embed.add_field(name = "User URL", value = user.jump_url, inline = False)

        await ctx.respond(embed = embed)
    
def setup(client):
    client.add_cog(Users(client))