"""
Handle creation and password hashing with scrypt.
"""

import hashlib
import hmac
import re
import secrets
import sqlite3
import time
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

MIN_PASSWORD_LENGTH = 4

# scrypt parameters (N=2^14, r=8, p=1) - moderate security for demo
SCRYPT_N = 16384
SCRYPT_R = 8
SCRYPT_P = 1
KEY_LEN = 32

def create(conn: sqlite3.Connection, handle: str, password: str) -> dict:
    """
    Create a new user with the given handle and caller-chosen password.
    
    Stores a scrypt hash with a per-user salt.
    
    Args:
        conn: SQLite connection.
        handle: User handle (2-20 chars, [a-z0-9_]).
        password: Plaintext password chosen by the caller (4+ chars).
    
    Returns:
        User dict.
    
    Raises:
        ValueError: If handle or password is invalid, or the handle exists.
    """
    # Validate handle
    if not (2 <= len(handle) <= 20):
        raise ValueError("handle must be 2-20 characters")
    
    if not re.match(r"^[a-z0-9_]+$", handle):
        raise ValueError("handle may contain only lowercase letters, digits, underscore")
    
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"password must be at least {MIN_PASSWORD_LENGTH} characters")
    
    # Check if handle exists
    cur = conn.execute("SELECT handle FROM users WHERE handle = ?", (handle,))
    if cur.fetchone():
        raise ValueError("handle already exists")
    
    # Generate salt and hash
    salt = secrets.token_bytes(16)
    pw_hash = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=KEY_LEN,
    )
    
    # Store user
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO users (handle, pw_salt, pw_hash, created_at, last_call, calls) "
        "VALUES (?, ?, ?, ?, ?, 1)",
        (handle, salt, pw_hash, now, now),
    )
    conn.commit()
    
    return {
        "handle": handle,
        "created_at": now,
        "last_call": now,
        "calls": 1,
    }

def verify(conn: sqlite3.Connection, handle: str, password: str) -> bool:
    """
    Verify a handle/password combination.
    
    Args:
        conn: SQLite connection.
        handle: User handle.
        password: Plaintext password to verify.
    
    Returns:
        True if password matches, False otherwise.
    """
    # Get user record
    cur = conn.execute(
        "SELECT pw_salt, pw_hash FROM users WHERE handle = ?",
        (handle,),
    )
    row = cur.fetchone()
    if not row:
        return False
    
    salt = row["pw_salt"]
    stored_hash = row["pw_hash"]
    
    # Compute hash of provided password
    try:
        computed_hash = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=SCRYPT_N,
            r=SCRYPT_R,
            p=SCRYPT_P,
            dklen=KEY_LEN,
        )
    except Exception:
        logger.exception("scrypt failed")
        return False
    
    # Constant-time comparison
    return hmac.compare_digest(computed_hash, stored_hash)

def update_last_call(conn: sqlite3.Connection, handle: str) -> None:
    """
    Update user's last_call timestamp and increment call count.
    """
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE users SET last_call = ?, calls = calls + 1 WHERE handle = ?",
        (now, handle),
    )
    conn.commit()