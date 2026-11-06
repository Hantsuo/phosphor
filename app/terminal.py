"""
Screen buffer for 80x24 terminal output with CP437-safe encoding.
"""

import re
import logging

logger = logging.getLogger(__name__)

class Screen:
    """
    Fixed 80x24 screen buffer with CP437-safe output.
    
    Attributes:
        width: Fixed screen width of 80 characters.
        height: Fixed screen height of 24 lines.
    """
    width = 80
    height = 24
    
    # ANSI color codes for our limited palette
    COLORS = {
        "green": "32",
        "amber": "33",
        "red": "31",
        "grey": "37",
    }
    
    # CP437 valid characters: ASCII + extended IBM PC characters
    # We'll use a simple approach: ASCII + box drawing characters
    CP437_BOX = {
        "┌": "+", "┐": "+", "└": "+", "┘": "+",
        "─": "-", "│": "|", "├": "+", "┤": "+",
        "┬": "+", "┴": "+", "┼": "+",
    }
    
    def __init__(self) -> None:
        """Initialize an empty screen buffer."""
        self._grid = [[[" ", "green"] for _ in range(self.width)] for _ in range(self.height)]
        self._cursor_row = 0
        self._cursor_col = 0
        
    def clear(self) -> None:
        """Clear the entire screen."""
        self._grid = [[[" ", "green"] for _ in range(self.width)] for _ in range(self.height)]
        self._cursor_row = 0
        self._cursor_col = 0
    
    def _sanitize(self, s: str) -> str:
        """
        Ensure string contains only CP437-safe characters.
        
        Replaces any character outside ASCII range 32-126 and basic box drawing
        with '?'.
        """
        result = []
        for ch in s:
            if 32 <= ord(ch) <= 126:
                result.append(ch)
            elif ch in self.CP437_BOX:
                # Use CP437 box drawing substitution
                result.append(self.CP437_BOX[ch])
            else:
                result.append("?")
        return "".join(result)
    
    def text(self, row: int, col: int, s: str, fg: str = "green") -> None:
        """
        Write text at specified position.
        
        Truncates to fit within row, never wraps to next line.
        """
        if not (0 <= row < self.height and 0 <= col < self.width):
            logger.warning(f"Position ({row},{col}) outside screen bounds")
            return
        
        s = self._sanitize(s)
        remaining = self.width - col
        if len(s) > remaining:
            s = s[:remaining]
        
        for i, ch in enumerate(s):
            if col + i < self.width:
                self._grid[row][col + i] = [ch, fg]
    
    def center(self, row: int, s: str, fg: str = "green") -> None:
        """
        Write centered text on the given row.
        """
        s = self._sanitize(s)
        col = max(0, (self.width - len(s)) // 2)
        self.text(row, col, s, fg)
    
    def hline(self, row: int, ch: str = "-") -> None:
        """
        Draw a horizontal line across the entire row.
        """
        ch = self._sanitize(ch)[0] if ch else "-"
        self.text(row, 0, ch * self.width, "green")
    
    def box(self, top: int, left: int, bottom: int, right: int, title: str = "") -> None:
        """
        Draw a box with optional title.
        
        Uses CP437-safe box drawing characters.
        """
        # Ensure bounds
        top = max(0, min(top, self.height - 1))
        left = max(0, min(left, self.width - 1))
        bottom = max(top, min(bottom, self.height - 1))
        right = max(left, min(right, self.width - 1))
        
        # Corners
        self.text(top, left, "+", "green")
        self.text(top, right, "+", "green")
        self.text(bottom, left, "+", "green")
        self.text(bottom, right, "+", "green")
        
        # Horizontal lines
        for col in range(left + 1, right):
            self.text(top, col, "-", "green")
            self.text(bottom, col, "-", "green")
        
        # Vertical lines
        for row in range(top + 1, bottom):
            self.text(row, left, "|", "green")
            self.text(row, right, "|", "green")
        
        # Title
        if title:
            title = self._sanitize(title)
            title_len = min(len(title), right - left - 1)
            title_pos = left + 1
            self.text(top, title_pos, f" {title[:title_len]} ", "green")
    
    def set_cursor(self, row: int, col: int) -> None:
        """
        Set cursor position for next render.
        """
        self._cursor_row = max(0, min(row, self.height - 1))
        self._cursor_col = max(0, min(col, self.width - 1))
    
    def render(self) -> str:
        """
        Render the screen as ANSI escape sequences.
        
        Returns:
            ANSI string ready to send to terminal.
        """
        lines = []
        current_fg = "green"
        
        for row in range(self.height):
            line = []
            cells = 0
            for col in range(self.width):
                ch, fg = self._grid[row][col]
                if fg != current_fg:
                    color_code = self.COLORS.get(fg, "32")
                    line.append(f"\x1b[{color_code}m")
                    current_fg = fg
                line.append(ch)
                cells += 1
            
            # Reset color at end of line, then pad to exactly 80 visible cells.
            # Escape sequences never count towards the 80 columns.
            if current_fg != "green":
                line.append("\x1b[0m")
                current_fg = "green"
            if cells < self.width:
                line.append(" " * (self.width - cells))
            
            lines.append("".join(line))
        
        # One CRLF per row: the terminal must never rely on auto-wrap.
        body = "\r\n".join(lines)
        
        # Position cursor
        cursor = f"\x1b[{self._cursor_row + 1};{self._cursor_col + 1}H"
        
        return "\x1b[2J\x1b[H" + body + cursor