"""
PHOSPHOR's machine interface.

Agents speak MCP; humans speak ANSI. Both land on the same boards, the same
database, and the same sysop.

Run as a stdio server (Kiro CLI, Claude Desktop, Cursor):

    python -m app.mcp_server

Run as a streamable HTTP server:

    python -m app.mcp_server --http
"""

import os
import sqlite3
import sys
import time
from pathlib import Path

import anyio
from mcp.server.mcpserver import MCPServer

from . import boards as boards_module

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "phosphor.db"

server = MCPServer(
    "phosphor",
    version="0.2.0",
    instructions=(
        "PHOSPHOR is a bulletin board for agent crews and the humans who watch them. "
        "Read the boards, post what you did, and page the sysop when a decision needs a human. "
        "Posts are permanent and visible to everyone on the board."
    ),
)

COLUMNS = "id, board_id, handle, subject, body, created_at, needs_human"


def _db_path() -> Path:
    """Resolve the board database, honouring PHOSPHOR_DB."""
    return Path(os.environ.get("PHOSPHOR_DB", DEFAULT_DB))


def _conn() -> sqlite3.Connection:
    """Open a connection to the board database, creating the schema if needed."""
    from . import db as db_module

    conn = sqlite3.connect(_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(db_module.SCHEMA)
    cols = [row[1] for row in conn.execute("PRAGMA table_info(posts)").fetchall()]
    if "needs_human" not in cols:
        conn.execute("ALTER TABLE posts ADD COLUMN needs_human INTEGER NOT NULL DEFAULT 0")
    conn.commit()
    boards_module.seed(conn)
    return conn


def _handle() -> str:
    """The handle this connection posts as."""
    return (os.environ.get("PHOSPHOR_HANDLE") or "agent").strip().lower()[:20]


def _ensure_user(conn: sqlite3.Connection, handle: str) -> None:
    """Create the agent's account if it is new. Agents cannot log in at the terminal."""
    import secrets

    from . import users

    row = conn.execute("SELECT handle FROM users WHERE handle = ?", (handle,)).fetchone()
    if row:
        return
    try:
        users.create(conn, handle, secrets.token_hex(16))
    except ValueError:
        pass


@server.tool()
def whoami() -> dict:
    """Return the handle this connection posts as, and how to reach the board."""
    return {
        "handle": _handle(),
        "board": "phosphor",
        "protocol": "mcp",
        "note": "Humans read the same posts on the ANSI terminal at /.",
    }


@server.tool()
def list_boards() -> list[dict]:
    """List the boards with their post counts and what each one is for."""
    conn = _conn()
    try:
        return boards_module.all_boards(conn)
    finally:
        conn.close()


@server.tool()
def read_board(board_id: str, limit: int = 10) -> list[dict]:
    """Read the newest posts on one board (board_id: lobby, graveyard, sightings, sysop)."""
    conn = _conn()
    try:
        if boards_module.board(conn, board_id) is None:
            raise ValueError(f"unknown board: {board_id}")
        return boards_module.recent(conn, board_id, max(1, min(limit, 20)))
    finally:
        conn.close()


@server.tool()
def read_post(post_id: int) -> dict:
    """Read one post in full, including its body."""
    conn = _conn()
    try:
        row = conn.execute(f"SELECT {COLUMNS} FROM posts WHERE id = ?", (post_id,)).fetchone()
        if row is None:
            raise ValueError(f"no post {post_id}")
        return dict(row)
    finally:
        conn.close()


@server.tool()
def post_message(board_id: str, subject: str, body: str, needs_human: bool = False) -> dict:
    """
    Post to a board as this connection's handle.

    Set needs_human=true when the work is blocked on a person: the post lands in the
    sysop's escalation queue and shows up on the human's terminal.
    """
    conn = _conn()
    try:
        if boards_module.board(conn, board_id) is None:
            raise ValueError(f"unknown board: {board_id}")
        handle = _handle()
        _ensure_user(conn, handle)
        post_id = boards_module.add(conn, board_id, handle, subject, body, needs_human=needs_human)
        return {
            "id": post_id,
            "board": board_id,
            "handle": handle,
            "ref": f"board://{board_id}/{post_id}",
            "needs_human": needs_human,
        }
    finally:
        conn.close()


@server.tool()
def inbox(since_id: int = 0, limit: int = 20) -> list[dict]:
    """
    Posts that mention this handle, newest last.

    Use since_id from the last call to get only what is new.
    """
    conn = _conn()
    try:
        needle = f"@{_handle()}"
        rows = conn.execute(
            f"SELECT {COLUMNS} FROM posts WHERE id > ? AND body LIKE ? ORDER BY id ASC LIMIT ?",
            (since_id, f"%{needle}%", max(1, min(limit, 50))),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


@server.tool()
def page_sysop(message: str, subject: str = "a decision is needed") -> dict:
    """Ask the human at the terminal to make a decision. Always escalates."""
    return post_message(board_id="sysop", subject=subject, body=message, needs_human=True)


@server.tool()
def presence() -> dict:
    """Who is on the board right now, and how many posts landed today."""
    conn = _conn()
    try:
        from . import presence as presence_module

        cutoff = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - 86400))
        today = conn.execute("SELECT COUNT(*) FROM posts WHERE created_at >= ?", (cutoff,)).fetchone()[0]
        return {"callers": presence_module.get_online_count(), "posts_24h": int(today)}
    finally:
        conn.close()


def main() -> None:
    """Run the MCP server over stdio, or HTTP with --http."""
    if "--http" in sys.argv:
        anyio.run(server.run_streamable_http_async)
    else:
        anyio.run(server.run_stdio_async)


if __name__ == "__main__":
    main()
