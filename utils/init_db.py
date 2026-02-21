import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT,
    difficulty TEXT,
    score INTEGER,
    total INTEGER
)
""")

conn.commit()
conn.close()

print("Database initialized successfully")
