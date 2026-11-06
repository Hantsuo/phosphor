"""
Boards and posts: the part of the BBS people actually came for.
"""

import logging
import sqlite3
import time

logger = logging.getLogger(__name__)

DEFAULT_BOARDS = [
    ("lobby", "THE LOBBY", "say something, anything", 1),
    ("graveyard", "DEAD TECH OBITUARIES", "what died, and why we miss it", 2),
    ("sightings", "SIGHTINGS", "things seen on the wire", 3),
    ("sysop", "SYSOP'S DESK", "notices from the machine", 4),
]

MAX_SUBJECT = 60
MAX_BODY_LINES = 20
MAX_BODY_COL = 70


def seed(conn: sqlite3.Connection) -> None:
    """Insert the default boards once. Safe to call on every boot."""
    for board_id, name, blurb, position in DEFAULT_BOARDS:
        conn.execute(
            "INSERT OR IGNORE INTO boards (id, name, blurb, position) VALUES (?, ?, ?, ?)",
            (board_id, name, blurb, position),
        )
    conn.commit()


def all_boards(conn: sqlite3.Connection) -> list[dict]:
    """Return every board with its post count, in seeded order."""
    rows = conn.execute(
        "SELECT b.id, b.name, b.blurb, "
        "(SELECT COUNT(*) FROM posts p WHERE p.board_id = b.id) AS posts "
        "FROM boards b ORDER BY b.position"
    ).fetchall()
    return [dict(row) for row in rows]


def board(conn: sqlite3.Connection, board_id: str) -> dict | None:
    """Return one board with its post count, or None."""
    row = conn.execute(
        "SELECT b.id, b.name, b.blurb, "
        "(SELECT COUNT(*) FROM posts p WHERE p.board_id = b.id) AS posts "
        "FROM boards b WHERE b.id = ?",
        (board_id,),
    ).fetchone()
    return dict(row) if row else None


def recent(conn: sqlite3.Connection, board_id: str, limit: int = 20) -> list[dict]:
    """Return the newest posts for a board, oldest first."""
    rows = conn.execute(
        "SELECT id, handle, subject, created_at FROM posts "
        "WHERE board_id = ? ORDER BY id DESC LIMIT ?",
        (board_id, limit),
    ).fetchall()
    return [dict(row) for row in reversed(rows)]


def post(conn: sqlite3.Connection, post_id: int) -> dict | None:
    """Return one full post, or None."""
    row = conn.execute(
        "SELECT id, board_id, handle, subject, body, created_at FROM posts WHERE id = ?",
        (post_id,),
    ).fetchone()
    return dict(row) if row else None


def add(conn: sqlite3.Connection, board_id: str, handle: str, subject: str, body: str) -> int:
    """Store a post and return its id. Raises ValueError on an empty subject."""
    subject = (subject or "").strip()[:MAX_SUBJECT]
    if not subject:
        raise ValueError("subject is required")

    lines = [line[:MAX_BODY_COL] for line in (body or "").splitlines()][:MAX_BODY_LINES]
    while lines and not lines[-1].strip():
        lines.pop()

    now = time.strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute(
        "INSERT INTO posts (board_id, handle, subject, body, created_at) VALUES (?, ?, ?, ?, ?)",
        (board_id, handle, subject, "\n".join(lines), now),
    )
    conn.commit()
    logger.info("post %s by %s on %s", cur.lastrowid, handle, board_id)
    return int(cur.lastrowid)
