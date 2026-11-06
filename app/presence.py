"""
In-memory presence tracking for online callers.
"""

import secrets
import logging
from typing import Dict, Set, Optional

logger = logging.getLogger(__name__)

# In-memory store of online callers
_online: Dict[str, str] = {}  # presence_id -> handle

def _reset_for_tests() -> None:
    """Reset online list (for testing only)."""
    global _online
    _online = {}

def add_caller(handle: str) -> str:
    """
    Add a caller to the online list.
    
    Args:
        handle: User handle.
    
    Returns:
        Unique presence ID for this session.
    """
    presence_id = secrets.token_hex(8)
    _online[presence_id] = handle
    logger.info(f"Caller {handle} joined (now {len(_online)} online)")
    return presence_id

def remove_caller(presence_id: str) -> None:
    """
    Remove a caller from the online list.
    
    Args:
        presence_id: Presence ID returned by add_caller.
    """
    if presence_id in _online:
        handle = _online.pop(presence_id)
        logger.info(f"Caller {handle} left (now {len(_online)} online)")

def get_online_count() -> int:
    """
    Get number of callers online.
    """
    return len(_online)

def get_online_handles() -> Set[str]:
    """
    Get set of all online handles.
    """
    return set(_online.values())