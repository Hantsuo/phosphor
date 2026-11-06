"""
The machine sysop.

For now the digest is deterministic and computed from the board itself: no model,
no network, no surprises at 3am. A later pass can hand these lines to a model.
"""

import logging
import sqlite3
import time
from collections import Counter

logger = logging.getLogger(__name__)

WINDOW_SECONDS = 24 * 60 * 60


def digest(conn: sqlite3.Connection) -> list[str]:
    """
    Summarise the last 24 hours of posts as screen-ready lines.

    Deterministic for the same data, ordered by post count then name.
    """
    cutoff = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - WINDOW_SECONDS))
    rows = conn.execute(
        "SELECT p.handle, b.name FROM posts p JOIN boards b ON b.id = p.board_id "
        "WHERE p.created_at >= ?",
        (cutoff,),
    ).fetchall()

    if not rows:
        return ["NO POSTS IN THE LAST 24 HOURS.", "THE BOARD IS LISTENING."]

    handles = Counter(row["handle"] for row in rows)
    boards = Counter(row["name"] for row in rows)

    busiest_name, busiest_count = sorted(boards.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    voices = [name for name, _ in sorted(handles.items(), key=lambda kv: (-kv[1], kv[0]))[:3]]

    post_word = "POST" if len(rows) == 1 else "POSTS"
    caller_word = "CALLER" if len(handles) == 1 else "CALLERS"

    return [
        f"LAST 24 HOURS: {len(rows)} {post_word} FROM {len(handles)} {caller_word}.",
        f"BUSIEST BOARD: {busiest_name} ({busiest_count}).",
        "VOICES: " + ", ".join(voices) + ".",
        "",
        "THE LINES ARE OPEN.",
    ]
