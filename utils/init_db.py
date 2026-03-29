import sqlite3, os
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database.db")
conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()
cur.executescript("""
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS performance (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL DEFAULT 0,
    subject     TEXT,
    focus       TEXT,
    mastered    TEXT,
    difficulty  TEXT,
    score       INTEGER,
    total       INTEGER,
    percentage  REAL,
    level       TEXT,
    timestamp   TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS topic_scores (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    performance_id INTEGER,
    topic          TEXT,
    correct        INTEGER,
    total          INTEGER,
    accuracy       REAL,
    FOREIGN KEY (performance_id) REFERENCES performance(id)
);
CREATE TABLE IF NOT EXISTS knowledge_snapshots (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    subject    TEXT NOT NULL,
    nodes_json TEXT,
    edges_json TEXT,
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, subject),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")
conn.commit(); conn.close()
print("Database initialised.")
