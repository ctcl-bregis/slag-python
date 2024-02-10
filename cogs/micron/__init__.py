# SLAG - CTCL 2024
# File: cogs/micron/__init__.py
# Purpose: Micron FBGA decoder and code lookup cog
# Created: February 6, 2024
# Modified: February 10, 2024

import os
import re
import sqlite3
from datetime import datetime

import discord
import requests
from bs4 import BeautifulSoup
from discord.errors import NotFound
from discord.ext import commands
from discord.ext.commands import Cog
from discord.ext.commands.errors import CommandOnCooldown

from lib import logger_setup, mkerrembed

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

week_dict = {
    "A": 2,
    "B": 4,
    "C": 6,
    "D": 8,
    "E": 10,
    "F": 12,
    "G": 14,
    "H": 16,
    "I": 18,
    "J": 20,
    "K": 22,
    "L": 24,
    "M": 26,
    "N": 28,
    "O": 30,
    "P": 32,
    "Q": 34,
    "R": 36,
    "S": 38,
    "T": 40,
    "U": 42,
    "V": 44,
    "W": 46,
    "X": 48,
    "Y": 50,
    "Z": 52
}

location_dict = {
    "1": "USA",
    "2": "Singapore",
    "3": "Italy",
    "4": "Japan",
    "5": "China",
    "7": "Taiwan",
    "8": "Korea",
    "9": "Mixed",
    "B": "Israel",
    "C": "Ireland",
    "D": "Malaysia",
    "F": "Philippines"
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

    try:
        density = int(den_pn[0]) * int(den_pn[1]) * mult
    except ValueError:
        return None
    
    # "Human size" the density
    if density >= 1073741824:
        density = str(int(density / 1073741824)) + " Gbit"
    elif density >= 1048576:
        density = str(int(density / 1048576)) + " Mbit"
    elif density >= 1024:
        density = str(int(density / 1024)) + " Kbit"
        
    return density

cog_logger = logger_setup("cog_micron", "logs/sys_log.log")

class Micron(Cog):
    def __init__(self, client):
        self.client = client

        if not os.path.exists("data/micron/"):
            os.mkdir("data/micron/")

        # Init database if it does not exist
        if not os.path.exists("data/micron/knowncodes.db"):
            dbc = sqlite3.connect("data/micron/knowncodes.db")
            cur = dbc.cursor()
            
            with open("cogs/micron/knowncodes.sql") as f:
                sql = f.read()

            cur.executescript(sql)
            dbc.commit()
            dbc.close()

    @discord.slash_command(name = "fbga", description = "Micron FBGA Lookup - Search for a FBGA code (bottom row on IC)")
    async def micron_fbga(self, ctx: discord.ApplicationContext, code: discord.Option(str, "FBGA code - not case sensitive", min_length = 5, max_length = 5, required = True)):
        if not re.match("[A-Z0-9]+", code):
            await ctx.respond(embed = mkerrembed(f"Invalid production code"))
            return

        dbc = sqlite3.connect("data/micron/knowncodes.db")
        cur = dbc.cursor()

        cur.execute("SELECT fbga, partnumber FROM knowncodes WHERE fbga=?", (code,))
        res = cur.fetchone()
        
        timestamp = datetime.now().strftime("%b %-d, %Y, %H:%M %Z")

        if res:
            cog_logger.info(f"FBGA code found in cache: {code}")
            pn = res[1]
        else:
            params = {"fbga": code}
            response = requests.get(micron_url, params = params)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                pnc = soup.find('td')
                if pnc:
                    pn = pnc.text
                    cog_logger.info(f"Known valid FBGA code inserted into database: {code}")
                    cur.execute("INSERT INTO knowncodes VALUES(?, ?)", (code, pn))
                    dbc.commit()
                else:
                    cog_logger.info(f"Known invalid FBGA code inserted into database: {code}")
                    cur.execute("INSERT INTO knowncodes VALUES(?, ?)", (code, "None"))
                    dbc.commit()
                    pn = "None"
            else:
                await ctx.respond(embed = mkerrembed(f"HTTP error: {response.status_code}"))
                return

        cog_logger.info(f"Part number: {pn}")

        
        if pn == "None":
            embed = discord.Embed(title = f"No part number found for {code}", color = 0x0000FF)
        
            if res:
                embed.set_footer(text = f"Cached - {timestamp}")
            else:
                embed.set_footer(text = f"{micron_url}?fbga={code} - {timestamp}")

            await ctx.respond(embed = embed)
            return
        else:
            embed = discord.Embed(title = f"Results for {code}", color = 0x0000FF)

        if pn.startswith("E"):
            embed.add_field(name = "Part Number - Elpida legacy part", value = pn, inline = False)
        else:
            embed.add_field(name = "Part Number", value = pn, inline = False)

        memtype_pn = pn[2:4]
        if memtype_pn in memtypes_dict.keys():
            memtype = memtypes_dict[memtype_pn]
            
            embed.add_field(name = "Type", value = memtype, inline = False)

            if getdensity(pn):
                embed.add_field(name = "Density", value = getdensity(pn), inline = False)

            if pn[-2:-1] == ":":
                embed.add_field(name = "Die Revision", value = pn[-1:], inline = False)

        if res:
            embed.set_footer(text = f"Cached - {timestamp}")
        else:
            embed.set_footer(text = f"{micron_url}?fbga={code} - {timestamp}")
            
        dbc.close()
        await ctx.respond(embed = embed)
        return

    @discord.slash_command(name = "flush_fbga", description = "Micron FBGA Lookup - Removes a specific FBGA code from the database")
    async def micron_flush_fbga(self, ctx: discord.ApplicationContext, code: discord.Option(str, "FBGA code - not case sensitive", min_length = 5, max_length = 5, required = True)):
        dbc = sqlite3.connect("data/micron/knowncodes.db")
        cur = dbc.cursor()
        cur.execute("SELECT fbga, partnumber FROM knowncodes WHERE fbga=?", (code,))
        res = cur.fetchone()

        if res:
            cur.execute("DELETE FROM knowncodes WHERE fbga=?", (code,))
            dbc.commit()
            embed = discord.Embed(title = f"{code} removed from database", color = 0x0000FF)
            cog_logger.info(f"FBGA code removed from database: {code}")
            dbc.close()
            await ctx.respond(embed = embed)
            return
        else:
            await ctx.respond(embed = mkerrembed("FGBA code not found in database"))
            return

    @discord.slash_command(name = "prod_code", description = "Micron FBGA Lookup - Decode production code (top row on IC)")
    async def micron_prod_code(self, ctx: discord.ApplicationContext, code: discord.Option(str, "Production code - not case sensitive", min_length = 5, max_length = 5, required = True)):
        # See Micron CSN-11 document
        code = code.upper()

        if not re.match("[A-Z0-9]+", code):
            await ctx.respond(embed = mkerrembed(f"Invalid production code"))
            return

        embed = discord.Embed(title = f"Results for {code}", color = 0x0000FF)

        # The first character is the last digit of the year, which does not really give a specific year
        yearcode = code[0]
        startyear = 199
        prodyear = ""
        try:
            while int(str(startyear) + str(yearcode)) <= datetime.now().year:
                prodyear += str(startyear) + str(yearcode) + ", "
                startyear += 1

            prodyear = prodyear[:-2]

            embed.add_field(name = "Production year", value = prodyear, inline = False)
        except:
            await ctx.respond(embed = mkerrembed(f"Invalid production code"))
            return
        
        try:
            weekcode = week_dict[code[1]]
            embed.add_field(name = "Production week range", value = f"Week {weekcode - 1} - Week {weekcode}", inline = False)
        except KeyError:
            await ctx.respond(embed = mkerrembed(f"Invalid production code"))
            return

        if re.match("[A-Z]+", code[2]):
            embed.add_field(name = "Die revision", value = code[2], inline = False)
        else:
            await ctx.respond(embed = mkerrembed(f"Invalid production code"))
            return

        try:
            embed.add_field(name = "Diffused", value = location_dict[code[3]], inline = False)
            embed.add_field(name = "Packaged", value = location_dict[code[4]], inline = False)
        except KeyError:
            await ctx.respond(embed = mkerrembed(f"Invalid production code"))
            return

        await ctx.respond(embed = embed)
        return

def setup(client):
    client.add_cog(Micron(client))