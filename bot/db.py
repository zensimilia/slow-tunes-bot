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
    except sqlite3.Error as error:
        log.critical("Can't connect to the database - %s", error)
        raise error


def send_query(query: str, args: tuple | None = None) -> sqlite3.Cursor:  # type: ignore
    """Send query to database and return cursor object."""

    if not args:
        args = tuple()

    with sqlite_connect(config.DB_FILE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, args)
            conn.commit()
        except sqlite3.Error as error:
            log.error("Can't send query to the database - %s", error)
            raise error
        return cursor


def init_sqlite():
    """Init sqlite database file and create tables."""

    # match table
    send_query(
        '''CREATE TABLE IF NOT EXISTS match (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original CHAR NOT NULL UNIQUE,
        slowed CHAR NOT NULL,
        user_id INTEGER NOT NULL,
        private BOOLEAN DEFAULT 1 NOT NULL,
        forbidden BOOLEAN DEFAULT 0 NOT NULL);'''
    )

    # likes table
    send_query(
        '''CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id INEGER NOT NULL,
        user_id INTEGER NOT NULL,
        UNIQUE (match_id, user_id));'''
    )


async def insert_match(original: str, slowed: str, user_id: int) -> int | None:
    """Insert row with original and slowed file ids."""

    query = send_query(
        '''INSERT INTO
        match (original, slowed, user_id, private, forbidden)
        VALUES (?, ?, ?, ?, ?);''',
        (original, slowed, user_id, True, False),
    )
    return query.lastrowid


async def get_match(original: str) -> tuple | None:
    """Get row of pair original and slowed file ids."""

    query = send_query(
        'SELECT * FROM match WHERE original = ?;',
        (original,),
    )
    return query.fetchone()


async def get_random_match() -> tuple | None:
    """Get random row from match table."""

    query = send_query(
        '''SELECT * FROM match
        WHERE private = ? AND forbidden = ?
        ORDER BY RANDOM() LIMIT 1;''',
        (
            False,
            False,
        ),
    )
    return query.fetchone()


async def toggle_private(idc: int, is_private: bool = True) -> None:
    """Toggle private status for slowed row."""

    send_query(
        'UPDATE match SET private = ? WHERE id = ?;',
        (
            is_private,
            idc,
        ),
    )


async def toggle_forbidden(idc: int, is_forbidden: bool = True) -> None:
    """Toggle forbidden status for slowed row."""

    send_query(
        'UPDATE match SET forbidden = ? WHERE id = ?;',
        (
            is_forbidden,
            idc,
        ),
    )


async def toggle_like(toggle: bool, match_id: int, user_id: int) -> None:
    """Toggle likes for /random audio."""

    if toggle:
        send_query(
            'INSERT OR IGNORE INTO likes (match_id, user_id) VALUES (?, ?);',
            (
                match_id,
                user_id,
            ),
        )
    else:
        send_query(
            'DELETE FROM likes WHERE match_id = ? AND user_id = ?;',
            (
                match_id,
                user_id,
            ),
        )


async def is_liked(match_id: int, user_id: int) -> bool:
    """Check if audio is already liked."""

    query = send_query(
        'SELECT * FROM likes WHERE match_id = ? AND user_id = ?;',
        (
            match_id,
            user_id,
        ),
    )

    return bool(query.fetchone())
