"""
Tests for presence tracking.
"""

import pytest
from app import presence

@pytest.fixture(autouse=True)
def reset_presence() -> None:
    """Reset presence state before each test."""
    presence._reset_for_tests()

def test_add_caller() -> None:
    """Add a caller to online list."""
    pid = presence.add_caller("testuser")
    assert isinstance(pid, str)
    assert len(pid) == 16  # 8 bytes hex = 16 chars
    assert presence.get_online_count() == 1
    assert "testuser" in presence.get_online_handles()

def test_remove_caller() -> None:
    """Remove a caller from online list."""
    pid = presence.add_caller("testuser")
    assert presence.get_online_count() == 1
    
    presence.remove_caller(pid)
    assert presence.get_online_count() == 0
    assert "testuser" not in presence.get_online_handles()

def test_remove_nonexistent_caller() -> None:
    """Removing nonexistent caller should not crash."""
    presence.remove_caller("nonexistent")
    # Should not raise error

def test_get_online_count() -> None:
    """Get correct online count."""
    assert presence.get_online_count() == 0
    
    pid1 = presence.add_caller("user1")
    assert presence.get_online_count() == 1
    
    pid2 = presence.add_caller("user2")
    assert presence.get_online_count() == 2
    
    presence.remove_caller(pid1)
    assert presence.get_online_count() == 1
    
    presence.remove_caller(pid2)
    assert presence.get_online_count() == 0

def test_get_online_handles() -> None:
    """Get set of online handles."""
    assert len(presence.get_online_handles()) == 0
    
    pid1 = presence.add_caller("user1")
    pid2 = presence.add_caller("user2")
    
    handles = presence.get_online_handles()
    assert isinstance(handles, set)
    assert len(handles) == 2
    assert "user1" in handles
    assert "user2" in handles
    
    presence.remove_caller(pid1)
    handles = presence.get_online_handles()
    assert len(handles) == 1
    assert "user2" in handles