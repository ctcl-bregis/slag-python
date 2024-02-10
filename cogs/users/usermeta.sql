CREATE TABLE usermeta (
    userid INT,
    userdb VARCHAR(255),
    register_date REAL,
    blacklisted INT,
    UNIQUE(userid, userdb)
);