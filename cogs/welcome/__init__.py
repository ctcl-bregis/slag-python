# SLAG - CTCL 2024
# File: cogs/welcome.py
# Purpose: Sends a welcome message on user join or a leave message on user leave
# Created: January 27, 2024
# Modified: February 5, 2024

from datetime import datetime
from discord.ext import commands
from discord.ext.commands import Cog
import discord

class Welcome(Cog):
    def __init__(self, client):
        self.client = client

    # TODO: Add configuration command or something that defines what channel in what guild to use to send these messages
    @Cog.listener()
    async def on_member_join(self, member):
        embed = discord.Embed(title="Welcome {member.name}!", color=0x00ff00)
        embed.set_thumbnail(url = member.display_avatar)

        await discord.TextChannel.send(discord.utils.get(member.guild.channels, name="welcome"), embed = embed)
        
    @Cog.listener()
    async def on_member_remove(self, member):
        embed = discord.Embed(title="Member Left: {member.name}", color=0xff0000)
        embed.set_thumbnail(url = member.display_avatar)  

        await discord.TextChannel.send(discord.utils.get(member.guild.channels, name="welcome"), embed = embed)
   


def setup(client):
    client.add_cog(Welcome(client))