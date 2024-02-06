# SLAG - CTCL 2024
# File: cogs/micron/__init__.py
# Purpose: Interface for Micron Technology FBGA code search utility
# Created: February 6, 2024
# Modified: February 6, 2024

from discord.errors import NotFound
from discord.ext import commands
from discord.ext.commands import Cog
import discord

from lib import mkerrembed
import os
import sqlite3
from datetime import datetime

import requests, re
from bs4 import BeautifulSoup

micron_url = "https://www.micron.com/support/tools-and-utilities/fbga"

memtypes_dict = {
    "40": "DDR4 SDRAM",
    "41": "DDR3 SDRAM",
    "42": "Mobile LPDDR2",
    "44": "RLDRAM 3",
    "46": "DDR SDRAM/Mobile LPDDR",
    "47": "DDR2 SDRAM",
    "48": "SDRAM/Mobile LPSDR",
    "49": "RLDRAM 2",
    "51": "GDDR5",
    "52": "Mobile LPDDR3",
    "53": "Mobile LPDDR4 (2x16 ch/die)",
    "58": "GDDR5X",
    "60": "DDR5 SDRAM",
    "61": "GDDR6/GDDR6X",
    "62": "Mobile LPDDR",
    "63": "Mobile LPDDR6" 
}

def getdensity(pn):
    den_pn = pn[5:]
    den_pn = den_pn[:-8]
    
    if "K" in den_pn:
        mult = 1024
        den_pn = den_pn.split("K")
    elif "M" in den_pn:
        mult = 1048576
        den_pn = den_pn.split("M")
    elif "G" in den_pn:
        mult = 1073741824
        den_pn = den_pn.split("G")
    else:
        mult = 0
    
    density = int(den_pn[0]) * int(den_pn[1]) * mult
    
    # "Human size" the density
    if density >= 1073741824:
        density = str(int(density / 1073741824)) + " Gbit"
    elif density >= 1048576:
        density = str(int(density / 1048576)) + " Mbit"
    elif density >= 1024:
        density = str(int(density / 1024)) + " Kbit"
        
    return density

class Micron(Cog):
    def __init__(self, client):
        self.client = client

        if not os.path.exists("data/micron/"):
            os.mkdir("data/micron/")

        if not os.path.exists("data/micron/knowncodes.db"):
            dbc = sqlite3.connect("data/micron/knowncodes.db")
            cur = dbc.cursor()
            
            with open("cogs/micron/knowncodes.sql") as f:
                sql = f.read()

            cur.executescript(sql)
            dbc.commit()
            dbc.close()


    @discord.slash_command(name = "fbga", description = "Search for a FBGA code")
    async def micron_fbga(self, ctx: discord.ApplicationContext, code: discord.Option(str, "FBGA code - not case sensitive", max_length = 5, required = True)):

        if len(code) > 5:
            ctx.respond(embed = mkerrembed("Input too long"))
            return

        code = code.upper()

        chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        if not any((c in chars) for c in code):
            ctx.respond(embed = mkerrembed("Invalid characters found in input"))
            return

        dbc = sqlite3.connect("data/micron/knowncodes.db")
        cur = dbc.cursor()

        cur.execute("SELECT fbga, partnumber FROM knowncodes WHERE fbga=?", (code,))
        res = cur.fetchone()
        
        timestamp = datetime.now().strftime("%b %-d, %Y, %H:%M %Z")

        if res:
            pn = res[1]
        else:
            params = {"fbga": code}
            response = requests.get(micron_url, params = params)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                pnc = soup.find('td')
                if pnc:
                    pn = pnc.text
                    cur.execute("INSERT INTO knowncodes VALUES(?, ?)", (code, pn))
                    dbc.commit()
                else:
                    cur.execute("INSERT INTO knowncodes VALUES(?, ?)", (code, "None"))
                    dbc.commit()
                    await ctx.respond(embed = mkerrembed(f"Part number not found: {code}"))
                    return
            else:
                await ctx.respond(embed = mkerrembed(f"HTTP error: {response.status_code}"))
                return


        embed = discord.Embed(title = f"Results for {code}", color = 0x0000FF)
        embed.add_field(name = "Part Number", value = pn, inline = False)

        memtype_pn = pn[2:4]
        if memtype_pn in memtypes_dict.keys():
            memtype = memtypes_dict[memtype_pn]
            
            embed.add_field(name = "Type", value = memtype, inline = False)
            embed.add_field(name = "Density", value = getdensity(pn), inline = False)
            embed.add_field(name = "Die Revision", value = pn[-1:], inline = False)

        if res:
            embed.set_footer(text = f"Cached - {timestamp}")
        else:
            embed.set_footer(text = f"{micron_url}?fbga={code} - {timestamp}")
            
        await ctx.respond(embed = embed)

def setup(client):
    client.add_cog(Micron(client))