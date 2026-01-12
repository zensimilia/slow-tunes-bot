import sqlite3

from bot.config import config
from bot.utils.u_logger import get_logger

LOG = get_logger()


class Error(Exception):
    """Custom exception class for database."""


def sqlite_connect(db_file: str) -> sqlite3.Connection:
    """Connect to the database file."""

    try:
        conn = sqlite3.connect(db_file, check_same_thread=False)
        conn.execute("pragma journal_mode=wal;")
        return conn
    except sqlite3.Error as error:
        LOG.critical("Can't connect to the database - %s", error)
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
            LOG.error("Can't send query to the database - %s", error)
            raise error
        return cursor


def execute_script(script_file: str):
    """Execute SQL script from file."""

    try:
        with open(script_file, "r", encoding="utf-8") as script:
            sql = script.read()
    except OSError as error:
        LOG.critical("Can't read from SQL script file: %s", error)
        raise SystemExit from error

    with sqlite_connect(config.DB_FILE) as conn:
        cursor = conn.cursor()
        try:
            cursor.executescript(sql)
            conn.commit()
        except sqlite3.Error as error:
            LOG.error("Can't send query to the database - %s", error)
            raise error


async def insert_match(
    original: str,
    slowed: str,
    user_id: int,
    private: bool = True,
    forbidden: bool = False,
) -> int | None:
    """Insert row with original and slowed file ids."""

    query = send_query(
        """INSERT INTO
        match (original, slowed, user_id, private, forbidden)
        VALUES (?, ?, ?, ?, ?);""",
        (
            original,
            slowed,
            user_id,
            private,
            forbidden,
        ),
    )
    return query.lastrowid


async def get_match(original: str) -> tuple | None:
    """Get row of pair original and slowed file ids."""

    query = send_query(
        "SELECT * FROM match WHERE original = ? LIMIT 1;",
        (original,),
    )
    return query.fetchone()


async def get_random_ids() -> list:
    """Get list of random public match ids."""

    query = send_query(
        """SELECT id FROM match
        WHERE private = ? AND forbidden = ?
        ORDER BY RANDOM();""",
        (
            False,
            False,
        ),
    )
    return [row[0] for row in query.fetchall()]


async def get_random_match() -> tuple | None:
    """Get random row from match table."""

    query = send_query(
        """SELECT * FROM match
        WHERE private = ? AND forbidden = ?
        ORDER BY RANDOM() LIMIT 1;""",
        (
            False,
            False,
        ),
    )
    return query.fetchone()


async def get_by_pk(table: str, pk: int) -> tuple | None:
    """Get the row by its id from a given table."""

    query = send_query(
        f"SELECT * FROM {table} WHERE id = ? LIMIT 1;",
        (pk,),
    )
    return query.fetchone()


async def toggle_private(idc: int, is_private: bool = True) -> None:
    """Toggle private status for slowed row."""

    send_query(
        "UPDATE match SET private = ? WHERE id = ?;",
        (
            is_private,
            idc,
        ),
    )


async def toggle_forbidden(idc: int, is_forbidden: bool = True) -> None:
    """Toggle forbidden status for slowed row."""

    send_query(
        "UPDATE match SET forbidden = ? WHERE id = ?;",
        (
            is_forbidden,
            idc,
        ),
    )


async def toggle_like(toggle: bool, match_id: int, user_id: int) -> None:
    """Toggle likes for /random audio."""

    if toggle:
        send_query(
            "INSERT OR IGNORE INTO likes (match_id, user_id) VALUES (?, ?);",
            (
                match_id,
                user_id,
            ),
        )
    else:
        send_query(
            "DELETE FROM likes WHERE match_id = ? AND user_id = ?;",
            (
                match_id,
                user_id,
            ),
        )


async def is_liked(match_id: int, user_id: int) -> bool:
    """Check if audio is already liked."""

    query = send_query(
        "SELECT * FROM likes WHERE match_id = ? AND user_id = ? LIMIT 1;",
        (
            match_id,
            user_id,
        ),
    )

    return bool(query.fetchone())


async def get_queue_count(user_id: int) -> int:
    """Returns cout of task in queue for user."""

    query = send_query(
        "SELECT * FROM queue WHERE user_id = ?;",
        (user_id,),
    )

    if row := query.fetchone():
        return row[2]

    return 0


async def inc_queue_count(user_id: int) -> sqlite3.Cursor:
    """Increase count for queue of user tasks."""

    return send_query(
        """INSERT OR REPLACE INTO queue
        VALUES (
            NULL,
            :user,
            COALESCE((SELECT count FROM queue WHERE user_id = :user), 0) + 1
        );""",
        (user_id,),
    )


async def dec_queue_count(user_id: int) -> sqlite3.Cursor:
    """Decrease count for queue of user tasks."""

    return send_query(
        """INSERT OR REPLACE INTO queue
        VALUES (
            NULL,
            :user_id,
            COALESCE(
                NULLIF(
                    (SELECT count FROM queue WHERE user_id = :user_id),
                    0
                ),
                1
            ) - 1
        );""",
        (user_id,),
    )


async def add_user(user_id: int, username: str) -> None:
    """Add new user to database."""

    send_query(
        """INSERT OR IGNORE INTO
        users (user_id, username)
        VALUES (?, ?);""",
        (
            user_id,
            username,
        ),
    )


async def users_count() -> int:
    """Returns count of users in database."""

    query = send_query("""SELECT COUNT(id) FROM users;""")
    return query.fetchone()[0]


async def slowed_count() -> int:
    """Returns count of slowed audios in database."""

    query = send_query("""SELECT COUNT(id) FROM match;""")
    return query.fetchone()[0]


async def random_count() -> int:
    """Returns count of public audios in database."""

    query = send_query(
        """SELECT COUNT(id) FROM match WHERE private = 0 and forbidden = 0;"""
    )
    return query.fetchone()[0]


async def get_matches(limit: int = 10, offset: int = 0) -> list | None:
    """Get rows from match table."""

    query = send_query(
        """SELECT * FROM match
        ORDER BY id DESC LIMIT ? OFFSET ?;""",
        (
            limit,
            offset,
        ),
    )
    return query.fetchall()


async def get_match_by_pk(pk: int) -> tuple | None:
    """Get the match by its id."""

    query = send_query(
        "SELECT * FROM match WHERE id = ? LIMIT 1;",
        (pk,),
    )
    return query.fetchone()
