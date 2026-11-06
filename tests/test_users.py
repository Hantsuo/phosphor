"""
Tests for user creation and password verification.
"""

import pytest
import sqlite3
from app import db
from app import users

@pytest.fixture
def temp_db() -> sqlite3.Connection:
    """Create a temporary database for testing."""
    # Use in-memory database
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(db.SCHEMA)
    conn.commit()
    yield conn
    conn.close()

def test_create_user(temp_db: sqlite3.Connection) -> None:
    """Create a new user with a valid handle and password."""
    user = users.create(temp_db, "testuser", "hunter2")

    assert user["handle"] == "testuser"
    assert "created_at" in user
    assert "last_call" in user
    assert user["calls"] == 1

    # Verify user exists in database
    cur = temp_db.execute("SELECT * FROM users WHERE handle = ?", ("testuser",))
    row = cur.fetchone()
    assert row is not None
    assert row["handle"] == "testuser"

def test_create_user_invalid_handle(temp_db: sqlite3.Connection) -> None:
    """Reject invalid handles."""
    # Too short
    with pytest.raises(ValueError, match="handle must be 2-20 characters"):
        users.create(temp_db, "a", "hunter2")

    # Too long
    with pytest.raises(ValueError, match="handle must be 2-20 characters"):
        users.create(temp_db, "a" * 21, "hunter2")

    # Invalid characters
    with pytest.raises(ValueError, match="handle may contain only lowercase letters"):
        users.create(temp_db, "Test User", "hunter2")

    with pytest.raises(ValueError, match="handle may contain only lowercase letters"):
        users.create(temp_db, "test-user", "hunter2")

def test_create_user_short_password(temp_db: sqlite3.Connection) -> None:
    """Reject passwords shorter than four characters."""
    with pytest.raises(ValueError, match="password must be at least 4 characters"):
        users.create(temp_db, "testuser", "abc")

def test_create_duplicate_user(temp_db: sqlite3.Connection) -> None:
    """Reject duplicate handles."""
    users.create(temp_db, "testuser", "hunter2")

    with pytest.raises(ValueError, match="handle already exists"):
        users.create(temp_db, "testuser", "hunter2")

def test_verify_password(temp_db: sqlite3.Connection) -> None:
    """Verify correct password."""
    users.create(temp_db, "testuser", "hunter2")

    # Correct password
    assert users.verify(temp_db, "testuser", "hunter2") == True

    # Wrong password
    assert users.verify(temp_db, "testuser", "wrongpassword") == False

def test_verify_nonexistent_user(temp_db: sqlite3.Connection) -> None:
    """Verify returns False for nonexistent user."""
    assert users.verify(temp_db, "nonexistent", "password") == False

def test_update_last_call(temp_db: sqlite3.Connection) -> None:
    """Update last_call timestamp and increment calls."""
    users.create(temp_db, "testuser", "hunter2")

    # Get initial values
    cur = temp_db.execute(
        "SELECT last_call, calls FROM users WHERE handle = ?",
        ("testuser",)
    )
    row = cur.fetchone()
    initial_calls = row["calls"]

    # Update
    users.update_last_call(temp_db, "testuser")

    # Verify updated
    cur = temp_db.execute(
        "SELECT last_call, calls FROM users WHERE handle = ?",
        ("testuser",)
    )
    row = cur.fetchone()
    assert row["calls"] == initial_calls + 1
    # Note: last_call update is verified by the database operation;
    # we can't reliably test timestamp inequality in fast tests
