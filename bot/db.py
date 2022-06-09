import sqlite3

from bot.config import AppConfig
from bot.utils.logger import get_logger

log = get_logger()
config = AppConfig()


class Error(Exception):
    """Custom exception class for database."""


def sqlite_connect(db_file: str) -> sqlite3.Connection:
    """Connect to the database file."""
    try:
        conn = sqlite3.connect(db_file, check_same_thread=False)
        conn.execute("pragma journal_mode=wal;")
        return conn
    except sqlite3.Error as err:
        log.critical("Can't connect to the database - %s", err)
        raise Error from err


def send_query(query: str, args: tuple | None = None) -> sqlite3.Cursor:  # type: ignore
    """Send query to database and return cursor object."""

    if not args:
        args = tuple()

    with sqlite_connect(config.DB_FILE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, args)
            conn.commit()
        except sqlite3.Error as err:
            log.error("Can't send query to the database - %s", err)
            raise Error from err
        return cursor


def init_sqlite():
    """Init sqlite database file and create tables."""

    send_query(
        '''CREATE TABLE IF NOT EXISTS match (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original CHAR,
        slowed CHAR,
        user_id INTEGER);'''
    )


async def insert_match(original: str, slowed: str, user_id: int) -> int | None:
    """Insert row with original and slowed file ids."""

    query = send_query(
        'INSERT INTO match (original, slowed, user_id) VALUES (?, ?, ?);',
        (
            original,
            slowed,
            user_id,
        ),
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
