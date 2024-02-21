# SLAG - CTCL 2024
# File: cogs/tags/__init__.py
# Purpose: User-settable tags extension
# Created: February 12, 2024
# Modified: February 20, 2024

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
from discord import default_permissions
from discord.commands import SlashCommandGroup

from lib import hsize, logger_setup, mkerrembed

cog_logger = logger_setup("tags_logger", "logs/tags.log")

class Tags(Cog):
    def __init__(self, client):
        self.client = client

    tag = SlashCommandGroup("tag", "Create, view and edit tags")

    @tag.command(name = "create", description = "Create a tag")
    async def tag_create(self, ctx: discord.ApplicationContext, name: discord.Option(str, "Tag Name",  min_length = 1, max_length = 40, required = True), content: discord.Option(str, "Content", min_length = 1, max_length = 4000, required = True)):

        dbc = sqlite3.connect("data/tags/tags.db")
        cur = dbc.cursor()

        cur.execute("SELECT creationtime, tagcreator, tagname, tagcontent FROM knowncodes WHERE fbga=?", (code,))
        res = cur.fetchone()

        await ctx.respond()

    @tag.command(name = "view", description = "View a tag")
    async def tag_view(self, ctx: discord.ApplicationContext, name: discord.Option(str, "Tag Name",  min_length = 1, max_length = 40, required = True)):

        dbc = sqlite3.connect("data/tags/tags.db")
        cur = dbc.cursor()

        cur.execute("SELECT creationtime, tagcreator, tagname, tagcontent FROM knowncodes WHERE fbga=?", (code,))
        res = cur.fetchone()

        await ctx.respond()
    
    @tag.command(name = "delete", description = "Delete a tag")
    async def tag_delete(self, ctx: discord.ApplicationContext, name: discord.Option(str, "Tag Name",  min_length = 1, max_length = 40, required = True)):

        await ctx.respond(int(ctx.author.guild.id))

    @tag.command(name = "admin_delete", description = "Delete any tag (admin only)")
    @default_permissions(administrator = True)
    async def tag_any_delete(self, ctx: discord.ApplicationContext, name: discord.Option(str, "Tag Name",  min_length = 1, max_length = 40, required = True)):

        await ctx.respond()

def setup(client):   
    if not os.path.exists("data/tags/"):
        os.mkdir("data/tags/")

    if not os.path.exists("data/tags/tags.db"):
        dbc = sqlite3.connect("data/tags/tags.db")
        cur = dbc.cursor()

        with open("cogs/tags/tags.sql") as f:
            schema = f.read()
 
        cur.executescript(schema)

    client.add_cog(Tags(client))