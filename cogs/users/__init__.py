# SLAG - CTCL 2024
# File: cogs/users/__init__.py
# Purpose: User profiling and birthday reminder cog
# Created: January 27, 2024
# Modified: February 5, 2024

import csv
import os
import logging
import sqlite3
from datetime import datetime, tzinfo, timedelta, timezone
import zoneinfo

from discord.errors import NotFound
from discord.ext import commands
from discord.ext.commands import Cog
from discord.ext.commands.errors import MemberNotFound
import discord

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

# 
class Users(Cog):
    def __init__(self, client):
        self.client = client
        self.dbc = sqlite3.connect("user_meta.db")
        self.cur = self.dbc.cursor()

        self.members = []

        if not os.path.exists("data/users/"):
            os.mkdir("data/users/")

    def refreshusers(self):
        # Store user IDs so the code does not compare the entire member object
        memberids = []

        for guild in self.client.guilds:
            for member in guild.members:
                if member.id not in self.memberids and member.bot == False:
                    self.members.append(member)

        for memberid in memberids:
            if not os.path.exists(f"data/user_{memberid}.db"):
                dbc = sqlite3.connect("data/user_{memberid}.db")
                con = dbc.cursor()

    @discord.slash_command(name = "birthdayset", description = "Set your birthday")
    async def birthday_set(self, ctx: discord.ApplicationContext, 
        tz: discord.Option(str, "User Timezone", autocomplete = discord.utils.basic_autocomplete(tzs), required = True),
        day: discord.Option(int, "Day of Birth", min_value = 1, max_value = 31, required = True),
        month: discord.Option(str,"Month of Birth", autocomplete = discord.utils.basic_autocomplete(monthdict.keys()), max_length = 9, required = True),
        year: discord.Option(int, "Year of Birth", min_value = 1900, max_value = (datetime.now().year - 13), required = False)
    ):

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


    
def setup(client):
    client.add_cog(Users(client))