import os
import sqlite3
from sqlite3 import Connection, DatabaseError

from bot.config import AppConfig

config = AppConfig()

DATABASE = os.path.join(config.DATA_DIR, "database.db")


def sqlite_connect(db_file: str) -> Connection:
    """Connect to the database file."""
    try:
        conn = sqlite3.connect(db_file, check_same_thread=False)
        conn.execute("pragma journal_mode=wal;")
        return conn
    except DatabaseError as err:
        print(err)  # TODO: logger
        raise Exception("Database error") from err


def init_sqlite():
    """Init sqlite database file and create tables."""

    with sqlite_connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS match '
            '(id INTEGER PRIMARY KEY AUTOINCREMENT, original CHAR, slowed CHAR);'
        )
        conn.commit()


async def insert_match(original: str, slowed: str) -> int | None:
    """Insert row with original and slowed file ids."""

    with sqlite_connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO match (original, slowed) VALUES (?, ?);',
            (original, slowed),
        )
        conn.commit()
        return cursor.lastrowid


async def get_match(original: str) -> tuple | None:
    """Get row of pair original and slowed file ids."""

    with sqlite_connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM match WHERE original=?;',
            (original,),
        )
        return cursor.fetchone()


async def get_random_match() -> tuple | None:
    """Get random row from match table."""

    with sqlite_connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT slowed FROM match ORDER BY RANDOM() LIMIT 1;')
        return cursor.fetchone()
