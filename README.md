<div align="center">
  <img src="slag_logo.svg" style="width: 50%" alt="SLAG"/>
</div>

# SLAG "Channel Catfish"
SLAG is a bot for the Discord chat service. It was created for small guilds such as school clubs.

SLAG is an initialism of "Security, Logging, Analytics and General Purpose". The logo is based off from this, with the goal of the bot to be "solid as steel". 

Unlike many other bots, there are no donations, premium or voting.

## Cogs
SLAG is modularized using the Pycord library's Cog feature

### base
'base' is the Cog that provides commands for showing information about the bot

### micron
The 'micron' Cog adds the ability to search the part number for an FBGA code (second 5-character row) on Micron Technology flash and DRAM parts. 

The Cog also adds a command that can decode the production code (first 5-character row).

To lower the amount of requests sent to the Micron website, the Cog makes use of an SQLite3 database that stores known FBGA codes and their associated part number.

### welcome
This Cog adds a "welcomer" that sends a welcome message to a specified channel. 

### users
This Cog is for the automatic profiling and logging of Discord users that shares the same guilds as the bot.

The Birthday feature is part of this Cog due to its use of the same database files.

## Requirements

### Host operating system
This bot is meant to be hosted in a Linux environment. Some features may not be available on other platforms.

### Python version
The bot is currently developed under a Python 3.10 environment, functionality might not be available on older or newer versions.

### Dependencies
As of January 31, 2024, the bot now uses pycord instead of discord.py

## Legal
This project is licensed under the MIT Licesnse. See LICENSE for the full text.

All product names, logos, brands, trademarks and registered trademarks are property of their respective owners. All company, product and service names used are for identification purposes only. Use of these names, trademarks and brands does not imply endorsement.

## Privacy
Instances of the bot hosted by CTCL (myself) follow the privacy policy [here](https://ctcl-tech.com/privacy/).

The bot itself does not attempt to send any data to any external server. All data collected by the bot stays on the host.