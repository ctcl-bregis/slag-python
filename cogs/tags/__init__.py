# SLAG - CTCL 2024
# File: cogs/tags/__init__.py
# Purpose: User-settable tags extension
# Created: February 12, 2024
# Modified: February 19, 2024

import asyncio
import os
#import re
import sqlite3
from datetime import datetime

#import aiohttp
import discord
from discord.errors import NotFound
from discord.ext import commands
from discord.ext.commands import Cog
from discord.ext.commands.errors import CommandOnCooldown

from lib import hsize, logger_setup, mkerrembed

cog_logger = logger_setup("tags_logger", "logs/tags.log")

class Tags(Cog):
    def __init__(self, client):
        self.client = client

    @discord.slash_command(name = "tag_create", description = "Create a tag")
    async def tag(self, ctx: discord.ApplicationContext, content: discord.Option(str, "Content", min_length = 1, max_length = 4000, required = True)):

        dbc = sqlite3.connect("data/tags/tags.db")
        cur = dbc.cursor()

        cur.execute("SELECT creationtime, tagcreator, tagname, tagcontent FROM knowncodes WHERE fbga=?", (code,))
        res = cur.fetchone()

        await ctx.respond()

    #@discord.slash_command(name = "tag", description = "View a tag")


def setup(client):
    if not os.path.exists("tags/"):
        os.mkdir("tags/")
        os.mkdir("tags/data/")
    
    if not os.path.exists("tags/data/"):
        os.mkdir("tags/data/")

    if not os.path.exists("tags/data/tags.db"):
        dbc = sqlite3.connect("tags/data/tags.db")
        cur = dbc.cursor()

        with open("cogs/tags/tags.sql") as f:
            schema = f.read()

        cur.executescript(schema)



    


    client.add_cog(Tags(client))