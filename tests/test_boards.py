"""
Tests for boards, posts, and the sysop digest.
"""

import sqlite3
import time

import pytest

from app import boards, db, sysop


@pytest.fixture
def temp_db() -> sqlite3.Connection:
    """A fresh in-memory database with the real schema."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(db.SCHEMA)
    conn.commit()
    yield conn
    conn.close()


def test_seed_is_idempotent(temp_db: sqlite3.Connection) -> None:
    """Seeding twice still leaves exactly four boards."""
    boards.seed(temp_db)
    boards.seed(temp_db)

    listed = boards.all_boards(temp_db)
    assert len(listed) == 4
    assert [b["id"] for b in listed] == ["lobby", "graveyard", "sightings", "sysop"]
    assert all(b["posts"] == 0 for b in listed)


def test_add_and_read_back(temp_db: sqlite3.Connection) -> None:
    """A post survives a round trip, newest last."""
    boards.seed(temp_db)
    first = boards.add(temp_db, "lobby", "guest", "hello", "first post\nsecond line")
    second = boards.add(temp_db, "lobby", "guest", "again", "second post")

    recent = boards.recent(temp_db, "lobby")
    assert [p["id"] for p in recent] == [first, second]
    assert recent[0]["subject"] == "hello"

    full = boards.post(temp_db, first)
    assert full["body"] == "first post\nsecond line"


def test_subject_and_body_limits(temp_db: sqlite3.Connection) -> None:
    """Subjects truncate at 60, bodies at 20 lines of 70 columns."""
    boards.seed(temp_db)
    long_subject = "s" * 90
    long_body = "\n".join("x" * 90 for _ in range(30))

    post_id = boards.add(temp_db, "lobby", "guest", long_subject, long_body)
    stored = boards.post(temp_db, post_id)

    assert len(stored["subject"]) == boards.MAX_SUBJECT
    lines = stored["body"].split("\n")
    assert len(lines) == boards.MAX_BODY_LINES
    assert all(len(line) <= boards.MAX_BODY_COL for line in lines)


def test_empty_subject_is_rejected(temp_db: sqlite3.Connection) -> None:
    """A post with no subject raises and stores nothing."""
    boards.seed(temp_db)
    with pytest.raises(ValueError):
        boards.add(temp_db, "lobby", "guest", "   ", "body")
    assert boards.recent(temp_db, "lobby") == []


def test_digest_without_posts(temp_db: sqlite3.Connection) -> None:
    """An empty board says so in two lines."""
    boards.seed(temp_db)
    lines = sysop.digest(temp_db)
    assert len(lines) == 2
    assert "NO POSTS" in lines[0]


def test_digest_counts_posts_and_voices(temp_db: sqlite3.Connection) -> None:
    """The digest counts today's posts and names up to three handles."""
    boards.seed(temp_db)
    boards.add(temp_db, "lobby", "guest", "one", "body")
    boards.add(temp_db, "lobby", "guest", "two", "body")
    boards.add(temp_db, "graveyard", "tester", "three", "body")

    lines = sysop.digest(temp_db)
    joined = "\n".join(lines)

    assert "3 POSTS" in joined
    assert "2 CALLERS" in joined
    assert "THE LOBBY" in joined
    assert "guest" in joined and "tester" in joined


def test_digest_ignores_old_posts(temp_db: sqlite3.Connection) -> None:
    """Posts older than 24 hours do not count."""
    boards.seed(temp_db)
    post_id = boards.add(temp_db, "lobby", "guest", "old", "body")
    old = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - 2 * 86400))
    temp_db.execute("UPDATE posts SET created_at = ? WHERE id = ?", (old, post_id))
    temp_db.commit()

    lines = sysop.digest(temp_db)
    assert "NO POSTS" in lines[0]
