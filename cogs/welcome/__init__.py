# SLAG - CTCL 2024
# File: cogs/welcome.py
# Purpose: Sends a welcome message on user join or a leave message on user leave
# Created: January 27, 2024
# Modified: January 29, 2024

from datetime import datetime
from discord.ext import commands

class Welcome(commands.Cog):
    def __init__(self, client):
        self.client = client

    # TODO: Add configuration command or something that defines what channel in what guild to use to send these messages
    @commands.Cog.listener()
    async def on_member_join(self, member):
        embed = discord.Embed(title="Welcome {member.name}!", color=0x00ff00)
        embed.set_thumbnail(url = member.display_avatar)

        discord.TextChannel.send(discord.utils.get(ctx.guild.channels, name="welcome"), embed = embed)
        

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        embed = discord.Embed(title="Member Left: {member.name}", color=0xff0000)
        embed.set_thumbnail(url = member.display_avatar)  

        discord.TextChannel.send(discord.utils.get(ctx.guild.channels, name="welcome"), embed = embed)
   


async def setup(client):
    await client.add_cog(Welcome(client))