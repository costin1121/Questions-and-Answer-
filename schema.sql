CREATE TABLE USERS(
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    NAME TEXT NOT NULL,
    PASSWORD TEXT NOT NULL,
    EXPERT BOOLEAN NOT NULL,
    ADMIN BOOLEAN NOT NULL
);


CREATE TABLE QUESTIONS(
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    QUESTION_TEXT TEXT NOT NULL,
    ANSWER_TEXT TEXT,
    ASKEB_BY_ID INTEGER NOT NULL,
    EXPERT_ID INTEGER NOT NULL
);