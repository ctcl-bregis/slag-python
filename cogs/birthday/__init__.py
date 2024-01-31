# SLAG - CTCL 2024
# File: cogs/birthday/__init__.py
# Purpose: User birthday reminders
# Created: January 27, 2024
# Modified: January 31, 2024

import csv
import os
import logging
import sqlite3
from datetime import datetime

from discord.errors import NotFound
from discord.ext import commands
from discord.ext.commands import Cog
from discord.ext.commands.errors import MemberNotFound

sys_logger = logging.getLogger("sys_logger")

class Birthday(Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def birthday(self, ctx, parameter: str == None, date: str == None):
        
        await ctx.send("test message")


def setup(client):
    dbc = sqlite3.connect("cogs/birthday/birthday.db")
    cur = dbc.cursor()
    if os.path.exists("cogs/birthday/birthday.sql"):
        try:
            with open("cogs/birthday/birthday.sql") as f:
                cur.executescript(f.read())
        except Exception as err:
            sys_logger.error(f"Exception raised when loading SQL configuration cogs/birthday/birthday.sql: {err}") 
        else:
            client.add_cog(Birthday(client))
    else:
        sys_logger.error("SQL configuration cogs/birthday/birthday.sql does not exist")