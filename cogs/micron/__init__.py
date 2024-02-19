# SLAG - CTCL 2024
# File: cogs/micron/__init__.py
# Purpose: Micron FBGA decoder and code lookup cog
# Created: February 6, 2024
# Modified: February 17, 2024

import asyncio
import os
import re
import sqlite3
from datetime import datetime

import aiohttp
import discord
from bs4 import BeautifulSoup
from discord.errors import NotFound
from discord.ext import commands
from discord.ext.commands import Cog
from discord.ext.commands.errors import CommandOnCooldown

from lib import hsize, logger_setup, mkerrembed

cog_logger = logger_setup("cog_micron", "logs/sys_log.log")

micron_url = "https://www.micron.com/support/tools-and-utilities/fbga"

# Info from numdram.xlsx May 4, 2023
dram_types_dict = {
    "40A": {"type": "DDR4 SDRAM", "voltage": "1.2", "vtokenlength": 1, "islpddr": False},
    "41J": {"type": "DDR3 SDRAM", "voltage": "1.5", "vtokenlength": 1, "islpddr": False},
    "41K": {"type": "DDR3 SDRAM", "voltage": "1.35", "vtokenlength": 1, "islpddr": False},
    "41L": {"type": "LPDDR2 Mobile", "voltage": "1.2", "vtokenlength": 1, "islpddr": True},
    "44K": {"type": "RLDRAM3", "voltage": "1.35", "vtokenlength": 1, "islpddr": False},
    "46V": {"type": "DDR1 SDRAM", "voltage": "2.5", "vtokenlength": 1, "islpddr": False},
    "46H": {"type": "DDR1 SDRAM", "voltage": "1.8", "vtokenlength": 2, "islpddr": False},
    "47H": {"type": "DDR2 SDRAM", "voltage": "1.35", "vtokenlength": 1, "islpddr": False},
    "48H": {"type": "SDRAM", "voltage": "1.8", "vtokenlength": 1, "islpddr": False},
    "48H": {"type": "LPSDRAM Mobile", "voltage": "1.8", "vtokenlength": 1, "islpddr": True},
    "48L": {"type": "SDR SDRAM", "voltage": "3.3", "vtokenlength": 2, "islpddr": False},
    "49H": {"type": "RLDRAM2", "voltage": "1.8", "vtokenlength": 1, "islpddr": False},
    "51J": {"type": "GDDR5", "voltage": "1.5", "vtokenlength": 1, "islpddr": False},
    "51K": {"type": "GDDR5", "voltage": "1.4", "vtokenlength": 1, "islpddr": False},
    "52H": {"type": "LPDDR3 Mobile", "voltage": "1.8", "vtokenlength": 2, "islpddr": False},
    "52K": {"type": "DDR3L Mobile", "voltage": "1.35", "vtokenlength": 1, "islpddr": False},
    "52L": {"type": "LPDDR3 Mobile", "voltage": "1.2", "vtokenlength": 1, "islpddr": True},
    "53B": {"type": "LPDRR4 Mobile", "voltage": "1.1", "vtokenlength": 1, "islpddr": True},
    "53D": {"type": "LPDDR4X Mobile", "voltage": "1.1", "vtokenlength": 1, "islpddr": True},
    "53E": {"type": "LPDDR4 Mobile", "voltage": "1.1", "vtokenlength": 1, "islpddr": True},
    "53E": {"type": "LPDDR4X Mobile", "voltage": "1.1", "vtokenlength": 1, "islpddr": True},
    "58K": {"type": "GDDR5", "voltage": "1.35", "vtokenlength": 1, "islpddr": False},
    "58K": {"type": "GDDR5X", "voltage": "1.35", "vtokenlength": 1, "islpddr": False},
    "58M": {"type": "GDDR5X", "voltage": "1.25", "vtokenlength": 1, "islpddr": False},
    "60B": {"type": "DDR5 SDRAM", "voltage": "1.1", "vtokenlength": 1, "islpddr": False},
    "61A": {"type": "GDDR6", "voltage": "1.2", "vtokenlength": 1, "islpddr": False},
    "61K": {"type": "GDDR6", "voltage": "1.35", "vtokenlength": 1, "islpddr": False},
    "61K": {"type": "GDDR6X", "voltage": "1.35", "vtokenlength": 1, "islpddr": False},
    "61M": {"type": "GDDR6", "voltage": "1.25", "vtokenlength": 1, "islpddr": False},
    "61M": {"type": "GDDR6X", "voltage": "1.25", "vtokenlength": 1, "islpddr": False},
    "62F": {"type": "LPDDR5 Mobile", "voltage": "1.05", "vtokenlength": 1, "islpddr": True},
    "62F": {"type": "LPDDR5X Mobile", "voltage": "1.05", "vtokenlength": 1, "islpddr": True},
    "68A": {"type": "GDDR7", "voltage": "1.2", "vtokenlength": 1, "islpddr": False},
    "68B": {"type": "GDDR7", "voltage": "1.1", "vtokenlength": 1, "islpddr": False},
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

depths = {
    "1K": 1 * 1024,
    "2K": 2 * 1024,
    "4K": 4 * 1024,
    "8K": 8 * 1024,
    "16K": 16 * 1024,
    "32K": 32 * 1024,
    "64K": 64 * 1024,
    "128K": 128 * 1024,
    "256K": 256 * 1024,
    "512K": 512 * 1024,
    "1M": 1 * 1024 * 1024,
    "2M": 2 * 1024 * 1024,
    "4M": 4 * 1024 * 1024,
    "8M": 8 * 1024 * 1024,
    "16M": 16 * 1024 * 1024,
    "32M": 32 * 1024 * 1024,
    "64M": 64 * 1024 * 1024,
    "128M": 128 * 1024 * 1024,
    "256M": 256 * 1024 * 1024,
    "512M": 512 * 1024 * 1024,
    "1G": 1 * 1024 * 1024 * 1024,
    "2G": 2 * 1024 * 1024 * 1024,
    "4G": 4 * 1024 * 1024 * 1024,
    "8G": 8 * 1024 * 1024 * 1024,
    "16G": 16 * 1024 * 1024 * 1024,
    "24G": 24 * 1024 * 1024 * 1024,
    "32G": 32 * 1024 * 1024 * 1024,
    "48G": 48 * 1024 * 1024 * 1024,
    "64G": 64 * 1024 * 1024 * 1024,
    "128G": 128 * 1024 * 1024 * 1024,
    "256G": 256 * 1024 * 1024 * 1024,
    "512G": 512 * 1024 * 1024 * 1024,
}

# It is important to have the list in this order because of the use of startswith(). For example: 128M16 could be selected with .startswith("128M1").
widths = [
    "16",
    "9",
    "8",
    "4",
    "2",
    "1"
]

def devinfo(pn):
    # TODO: Flash part decoding, Elpida (legacy) part decoding

    # ===========================
    # Micron DRAM device decoding 
    # ===========================
    # devfamily is to keep track what type of device the part number relates to (DRAM, flash, etc.)
    devfamily = None
    for key, value in dram_types_dict.items():
        if pn.startswith("MT" + key):
            devtype = value["type"]
            devfamily = "dram"
            devvoltage = value["voltage"]
            # If the Voltage Mark Token is either 1 or 2 letters
            devtypevtoken = value["vtokenlength"]
            break

    if devfamily == "dram":
        if devtypevtoken == 2:
            pn = pn[6:]
        else:
            pn = pn[5:]

        for key, value in depths.items():
            for width in widths:
                densitycode = key + width
                if pn.startswith(densitycode):
                    pn = pn[len(densitycode):]
                    density = hsize(value * int(width))

    # This seems to be consistent across product types (DRAM, flash, etc.)
    if pn[-2:-1] == ":":
        dierev = pn[-1]

    if not devfamily:
        return False
    
    return {"devtype": devtype, "density": density, "dierev": dierev}

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
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{micron_url}?fbga={code}") as response:
                    status = response.status
                    text = await response.text()

            if status == 200:
                soup = BeautifulSoup(text, 'html.parser')
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
                await ctx.respond(embed = mkerrembed(f"HTTP error: {status}"))
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
        elif pn.startswith("HYB"):
            # It is highly unlikely that a code would resolve to an Infineon/Qimonda part but it is here just in case
            embed.add_field(name = "Part Number - Qimonda legacy part", value = pn, inline = False)
        else:
            embed.add_field(name = "Part Number", value = pn, inline = False)
            devinfodict = devinfo(pn)
            if devinfodict:
                embed.add_field(name = "Type", value = devinfodict["devtype"], inline = False)
                embed.add_field(name = "Density", value = devinfodict["density"], inline = False)
                embed.add_field(name = "Die Revision", value = devinfodict["dierev"], inline = False)

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