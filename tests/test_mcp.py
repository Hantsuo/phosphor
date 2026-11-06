"""
Tests for the MCP interface and the human escalation queue.
"""

import importlib
import os
import sqlite3

import pytest

from app import boards, db


@pytest.fixture
def board_db(tmp_path, monkeypatch) -> str:
    """A file-backed board database for the MCP tools to open themselves."""
    path = tmp_path / "phosphor-test.db"
    monkeypatch.setenv("PHOSPHOR_DB", str(path))
    monkeypatch.setenv("PHOSPHOR_HANDLE", "scout")
    conn = sqlite3.connect(path)
    conn.executescript(db.SCHEMA)
    conn.commit()
    boards.seed(conn)
    conn.close()
    return str(path)


def test_agent_can_post_and_read_back(board_db: str) -> None:
    """An agent posts through MCP and a human could read the same row."""
    from app import mcp_server

    importlib.reload(mcp_server)

    result = mcp_server.post_message("lobby", "handoff ready", "the crawl finished, 42 pages", needs_human=False)
    assert result["handle"] == "scout"
    assert result["id"] > 0

    posts = mcp_server.read_board("lobby")
    assert [p["subject"] for p in posts] == ["handoff ready"]

    full = mcp_server.read_post(result["id"])
    assert full["body"] == "the crawl finished, 42 pages"


def test_escalation_reaches_the_human_queue(board_db: str) -> None:
    """page_sysop lands in the escalation list until a human clears it."""
    from app import mcp_server

    importlib.reload(mcp_server)

    mcp_server.page_sysop("approve the deploy?")

    conn = sqlite3.connect(board_db, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    waiting = boards.escalations(conn)
    assert len(waiting) == 1
    assert waiting[0]["subject"] == "a decision is needed"

    assert boards.resolve(conn, waiting[0]["id"]) is True
    assert boards.escalations(conn) == []
    conn.close()


def test_inbox_only_returns_mentions(board_db: str) -> None:
    """inbox filters on @handle so an agent can poll cheaply."""
    from app import mcp_server

    importlib.reload(mcp_server)

    mcp_server.post_message("lobby", "for scout", "hey @scout take a look")
    mcp_server.post_message("lobby", "for nobody", "just thinking out loud")

    messages = mcp_server.inbox()
    assert [m["subject"] for m in messages] == ["for scout"]


def test_unknown_board_is_a_clean_error(board_db: str) -> None:
    """A bad board id raises ValueError instead of touching the database."""
    from app import mcp_server

    importlib.reload(mcp_server)

    with pytest.raises(ValueError):
        mcp_server.post_message("nowhere", "x", "y")
