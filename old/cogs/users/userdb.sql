-- Table for the information of a user that can change
CREATE TABLE userinfo (
    timestamp REAL,
    username VARCHAR(64),
    nickname VARCHAR(64),
    birthday_tz VARCHAR(64),
    birthday_day INT,
    birthday_month INT,
    birthday_year INT
);

-- Table of the log of status and activity of the user
CREATE TABLE useractivity (
    timestamp REAL,
    status_web INT,
    status_mobile INT,
    status_desktop INT,
    userstatus VARCHAR(128),
    userstatusemoji VARCHAR(32),
    activitytype VARCHAR(12),
    activityurl VARCHAR(128),
    activityname VARCHAR(128),
    activitydetails VARCHAR(128),
    activityid INT,
    activitysessionid INT,
    activityemoji VARCHAR(32),
    spotifytitle VARCHAR(128),
    spotifyalbum VARCHAR(128),
    spotifyartist VARCHAR(128),
    spotifyid VARCHAR(22)
);

-- Log of messages of the user
CREATE TABLE usermessages (
    timestamp REAL,
    msgid INT,
    channelid INT,
    guildid INT,
    isdeleted INT,
    msgcontent VARCHAR(4000),
    UNIQUE(msgid)
);

-- Log of edits done to messages
CREATE TABLE messageedit (
    timestamp REAL,
    msgid INT,
    channelid INT,
    guildid INT
    oldcontent VARCHAR(4000),
    newcontent VARCHAR(4000)
);