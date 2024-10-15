CREATE TABLE usermeta (
    userid INT,
    userdb VARCHAR(255),
    register_date REAL,
    blacklisted INT,
    birthyear INT,
    birthmonth INT,
    birthday INT,
    UNIQUE(userid, userdb)
);