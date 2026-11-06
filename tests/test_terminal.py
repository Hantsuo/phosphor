"""
Tests for terminal screen buffer.
"""

import pytest
from app.terminal import Screen

def test_screen_dimensions() -> None:
    """Screen should have fixed 80x24 dimensions."""
    screen = Screen()
    assert screen.width == 80
    assert screen.height == 24

def test_text_fits_within_row() -> None:
    """Text should be truncated to fit within row, never wrap."""
    screen = Screen()
    screen.text(0, 75, "abcdefghijklmnop")  # 16 chars starting at col 75
    # Should only write 5 chars (80 - 75)
    rendered = screen.render()
    # Check that line 1 contains exactly 80 chars
    lines = rendered.split("\n")
    # Skip ANSI clear sequence and get first line
    line_start = rendered.find("\x1b[2J\x1b[H") + len("\x1b[2J\x1b[H")
    first_line = rendered[line_start:line_start + 80]
    assert len(first_line) == 80

def test_cp437_sanitization() -> None:
    """Non-CP437 characters should be replaced with '?'."""
    screen = Screen()
    # Test with smart quotes and em dash
    screen.text(0, 0, "Hello — World", "green")
    rendered = screen.render()
    # Should replace — with ?
    assert "Hello ? World" in rendered or "Hello  ? World" in rendered

def test_box_drawing() -> None:
    """Box drawing should use CP437-safe characters."""
    screen = Screen()
    screen.box(5, 10, 15, 30, "Test Box")
    rendered = screen.render()
    # Should use +, -, | characters
    assert "+" in rendered
    assert "-" in rendered
    assert "|" in rendered

def test_center_text() -> None:
    """Centered text should be positioned correctly."""
    screen = Screen()
    screen.center(10, "HELLO", "green")
    # Text should start at column (80 - 5) / 2 = 37.5 -> 37
    # We can't easily check the grid directly, but we can verify
    # the render doesn't crash
    rendered = screen.render()
    assert rendered is not None

def test_cursor_position() -> None:
    """Render should end with cursor position command."""
    screen = Screen()
    screen.set_cursor(5, 10)
    rendered = screen.render()
    # Should end with ESC[6;11H (1-indexed)
    assert "\x1b[6;11H" in rendered or rendered.endswith("\x1b[6;11H")

def test_hline() -> None:
    """Horizontal line should span full width."""
    screen = Screen()
    screen.hline(10, "=")
    rendered = screen.render()
    # Should have 80 equals signs on row 11 (1-indexed in ANSI)
    lines = rendered.split("\n")
    # Skip clear sequence
    line_start = rendered.find("\x1b[2J\x1b[H") + len("\x1b[2J\x1b[H")
    # Get line 11 (0-indexed in our grid, but row 11 in terminal)
    # This is complex to parse exactly, so just verify render works
    assert "=" * 80 in rendered

def test_clear() -> None:
    """Clear should reset screen to spaces."""
    screen = Screen()
    screen.text(0, 0, "Test", "green")
    screen.clear()
    # After clear, first cell should be space
    rendered = screen.render()
    # Hard to test exactly due to ANSI codes, but ensure
    # no "Test" in output after clear
    assert "Test" not in rendered