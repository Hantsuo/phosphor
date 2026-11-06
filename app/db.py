"""
SQLite connection factory and schema bootstrap.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DB_PATH = Path("phosphor.db")
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  handle      TEXT PRIMARY KEY,
  pw_salt     BLOB NOT NULL,
  pw_hash     BLOB NOT NULL,
  created_at  TEXT NOT NULL,
  last_call   TEXT NOT NULL,
  calls       INTEGER NOT NULL DEFAULT 1
);
"""

def connect() -> sqlite3.Connection:
    """
    Connect to SQLite database and ensure schema exists.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    conn.commit()
    return conn

def drop_all() -> None:
    """
    Drop all tables (for tests).
    """
    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.execute("DROP TABLE IF EXISTS users")
        conn.commit()
        conn.close()
        DB_PATH.unlink()