# SLAG - CTCL 2024
# File: cogs/log.py
# Purpose: Message and action logging
# Created: January 27, 2024
# Modified: January 31, 2024

# NOTE: This cog is unrelated to the discord.py and sys_logger loggers. This cog is for recording user and guild activity.

import csv
import os
import logging
from datetime import datetime

from discord.errors import NotFound
from discord.ext import commands
from discord.ext.commands import Cog
from discord.ext.commands.errors import MemberNotFound

sys_logger = logging.getLogger("sys_logger")

# Reused code from ctclsite-python
def csv_log(data, header, filename):
    # print(list(data.keys()))
    # print(log_header[1:])

    validated_data = {}
    # Convert everything to a string and replace any strings that are too long
    for key, value in data.items():
        if len(str(value)) < 16384:
            validated_data[key] = str(value)
        else:
            validated_data[key] = f"!! {key} too long !!"

    # This is probably very inefficient
    if not os.path.exists(filename):
        with open(filename, "w", encoding='UTF8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames = header)
            writer.writeheader()

    # Timestamp is separate from the sent data
    now = datetime.now()
    timestr = now.strftime("%Y-%b-%d-%k-%M-%S").lower()
    validated_data["time"] = timestr

    # TODO: Speed this up?
    #count = 0
    #with open(log_latest, "r") as f:
    #    for count, line in enumerate(f):
    #        pass

    # If the log is currently too long, back it up
    #if count > log_max_length:
    #    arc_name = f"{log_dir}log_{timestr}"

        # Rename current log file before adding it to the archive
        #os.rename(log_latest, f"{arc_name}.csv")

        # Create tar file with gzip compression
        #tar = tarfile.open(f"{arc_name}.tar.gz", "w:gz", compresslevel=9)
        #tar.add(f"{arc_name}.csv")
        #tar.close()

        # Remove the old log file
        #os.remove(f"{arc_name}.csv")

        # Create another current log file
        #with open(log_latest, "w", encoding='UTF8', newline='') as f:
        #    writer = csv.writer(f)
        #    writer.writerow(log_header)

    if not os.path.exists(filename):
        writer = csv.DictWrtier(f, fieldnames = header)
        writer.writeheader()

    with open(filename, "a") as f:
        writer = csv.DictWriter(f, fieldnames = header)
        writer.writerow(validated_data)


msg_log_header = ["time", "id", "content", "author", "channel", "channelid"]


class Logger(Cog):
    def __init__(self, client):
        self.client = client

        if not os.path.exists("logs"):
            os.mkdir("logs/")
        
        if not os.path.exists("logs/dm/"):
            os.mkdir("logs/dm/")
        

    @Cog.listener()
    async def on_message(self, message):
        message_data = {}
    
        message_data["id"] = message.id
        message_data["content"] = message.content
        message_data["author"] = message.author.name
        try: 
            message_data["channel"] = message.channel.name
        except:
            message_data["channel"] = ""
        message_data["channelid"] = message.channel.id
    
        # Check and create directories
        # This is done with on_message so the bot does not have to be restarted on guild join
        # TODO: Having this in on_message is inefficient, figure out how to automatically restart the bot on guild join
        if not os.path.exists("logs/"):
            sys_logger.info("logs directory does not exist. Creating one now.")
            os.mkdir("logs/")
    
        # Do not log messages from bots
        if not message.author.bot:
            if message.guild:
                for guild in self.client.guilds:
                    if not os.path.exists(f"logs/{message.guild.id}"):
                        sys_logger.info(f"Directory for guild \"{message.guild.id}\" does not exist. Creating one now.")
                        os.mkdir(f"logs/{message.guild.id}")
        
                csv_log(message_data, msg_log_header, f"logs/{str(message.guild.id)}/{str(message.author.id)}_msg_log.csv")
            else:
                csv_log(message_data, msg_log_header, f"logs/dm/{message.author.name}_msg_log.csv")


def setup(client):
    client.add_cog(Logger(client))