import os
import sqlite3
from sqlite3 import Connection, Cursor, DatabaseError, OperationalError

from bot.config import AppConfig
from bot.utils.logger import get_logger

log = get_logger()
config = AppConfig()

DATABASE = os.path.join(config.DATA_DIR, "database.db")


def sqlite_connect(db_file: str) -> Connection:
    """Connect to the database file."""
    try:
        conn = sqlite3.connect(db_file, check_same_thread=False)
        conn.execute("pragma journal_mode=wal;")
        return conn
    except (DatabaseError, OperationalError) as err:
        log.error(err)
        raise Exception("Database error!") from err


def send_query(query: str, args: tuple | None = None) -> Cursor:
    """Send query to database and return cursor object."""

    if not args:
        args = tuple()

    try:
        with sqlite_connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                args,
            )
            conn.commit()
            return cursor
    except (DatabaseError, OperationalError) as err:
        log.error(err)
        raise Exception("Database error!") from err


def init_sqlite():
    """Init sqlite database file and create tables."""

    send_query(
        'CREATE TABLE IF NOT EXISTS match '
        '(id INTEGER PRIMARY KEY AUTOINCREMENT, original CHAR, slowed CHAR);'
    )


async def insert_match(original: str, slowed: str) -> int | None:
    """Insert row with original and slowed file ids."""

    query = send_query(
        'INSERT INTO match (original, slowed) VALUES (?, ?);',
        (original, slowed),
    )
    return query.lastrowid


async def get_match(original: str) -> tuple | None:
    """Get row of pair original and slowed file ids."""

    query = send_query(
        'SELECT * FROM match WHERE original=?;',
        (original,),
    )
    return query.fetchone()


async def get_random_match() -> tuple | None:
    """Get random row from match table."""

    query = send_query('SELECT slowed FROM match ORDER BY RANDOM() LIMIT 1;')
    return query.fetchone()
