# SLAG - CTCL 2024
# File: cogs/users/__init__.py
# Purpose: User profiling and birthday reminder extension
# Created: January 27, 2024
# Modified: February 18, 2024

import csv
import logging
import os
import sqlite3
import sys
import zoneinfo
from datetime import datetime, time, timedelta, timezone, tzinfo

import discord
from discord import default_permissions
from discord.errors import Forbidden, NotFound
from discord.ext import commands, tasks
from discord.ext.commands import Cog
from discord.ext.commands.errors import MemberNotFound

from lib import logger_setup, mkerrembed

sys_logger = logging.getLogger("sys_logger")

if not os.path.exists("logs/"):
    os.mkdir("logs/")

if not os.path.exists("logs/users/"):
    os.mkdir("logs/users/")

cog_logger = logger_setup("users_logger", "logs/users.log", level=logging.DEBUG)

monthdict = {
    "january": {"num": 1, "days": 31},
    "february": {"num": 2, "days": 29},
    "march": {"num": 3, "days": 31},
    "april": {"num": 4, "days": 30},
    "may": {"num": 5, "days": 31},
    "june": {"num": 6, "days": 30},
    "july": {"num": 7, "days": 31},
    "august": {"num": 8, "days": 31},
    "september": {"num": 9, "days": 30},
    "october": {"num": 10, "days": 31},
    "november": {"num": 11, "days": 30},
    "december": {"num": 12, "days": 31}
}

onlinestatus = {
    "offline": 0,
    "online": 1,
    "idle": 2,
    "dnd": 3
}

# Check if the file exists and is a valid SQLite3 database
def dbvalid(db):
    dbc = sqlite3.connect(db)
    cur = dbc.cursor()
    
    result = cur.execute("SELECT 1 FROM sqlite_master LIMIT 1").fetchone()
    dbc.close()

    if result:
        return True
    else:
        return False

class Users(Cog):
    def __init__(self, client):
        self.client = client

    @Cog.listener()
    async def on_ready(self):
        await refreshusers(self.client)
    
    @discord.slash_command(name = "birthday", description = "Set your birthday")
    async def birthday_set(self, ctx: discord.ApplicationContext,
        month: discord.Option(str, "Month of Birth", autocomplete = discord.utils.basic_autocomplete(monthdict.keys()), max_length = 9, required = True),
        day: discord.Option(int, "Day of Birth", min_value = 1, max_value = 31, required = True),
        year: discord.Option(int, "Year of Birth", min_value = 1900, max_value = (datetime.now().year - 13), required = False)):

        if day > monthdict[month]["days"]:
            ctx.respond(embed = mkerrembed(f"Invalid day parameter: {day}. Day of month must be between 1 and {monthdict[month]['days']}"))
            return

        if not month.lower() in monthdict.keys():
            await ctx.respond(embed = mkerrembed(f"Invalid month: {month.lower()}"))
            return

        month = monthdict[month.lower()]["num"]

        userid = ctx.author.id

        dbc = sqlite3.connect("data/users/usermeta.db")
        cur = dbc.cursor()

        if not year:
            year = 0

        values = (year, month, day, userid)

        cur.execute("UPDATE usermeta SET birthyear=?, birthmonth=?, birthday=? WHERE userid=?", values)
        dbc.commit()
        dbc.close()

        await ctx.respond("Birthday Set")

    @tasks.loop(time = time(0, 0, tzinfo=timezone.utc))
    async def birthday_reminder(self):
        dbc = sqlite3.connect("data/users/guildmeta.db")
        cur = dbc.cursor()

        cur.execute("SELECT birthdaychannel FROM guildmeta WHERE guildid=?", (ctx.guild.id,))

        channels = [i[0] for i in cur.fetchall()]

        dbc.close()


        if channel == 0:
            cog_logger.error(f"Birthday channel not set for guild: {ctx.guild.id}")
            await ctx.respond("Birthday channel not set")
            return

        dbc = sqlite3.connect("data/users/usermeta.db")
        cur = dbc.cursor()

        res = list(cur.execute("SELECT userid, birthyear, birthmonth, birthday FROM usermeta"))
        dbc.close()

        now = datetime.now()
        daynow = now.day
        monthnow = now.month
        yearnow = now.year

        msgcount = 0
        for user in res:
            # For anyone with a leap day birthday, just have the reminder on the 28th of February
            if user[3] == 29 and user[2] == 2:
                user[3] = 28

            if user[3] == daynow and user[2] == monthnow:
                embed = discord.Embed(title = "Happy Birthday", color = 0x00ffff)
                embed.add_field(name = "", value = f"It is the birthday of <@{user[0]}>")
                for channel in channels:
                    if self.client.get_user(user[0]) in [member.id for member in self.client.get_channel(channel).guild.members]:
                        await self.client.get_channel(channel).send(embed = embed)


    @discord.slash_command(name = "birthdayreminder", description = "Check for user birthdays")
    @default_permissions(administrator = True)
    async def birthday_forcereminder(self, ctx: discord.ApplicationContext):
        dbc = sqlite3.connect("data/users/guildmeta.db")
        cur = dbc.cursor()

        cur.execute("SELECT birthdaychannel FROM guildmeta")

        channels = [i[0] for i in cur.fetchall()]

        dbc.close()

        tmp = []
        for channel in channels:
            if channel == 0:
                cog_logger.warn(f"Birthday channel not set for guild: {ctx.guild.id}")
            else:
                tmp.append(channel)
        channels = tmp

        dbc = sqlite3.connect("data/users/usermeta.db")
        cur = dbc.cursor()

        res = list(cur.execute("SELECT userid, birthyear, birthmonth, birthday FROM usermeta"))
        dbc.close()

        now = datetime.now()
        daynow = now.day
        monthnow = now.month
        yearnow = now.year

        msgcount = 0
        for user in res:
            # For anyone with a leap day birthday, just have the reminder on the 28th of February
            if user[3] == 29 and user[2] == 2:
                user[3] = 28

            if user[3] == daynow and user[2] == monthnow:
                embed = discord.Embed(title = "Happy Birthday", color = 0x00ffff)
                embed.add_field(name = "", value = f"It is the birthday of <@{user[0]}>")
                for channel in channels:
                    if user[0] in [member.id for member in self.client.get_channel(channel).members]:
                        await self.client.get_channel(channel).send(embed = embed)
                
    @discord.slash_command(name = "birthdayconfig", description = "Configure the birthday reminder feature")
    @default_permissions(administrator = True)
    async def birthday_config(self, ctx: discord.ApplicationContext, channel: discord.Option(discord.TextChannel, "Channel to send messages in", required = True)):
        if not ctx.guild:
            ctx.respond("This command must be used in a guild")
            return
        
        dbc = sqlite3.connect("data/users/guildmeta.db")
        cur = dbc.cursor()

        cur.execute("UPDATE guildmeta SET birthdaychannel=? WHERE guildid=?", (channel.id, ctx.guild.id))

        dbc.commit()
        dbc.close()

        await ctx.respond(f"Birthday message channel set to {channel.mention}")


    @discord.slash_command(name = "userinfo", description = "Displays information about a user")
    async def userinfo(self, ctx: discord.ApplicationContext, user: discord.Option(discord.User, "User", required = False)):
        date_format = "%B %d, %Y %I:%M %p"

        # Default to the user that invoked the command
        if user is None:
            user = ctx.author
            fetched_user = await self.client.fetch_user(ctx.author.id)
        else:
            try:
                user = await ctx.guild.fetch_member(user.id)
                fetched_user = await self.client.fetch_user(user.id)
            except (MemberNotFound, NotFound):
                try:
                    user = await self.client.fetch_user(user.id)
                    fetched_user = user
                except MemberNotFound:
                    await ctx.respond(f"User {user.id} not found")
                    return
            except (AttributeError):
                # AttributeError may be raised if ctx.guild is None, such as in DMs
                user = await self.client.fetch_user(user.id)
                fetched_user = user
                

        if fetched_user.accent_colour:
            user_color = fetched_user.accent_colour
        else:
            user_color = fetched_user.color

        embed = discord.Embed(title = f"User Information for {user}", color = user_color)
        embed.set_author(name = str(user), icon_url = user.default_avatar)
        embed.set_thumbnail(url = user.display_avatar)
      
        embed.add_field(name = "Username", value = user.name, inline = True)
        if isinstance(user, discord.Member):
            embed.add_field(name = "Nickname", value = user.nick, inline = True)
        else:
            embed.add_field(name = "Global Name", value = user.display_name, inline = True)

        embed.add_field(name = "User ID", value = user.id, inline = True)

        if isinstance(user, discord.Member):
            embed.add_field(name = "Joined", value = user.joined_at.strftime(date_format), inline = False)
        
        embed.add_field(name = "Registered", value = user.created_at.strftime(date_format), inline = False)

        # Display roles
        if isinstance(user, discord.Member):
            if user in ctx.guild.members:
                members = sorted(ctx.guild.members, key=lambda m: m.joined_at)
                embed.add_field(name = "Join position", value = str(members.index(user) + 1), inline = False)
            else:
                embed.add_field(name = "Join position", value = "N/A", inline = False)

            if len(user.roles) > 1:
                role_string = ' '.join([r.mention for r in user.roles][1:])
                embed.add_field(name = "Roles [{}]".format(len(user.roles) - 1), value = role_string, inline = False)

            embed.add_field(name = "Status on Mobile", value = user.mobile_status, inline = True)
            embed.add_field(name = "Status on Desktop", value = user.desktop_status, inline = True)
            embed.add_field(name = "Status on Web", value = user.web_status, inline = True)

        embed.add_field(name = "Is bot", value = user.bot, inline = True)

        # Avoiding the use of flag bits here since it overcomplicates things and Python endianness depends on the CPU
        user_flags = ""
        if user.public_flags.staff:
            user_flags += f"User is a Discord Employee\n"
        if user.public_flags.partner:
            user_flags += f"User is a Discord Partner\n"
        if user.public_flags.hypesquad:
            user_flags += f"User is a HypeSquad Events member\n"
        if user.public_flags.bug_hunter:
            user_flags += f"User is a Bug Hunter\n"
        if user.public_flags.bug_hunter_level_2:
            user_flags += f"User is a Bug Hunter Level 2\n"
        if user.public_flags.hypesquad_bravery:
            user_flags += f"User is a HypeSquad Bravery Member\n"
        if user.public_flags.hypesquad_brilliance:
            user_flags += f"User is a HypeSquad Brilliance Member\n"
        if user.public_flags.hypesquad_balance:
            user_flags += f"User is a HypeSquad Balance Member\n"
        if user.public_flags.early_supporter:
            user_flags += f"User is an Early Supporter (Nitro before Oct 10 2018)\n"
        if user.public_flags.team_user:
            user_flags += f"User is a Team User\n"
        if user.public_flags.system:
            user_flags += f"User is a System User\n"
        if user.public_flags.verified_bot:
            user_flags += f"User is a Verified Bot\n"
        if user.public_flags.verified_bot_developer:
            user_flags += f"User is an Early Verified Bot Developer\n"
        if user.public_flags.discord_certified_moderator:
            user_flags += f"User is a Discord Certified Moderator\n"
        if user.public_flags.active_developer:
            user_flags += f"User is an Active Developer\n"

        embed.add_field(name = "User Flags", value = user_flags, inline = False)
        
        embed.add_field(name = "User URL", value = user.jump_url, inline = False)

        await ctx.respond(embed = embed)
    
    @Cog.listener()
    async def on_guild_join(self, guild):
        cog_logger.info("Bot joined guild, refreshing users")
        refreshusers()

    @Cog.listener()
    async def on_message(self, msg):
        # Do not log messages from bots
        if msg.author.bot:
            return

        author = msg.author.id
        userdb = await checkuserindb(self.client, author)

        if not userdb:
            return

        timestamp = datetime.timestamp(datetime.now())
        msgid = msg.id
        channelid = msg.channel.id
        if msg.guild:
            guildid = msg.guild.id
        else:
            guildid = 0
        isdeleted = 0
        msgcontent = msg.content

        entry = (timestamp, msgid, channelid, guildid, isdeleted, msgcontent)

        dbc = sqlite3.connect(userdb)
        cur = dbc.cursor()

        cur.execute("INSERT OR IGNORE INTO usermessages VALUES(?, ?, ?, ?, ?, ?)", entry)

        dbc.commit()
        dbc.close()

    @Cog.listener()
    async def on_raw_message_delete(self, payload):
        # FIXME: This retrieves the message from the bot cache, making the use of the "raw" version of this event pointless
        message = self.client.get_message(payload.message_id)
        if not message:
            cog_logger.info(f"Message not found: {payload.message_id}")
            return

        userdb = checkuserindb(self.client, message.author.id)
        if not userdb:
            cog_logger.info(f"User not found: {message.author.id}")

        dbc = sqlite3.connect(userdb)
        cur = dbc.cursor()

        cur.execute("UPDATE usermessages SET isdeleted = 1 WHERE msgid = ?", (message.id,))

        dbc.commit()
        dbc.close()

    @Cog.listener()
    async def on_presence_update(self, before, after):
        userid = after.id

        # Once again, do not log bots
        if after.bot:
            return

        userdb = await checkuserindb(self.client, userid)

        if not userdb:
            return

        activities = after.activities

        timestamp = datetime.timestamp(datetime.now())
        status_mobile = onlinestatus[str(after.mobile_status)]
        status_desktop = onlinestatus[str(after.desktop_status)]
        status_web = onlinestatus[str(after.web_status)]
        userstatus = ""
        userstatusemoji = ""
        activitytype = ""
        activityurl = ""
        activityname = ""
        activitydetails = ""
        activityid = 0
        activitysessionid = 0
        activityemoji = ""
        spotifytitle = ""
        spotifyalbum = ""
        spotifyartist = ""
        spotifyid = ""

        if activities != ():
            for activity in activities:
                if isinstance(activity, discord.CustomActivity):
                    userstatus = activity.name
                    if activity.emoji:
                        userstatusemoji = activity.emoji.name
                elif isinstance(activity, discord.Activity):
                    if activity.type == discord.ActivityType.playing:
                        activitytype = "playing"
                    elif activity.type == discord.ActivityType.streaming:
                        activitytype = "streaming"
                    elif activity.type == discord.ActivityType.listening:
                        activitytype = "listening"
                    elif activity.type == discord.ActivityType.watching:
                        activitytype = "watching"

                    if activity.url:
                        activityurl = activity.url
                    if activity.name:
                        activityname = activity.name
                    if activity.details:
                        activitydetails = activity.details
                    if activity.application_id:
                        activityid = activity.application_id
                    if activity.emoji:
                        activityemoji = activity.emoji
                elif isinstance(activity, discord.Spotify):
                    spotifytitle = activity.title
                    spotifyalbum = activity.album
                    spotifyartist = activity.artist
                    spotifyid = activity.track_id


        entry = (timestamp, status_web, status_mobile, status_desktop, userstatus, userstatusemoji, activitytype, activityurl, activityname, activitydetails, activityid, activitysessionid, activityemoji, spotifytitle, spotifyalbum, spotifyartist, spotifyid)

        dbc = sqlite3.connect(userdb)
        cur = dbc.cursor()

        cur.execute("INSERT INTO useractivity VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", entry)
        dbc.commit()
        dbc.close()

    
    @discord.slash_command(name = "welcomeconfig", description = "Configure the welcomer feature")
    @default_permissions(administrator = True)
    async def birthday_config(self, ctx: discord.ApplicationContext, channel: discord.Option(discord.TextChannel, "Channel to send messages in", required = True)):
        if not ctx.guild:
            ctx.respond("This command must be used in a guild")
            return
        
        dbc = sqlite3.connect("data/users/guildmeta.db")
        cur = dbc.cursor()

        cur.execute("UPDATE guildmeta SET welcomerchannel=? WHERE guildid=?", (channel.id, ctx.guild.id))

        dbc.commit()
        dbc.close()

        await ctx.respond(f"Welcome message channel set to {channel.mention}")

    @Cog.listener()
    async def on_member_join(self, member):
        checkuserindb(self.client, member.id)
        embed = discord.Embed(title="Welcome {member.name}", color=0x00ff00)
        embed.set_thumbnail(url = member.display_avatar)
        
        dbc = sqlite3.connect("data/users/guildmeta.db")
        cur = dbc.cursor()
        cur.execute("SELECT welcomerchannel FROM guildmeta WHERE guildid=?", (member.guild.id))
        res = cur.fetchone()[0]
        dbc.close()

        if res and res != 0:
            await self.client.get_channel(res).send(embed = embed)
        else:
            cog_logger.warn("Welcome message channel not set or guild not found")

    @Cog.listener()
    async def on_member_remove(self, member):
        embed = discord.Embed(title="Member Left: {member.name}", color=0xff0000)
        embed.set_thumbnail(url = member.display_avatar)  

        dbc = sqlite3.connect("data/users/guildmeta.db")
        cur = dbc.cursor()
        cur.execute("SELECT welcomerchannel FROM usermeta WHERE guildid=?", (member.guild.id))
        res = cur.fetchone()[0]
        dbc.close()

        if res and res != 0:
            await self.client.get_channel(res).send(embed = embed)
        else:
            cog_logger.warn("Welcome message channel not set or guild not found")

async def checkuserindb(client, userid, adduser = True):
    try:
        user = await client.fetch_user(userid)
    except discord.NotFound:
        cog_logger.warn(f"User not found")
        return False

    if user.bot:
        cog_logger.warn(f"User {userid} is a bot")
        return False

    dbc = sqlite3.connect("data/users/usermeta.db")
    cur = dbc.cursor()

    cur.execute("SELECT userid, userdb, blacklisted FROM usermeta WHERE userid=?", (userid,))
    usermeta = cur.fetchone()
    dbc.close()

    userdb = f"data/users/user_{userid}.db"

    if usermeta:
        # Return database file path
        return userdb
    else:
        if adduser:
            cog_logger.info(f"Creating database for {userid}")

            if os.path.exists(userdb):
                cog_logger.info(f"Database for {userid} exists but not present in usermeta, removing")
                os.remove(userdb)

            with open("cogs/users/userdb.sql") as f:
                userdbschema = f.read()

            dbc = sqlite3.connect(userdb)
            cur = dbc.cursor()
            cur.executescript(userdbschema)
            dbc.commit()
            dbc.close()

            values = (userid, userdb, user.created_at, 0, 0, 0, 0)

            dbc = sqlite3.connect("data/users/usermeta.db")
            cur = dbc.cursor()
            # Fields for the one table in "usermeta.db" should be set UNIQUE for this to work properly. See https://www.sqlite.org/lang_conflict.html.
            cur.execute("INSERT OR IGNORE INTO usermeta VALUES(?, ?, ?, ?, ?, ?, ?)", values)
            dbc.commit()
            dbc.close()
            return userdb
        else:
            cog_logger.warn(f"User {userid} not found in database")
            dbc.close()
            return False

async def gathermessages(client):
    users = {}
    for channel in client.get_all_channels():
        if isinstance(channel, discord.TextChannel):
            try:
                messages = await channel.history(limit = None).flatten()
            except Forbidden:
                sys_logger.warn(f"HTTP 403 encountered when processing channel: {channel.id}")
            else:
                for message in messages:
                    if not message.author.id in users.keys():
                        users[message.author.id] = []

                    users[message.author.id].append(message)

    cog_logger.info("Messages collected from Discord. Now adding messages to databases.")

    messagecount = 0
    for user, messages in users.items():
        messagecount += 1
        userdb = await checkuserindb(client, user)
        if not userdb:
            continue
        dbc = sqlite3.connect(userdb)
        cur = dbc.cursor()

        for message in messages:
            timestamp = datetime.timestamp(message.created_at)
            msgid = message.id
            channelid = message.channel.id
            guildid = message.guild.id
            isdeleted = 0
            msgcontent = message.content

            values = (timestamp, msgid, channelid, guildid, isdeleted, msgcontent)

            cur.execute("INSERT OR IGNORE INTO usermessages VALUES(?, ?, ?, ?, ?, ?)", values)

        dbc.commit()
        dbc.close()

    cog_logger.info("Message gathering done")

# Refresh the users while not collecting message history
async def refreshusers(client):
    memberids = []

    for guild in client.guilds:
        for member in guild.members:
            if member.id not in memberids and member.bot == False:
                memberids.append(member.id)

    for memberid in memberids:
        await checkuserindb(client, memberid)

def setup(client):
    if not os.path.exists("data/users/"):
        os.mkdir("data/users/")

    if not os.path.exists(f"data/users/guildmeta.db"):
        dbc = sqlite3.connect(f"data/users/guildmeta.db")
        cur = dbc.cursor()
        with open("cogs/users/guildmeta.sql") as f:
            cur.executescript(f.read())
        dbc.commit()
    else:
        dbc = sqlite3.connect(f"data/users/guildmeta.db")
        cur = dbc.cursor()
    
    for guild in client.guilds:
        cur.execute("SELECT guildid FROM guildmeta WHERE guildid=?", (guild.id,))
        res = cur.fetchone()

        if not res:
            cog_logger.info(f"Database does not exist for guild: {guild.id}")
            values = (guild.id, 0, 0)
            cur.execute("INSERT OR IGNORE INTO guildmeta VALUES(?, ?, ?)", values)

    dbc.commit()
    dbc.close()

    if not os.path.exists(f"data/users/usermeta.db"):
        dbc = sqlite3.connect(f"data/users/usermeta.db")
        cur = dbc.cursor()
        with open("cogs/users/usermeta.sql") as f:
            cur.executescript(f.read())
        dbc.commit()
        dbc.close()
    
    client.add_cog(Users(client))
    
