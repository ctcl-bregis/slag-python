# SLAG - CTCL 2024
# File: cogs/users/__init__.py
# Purpose: User profiling and birthday reminder cog
# Created: January 27, 2024
# Modified: February 9, 2024

import csv
import logging
import os
import sqlite3
import zoneinfo
from datetime import datetime, timedelta, timezone, tzinfo

import discord
from discord.errors import NotFound
from discord.ext import commands
from discord.ext.commands import Cog
from discord.ext.commands.errors import MemberNotFound

from lib import mkerrembed, logger_setup

sys_logger = logging.getLogger("sys_logger")

if not os.path.exists("logs/users/"):
    os.mkdir("logs/users/")

cog_logger = logger_setup("users_logger", "logs/users.log", level=logging.DEBUG)

monthdict = {
    "January": {"num": "1", "days": 31},
    "February": {"num": "2", "days": 29},
    "March": {"num": "3", "days": 31},
    "April": {"num": "4", "days": 30},
    "May": {"num": "5", "days": 31},
    "June": {"num": "6", "days": 30},
    "July": {"num": "7", "days": 31},
    "August": {"num": "8", "days": 31},
    "September": {"num": "9", "days": 30},
    "October": {"num": "10", "days": 31},
    "November": {"num": "11", "days": 30},
    "December": {"num": "12", "days": 31}
}

onlinestatus = {
    "offline": 0,
    "online": 1,
    "idle": 2,
    "dnd": 3
}

tzs = zoneinfo.available_timezones()

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
        self.members = []

        if not os.path.exists("data/users/"):
            os.mkdir("data/users/")

    def refreshusers(self):
        # Store user IDs so the code does not compare the entire member object
        memberids = []
        self.members = []

        for guild in self.client.guilds:
            for member in guild.members:
                if member.id not in memberids and member.bot == False:
                    self.members.append(member)

        if not os.path.exists(f"data/users/usermeta.db"):
            dbc = sqlite3.connect(f"data/users/usermeta.db")
            cur = dbc.cursor()
            with open("cogs/users/usermeta.sql") as f:
                cur.executescript(f.read())
        else:
            dbc = sqlite3.connect(f"data/users/usermeta.db")
            cur = dbc.cursor()

        values = []
        for member in self.members:
            values.append((member.id, f"data/users/user_{member.id}.db", member.created_at))
    
        cur.execute("SELECT * FROM usermeta")
        metacount = len(cur.fetchall())

        cog_logger.info(f"{len(self.members)} unique members found while usermeta has {metacount} entries")

        # Fields for the one table in "usermeta.db" should be set UNIQUE for this to work properly. See https://www.sqlite.org/lang_conflict.html.
        cur.executemany("INSERT OR IGNORE INTO usermeta VALUES(?, ?, ?)", values)
        dbc.commit()
        dbc.close()

        with open("cogs/users/userdb.sql") as f:
            userdbschema = f.read()

        for usermeta in values:
            if os.path.exists(usermeta[1]) and not dbvalid(usermeta[1]):
                cog_logger.info(f"Database for {usermeta[0]} invalid, removing")
                os.remove(usermeta[1])
                
            if not os.path.exists(usermeta[1]):
                cog_logger.info(f"Database for {usermeta[0]} missing or was invalid, creating one now")
                dbc = sqlite3.connect(usermeta[1])
                cur = dbc.cursor()
                cur.executescript(userdbschema)
                dbc.commit()
                dbc.close()

    async def checkuserindb(self, userid, adduser = True):
        try:
            user = await self.client.fetch_user(userid)
        except discord.NotFound:
            cog_logger.warn(f"User not found")
            return False

        if user.bot:
            cog_logger.warn(f"User {userid} is a bot")
            return False

        dbc = sqlite3.connect("data/users/usermeta.db")
        cur = dbc.cursor()

        cur.execute("SELECT userid, userdb FROM usermeta WHERE userid=?", (userid,))
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

                values = (userid, userdb, user.created_at)

                dbc = sqlite3.connect("data/users/usermeta.db")
                cur = dbc.cursor()
                # Fields for the one table in "usermeta.db" should be set UNIQUE for this to work properly. See https://www.sqlite.org/lang_conflict.html.
                cur.execute("INSERT OR IGNORE INTO usermeta VALUES(?, ?, ?)", values)
                dbc.commit()
                dbc.close()
                return userdb
            else:
                cog_logger.warn(f"User {userid} not found in database")
                dbc.close()
                return False

    async def gathermessages(self):
        users = {}
        for channel in self.client.get_all_channels():
            if isinstance(channel, discord.TextChannel):
                messages = await channel.history(limit = None).flatten()
                for message in messages:
                    if not message.author.id in users.keys():
                        users[message.author.id] = []

                    users[message.author.id].append(message)

        cog_logger.info("Messages collected from Discord. Now adding messages to databases.")

        messagecount = 0
        for user, messages in users.items():
            messagecount += 1
            userdb = await self.checkuserindb(user)
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

    @Cog.listener()
    async def on_ready(self):
        self.refreshusers()
        
    @discord.slash_command(name = "gathermessages", description = "Gathers all messages of every guild and logs them")
    async def gather_messages_command(self, ctx: discord.ApplicationContext):
        await ctx.respond("This may take a very, very, long time. If you become light headed from thirst, feel free to pass out. An intubation associate will be dispatched to revive you with peptic salve and adrenaline.")
        await self.gathermessages()
        await ctx.respond("Gathering done")
        return

    @discord.slash_command(name = "birthdayset", description = "Set your birthday")
    async def birthday_set(self, ctx: discord.ApplicationContext, 
        tz: discord.Option(str, "User Timezone", autocomplete = discord.utils.basic_autocomplete(tzs), required = True),
        day: discord.Option(int, "Day of Birth", min_value = 1, max_value = 31, required = True),
        month: discord.Option(str,"Month of Birth", autocomplete = discord.utils.basic_autocomplete(monthdict.keys()), max_length = 9, required = True),
        year: discord.Option(int, "Year of Birth", min_value = 1900, max_value = (datetime.now().year - 13), required = False)):

        if day > monthdict[month]["days"]:
            ctx.respond(embed = mkerrembed(f"Invalid day parameter: {day}. Day of month must be between 1 and {monthdict[month]['days']}"))
            return

        if not month.lower() in monthdict.keys():
            ctx.respond(embed = mkerrembed(f"Invalid month: {day}"))
            return

        await ctx.respond("")


    @discord.slash_command(name = "birthdaysetuser", description = "Set the birthday of another user")
    async def birthday_set_user(self, ctx: discord.ApplicationContext):

        await ctx.respond("")

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
                    await ctx.respond(f"User {user} not found")
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
        user_flags += f"User is a Discord Employee: {user.public_flags.staff}\n"
        user_flags += f"User is a Discord Partner: {user.public_flags.partner}\n"
        user_flags += f"User is a HypeSquad Events member: {user.public_flags.hypesquad}\n"
        user_flags += f"User is a Bug Hunter: {user.public_flags.bug_hunter}\n"
        user_flags += f"User is a Bug Hunter Level 2: {user.public_flags.bug_hunter_level_2}\n"
        user_flags += f"User is a HypeSquad Bravery Member: {user.public_flags.hypesquad_bravery}\n"
        user_flags += f"User is a HypeSquad Brilliance Member: {user.public_flags.hypesquad_brilliance}\n"
        user_flags += f"User is a HypeSquad Balance Member: {user.public_flags.hypesquad_balance}\n"
        user_flags += f"User is an Early Supporter (Nitro before Oct 10 2018): {user.public_flags.early_supporter}\n"
        user_flags += f"User is a Team User: {user.public_flags.team_user}\n"
        user_flags += f"User is a System User: {user.public_flags.system}\n"
        user_flags += f"User is a Verified Bot: {user.public_flags.verified_bot}\n"
        user_flags += f"User is an Early Verified Bot Developer: {user.public_flags.verified_bot_developer}\n"
        user_flags += f"User is a Discord Certified Moderator: {user.public_flags.discord_certified_moderator}\n"
        user_flags += f"User is an Active Developer: {user.public_flags.active_developer}\n"

        embed.add_field(name = "User Flags", value = user_flags, inline = False)
        
        embed.add_field(name = "User URL", value = user.jump_url, inline = False)

        await ctx.respond(embed = embed)
    
    @Cog.listener()
    async def on_member_join(self, member):
        # FIXME: calling this on a member join instead of manually adding the user is likely extremely inefficient
        self.refreshusers()

    @Cog.listener()
    async def on_guild_join(self, guild):
        self.refreshusers()

    @Cog.listener()
    async def on_message(self, msg):
        # Do not log messages from bots
        if msg.author.bot:
            return

        author = msg.author.id
        userdb = await self.checkuserindb(author)

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

        cur.execute("INSERT INTO usermessages VALUES(?, ?, ?, ?, ?, ?)", entry)

        dbc.commit()
        dbc.close()

    @Cog.listener()
    async def on_raw_message_delete(self, payload):
        # FIXME: This retrieves the message from the bot cache, making the use of the "raw" version of this event pointless
        message = self.client.get_message(payload.message_id)
        if not message:
            cog_logger.INFO(f"Message not found: {payload.message_id}")
            return

        userdb = self.checkuserindb(message.author.id)
        if not userdb:
            cog_logger.INFO(f"User not found: {message.author.id}")

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

        userdb = await self.checkuserindb(userid)

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

def setup(client):
    


    client.add_cog(Users(client))