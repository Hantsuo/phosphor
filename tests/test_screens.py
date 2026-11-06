"""
Tests for screen rendering functions.
"""

from app import screens

def test_login_screen() -> None:
    """Login screen should render without error."""
    frame = screens.login("testuser", "ERROR")
    assert isinstance(frame, str)
    assert len(frame) > 0
    assert "\x1b[2J\x1b[H" in frame  # Clear screen

def test_password_screen() -> None:
    """Password screen should render without error."""
    frame = screens.password("testuser", "WRONG PASSWORD")
    assert isinstance(frame, str)
    assert len(frame) > 0
    assert "\x1b[2J\x1b[H" in frame

def test_menu_screen() -> None:
    """Menu screen should render without error."""
    frame = screens.menu("testuser", 5, "HINT")
    assert isinstance(frame, str)
    assert len(frame) > 0
    assert "\x1b[2J\x1b[H" in frame
    
    # Menu without user
    frame = screens.menu(None, 3)
    assert isinstance(frame, str)
    assert len(frame) > 0

def test_about_screen() -> None:
    """About screen should render without error."""
    frame = screens.about()
    assert isinstance(frame, str)
    assert len(frame) > 0
    assert "\x1b[2J\x1b[H" in frame

def test_boot_function() -> None:
    """Boot function should modify screen without error."""
    from app.terminal import Screen
    
    screen = Screen()
    screens.boot(0, screen)
    
    # Should have set some text
    rendered = screen.render()
    assert len(rendered) > 0
    assert "\x1b[2J\x1b[H" in rendered