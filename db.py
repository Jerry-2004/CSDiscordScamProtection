import sqlite3

DB_NAME = "data/bot_data.db"

def connect():
    return sqlite3.connect(DB_NAME)

def create_tables():
    with connect() as conn:
        c = conn.cursor()
        # Table to store scam reports
        c.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reported_user_id TEXT NOT NULL,
                reporter_user_id TEXT NOT NULL,
                reason TEXT,
                proof TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                votes INTEGER DEFAULT 0
            );
        """)

        # Table to store banned users
        c.execute("""
            CREATE TABLE IF NOT EXISTS banned_users (
                user_id TEXT PRIMARY KEY,
                banned_on DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)