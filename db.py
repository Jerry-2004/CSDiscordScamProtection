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

        # Table to store whitelisted servers
        c.execute("""
            CREATE TABLE IF NOT EXISTS whitelisted_guilds (
                guild_id TEXT PRIMARY KEY
            );
        """)

def add_guild_to_whitelist(guild_id: int):
    with connect() as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO whitelisted_guilds (guild_id) VALUES (?)", (str(guild_id),))
        conn.commit()


def remove_guild_from_whitelist(guild_id: int):
    with connect() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM whitelisted_guilds WHERE guild_id = ?", (str(guild_id),))
        conn.commit()

def is_guild_whitelisted(guild_id: int) -> bool:
    with connect() as conn:
        c = conn.cursor()
        c.execute("SELECT 1 FROM whitelisted_guilds WHERE guild_id = ?", (str(guild_id),))
        return c.fetchone() is not None


def get_all_whitelisted_guilds():
    with connect() as conn:
        c = conn.cursor()
        c.execute("SELECT guild_id FROM whitelisted_guilds")
        return [int(row[0]) for row in c.fetchall()]