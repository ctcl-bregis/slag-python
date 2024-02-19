# SLAG - CTCL 2024
# File: cogs/tags/__init__.py
# Purpose: User-settable tags extension
# Created: February 12, 2024
# Modified: February 18, 2024

import asyncio
import os
import re
import sqlite3
from datetime import datetime

import aiohttp
import discord
from discord.errors import NotFound
from discord.ext import commands
from discord.ext.commands import Cog
from discord.ext.commands.errors import CommandOnCooldown

class Tags(Cog):
    def __init__(self, client):
        self.client = client

    #@discord.slash_command(name = "tag", description = "Edit, create and view tags")
    #async def tag(self,ctx: discord.ApplicationContext, code: discord.Option(str, "Action", min_length = 5, max_length = 5, required = True)):

    #    await ctx.respond()


def setup(client):
    client.add_cog(Tags(client))