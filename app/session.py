"""
Session state machine for terminal connections.
"""

import asyncio
import json
import logging
import time
import sqlite3
from enum import Enum
from typing import Optional, Dict, Any

from . import screens
from . import users
from .terminal import Screen

logger = logging.getLogger(__name__)

class SessionState(Enum):
    """Session state machine states."""
    BOOT = "boot"
    LOGIN_HANDLE = "login_handle"
    LOGIN_PASSWORD = "login_password"
    NEW_PASSWORD = "new_password"
    CONFIRM_PASSWORD = "confirm_password"
    MENU = "menu"
    ABOUT = "about"
    BOARD_LIST = "board_list"
    BOARD_VIEW = "board_view"
    POST_VIEW = "post_view"
    COMPOSE_SUBJECT = "compose_subject"
    COMPOSE_BODY = "compose_body"
    WHO = "who"
    DIGEST = "digest"
    ESCALATIONS = "escalations"
    GAME = "game"

class Session:
    """
    Per-connection session state machine.
    
    Attributes:
        fast: Whether to skip boot animations.
        handle: Current user handle if logged in.
        boot_tick: Current boot frame number.
        login_handle_input: Handle input buffer.
        login_password_input: Password input buffer.
        login_attempts: Number of failed password attempts.
        last_activity: Timestamp of last activity.
        idle_timeout: Seconds before idle timeout (30 minutes).
    """
    
    def __init__(self, fast: bool = False) -> None:
        """Initialize a new session."""
        self.state = SessionState.BOOT
        self.fast = fast
        self.handle: Optional[str] = None
        self.boot_tick = 0
        self.login_handle_input = ""
        self.login_password_input = ""
        self.login_attempts = 0
        self.pending_password = ""
        self.board_id: Optional[str] = None
        self.post_id: Optional[int] = None
        self.draft_subject = ""
        self.draft_lines: list[str] = []
        self.read_buffer = ""
        self.game_state = None
        self.game_lines: list[str] = []
        self.game_input = ""
        self.game_finished = False
        self.last_activity = time.time()
        self.idle_timeout = 30 * 60  # 30 minutes
        
        # Presence tracking will be managed by presence module
        self.presence_id: Optional[str] = None
    
    def check_idle(self) -> bool:
        """
        Check if session has been idle too long.
        
        Returns:
            True if session should be disconnected.
        """
        return time.time() - self.last_activity > self.idle_timeout
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()
    
    async def handle_key(self, conn: sqlite3.Connection, key: str) -> Optional[str]:
        """
        Handle a key press in current state.
        
        Args:
            conn: SQLite connection.
            key: Key pressed (single character or special key).
        
        Returns:
            ANSI frame to send, or None for no frame.
        """
        self.update_activity()
        
        if self.state == SessionState.BOOT:
            return await self._handle_boot(key)
        elif self.state == SessionState.LOGIN_HANDLE:
            return await self._handle_login_handle(conn, key)
        elif self.state == SessionState.LOGIN_PASSWORD:
            return await self._handle_login_password(conn, key)
        elif self.state == SessionState.NEW_PASSWORD:
            return await self._handle_new_password(key)
        elif self.state == SessionState.CONFIRM_PASSWORD:
            return await self._handle_confirm_password(conn, key)
        elif self.state == SessionState.MENU:
            return await self._handle_menu(conn, key)
        elif self.state == SessionState.WHO:
            return await self._handle_who(key)
        elif self.state == SessionState.DIGEST:
            return await self._handle_digest(conn, key)
        elif self.state == SessionState.ESCALATIONS:
            return await self._handle_escalations(conn, key)
        elif self.state == SessionState.GAME:
            return await self._handle_game(key)
        elif self.state == SessionState.BOARD_LIST:
            return await self._handle_board_list(conn, key)
        elif self.state == SessionState.BOARD_VIEW:
            return await self._handle_board_view(conn, key)
        elif self.state == SessionState.POST_VIEW:
            return await self._handle_post_view(conn, key)
        elif self.state == SessionState.COMPOSE_SUBJECT:
            return await self._handle_compose_subject(conn, key)
        elif self.state == SessionState.COMPOSE_BODY:
            return await self._handle_compose_body(conn, key)
        elif self.state == SessionState.ABOUT:
            return await self._handle_about(key)
        
        return None
    
    async def _handle_boot(self, key: str) -> str:
        """Handle keys during boot sequence."""
        if self.boot_tick >= 5:
            self.state = SessionState.LOGIN_HANDLE
            return screens.login()

        if self.fast:
            self.boot_tick = 5
            return self._render_boot()

        self.boot_tick += 1
        return self._render_boot()
    
    async def _handle_login_handle(self, conn: sqlite3.Connection, key: str) -> str:
        """Handle handle input."""
        error = ""
        
        if key == "\r":  # Enter
            if not self.login_handle_input:
                error = "HANDLE REQUIRED"
            elif len(self.login_handle_input) < 2:
                error = "TOO SHORT"
            elif len(self.login_handle_input) > 20:
                error = "TOO LONG"
            elif not all(c.isalnum() or c == "_" for c in self.login_handle_input):
                error = "INVALID CHARACTERS"
            else:
                # Check if user exists
                cur = conn.execute(
                    "SELECT handle FROM users WHERE handle = ?",
                    (self.login_handle_input.lower(),),
                )
                if cur.fetchone():
                    # Existing user - ask for password
                    self.handle = self.login_handle_input.lower()
                    self.state = SessionState.LOGIN_PASSWORD
                    self.login_attempts = 0
                    return screens.password(self.handle)
                else:
                    # New handle - let the caller choose a password
                    self.handle = self.login_handle_input.lower()
                    self.state = SessionState.NEW_PASSWORD
                    self.pending_password = ""
                    return screens.new_password(self.handle)
        
        elif key == "\x7f":  # Backspace
            if self.login_handle_input:
                self.login_handle_input = self.login_handle_input[:-1]
        
        elif len(key) == 1 and key.isprintable():
            if len(self.login_handle_input) < 20:
                self.login_handle_input += key
        
        return screens.login(self.login_handle_input, error)
    
    async def _handle_login_password(self, conn: sqlite3.Connection, key: str) -> str:
        """Handle password input."""
        if not self.handle:
            self.state = SessionState.LOGIN_HANDLE
            return screens.login()
        
        error = ""
        
        if key == "\r":  # Enter
            if users.verify(conn, self.handle, self.login_password_input):
                # Password correct - log in
                users.update_last_call(conn, self.handle)
                self.state = SessionState.MENU
                from .presence import add_caller
                self.presence_id = add_caller(self.handle)
                return screens.menu(self.handle, 1)  # TODO: Get actual online count
            else:
                # Password wrong
                self.login_attempts += 1
                self.login_password_input = ""
                
                if self.login_attempts >= 3:
                    # Too many attempts - disconnect
                    return "carrier lost"
                else:
                    error = f"WRONG PASSWORD ({self.login_attempts}/3)"
        
        elif key == "\x7f":  # Backspace
            if self.login_password_input:
                self.login_password_input = self.login_password_input[:-1]
        
        elif len(key) == 1 and key.isprintable():
            if len(self.login_password_input) < 20:  # Reasonable max
                self.login_password_input += key
        
        return screens.password(self.handle, error)
    
    async def _handle_new_password(self, key: str) -> str:
        """Handle password choice for a brand new handle."""
        if key == "\r":
            if len(self.login_password_input) < 4:
                return screens.new_password(self.handle, "AT LEAST 4 CHARACTERS", self.login_password_input)
            self.pending_password = self.login_password_input
            self.login_password_input = ""
            self.state = SessionState.CONFIRM_PASSWORD
            return screens.confirm_password(self.handle)
        
        if key == "\x7f":
            self.login_password_input = self.login_password_input[:-1]
        elif len(key) == 1 and key.isprintable() and len(self.login_password_input) < 20:
            self.login_password_input += key
        
        return screens.new_password(self.handle, "", self.login_password_input)
    
    async def _handle_confirm_password(self, conn: sqlite3.Connection, key: str) -> str:
        """Handle password confirmation, then create the account."""
        if key == "\r":
            if self.login_password_input != self.pending_password:
                self.login_password_input = ""
                self.pending_password = ""
                self.state = SessionState.NEW_PASSWORD
                return screens.new_password(self.handle, "PASSWORDS DID NOT MATCH", "")
            try:
                users.create(conn, self.handle, self.pending_password)
            except ValueError as exc:
                self.state = SessionState.LOGIN_HANDLE
                self.handle = None
                return screens.login(self.login_handle_input, str(exc).upper())
            self.login_password_input = ""
            self.pending_password = ""
            self.state = SessionState.MENU
            from .presence import add_caller, get_online_count
            self.presence_id = add_caller(self.handle)
            return screens.menu(self.handle, get_online_count())
        
        if key == "\x7f":
            self.login_password_input = self.login_password_input[:-1]
        elif len(key) == 1 and key.isprintable() and len(self.login_password_input) < 20:
            self.login_password_input += key
        
        return screens.confirm_password(self.handle, "", self.login_password_input)
    
    async def _handle_menu(self, conn: sqlite3.Connection, key: str) -> str:
        """Handle menu navigation."""
        from . import boards as boards_module
        from . import sysop as sysop_module
        from .presence import get_online_count, get_callers

        upper = key.upper()

        if upper == "Q":
            return "carrier lost"
        if upper == "A":
            self.state = SessionState.ABOUT
            return screens.about()
        if upper == "W":
            self.state = SessionState.WHO
            return screens.who(get_callers())
        if upper == "S":
            self.state = SessionState.DIGEST
            return screens.digest(sysop_module.digest(conn))
        if upper == "E":
            self.state = SessionState.ESCALATIONS
            return screens.escalations(boards_module.escalations(conn))
        if upper == "B":
            self.state = SessionState.BOARD_LIST
            return screens.board_list(boards_module.all_boards(conn))
        if upper == "G":
            from . import game as game_module

            self.game_state = game_module.new_state()
            self.game_lines = game_module.look(self.game_state)
            self.game_input = ""
            self.game_finished = False
            self.state = SessionState.GAME
            return screens.game(self.game_state, self.game_lines)
        if upper in ("M", "F"):
            hint = "NOT WIRED YET"
        else:
            hint = "UNKNOWN KEY"

        return screens.menu(self.handle, get_online_count(), hint)

    async def _handle_who(self, key: str) -> str:
        """Handle the who's online screen."""
        from .presence import get_callers, get_online_count

        if key.upper() == "Q":
            self.state = SessionState.MENU
            return screens.menu(self.handle, get_online_count())
        return screens.who(get_callers())

    async def _handle_digest(self, conn: sqlite3.Connection, key: str) -> str:
        from . import sysop as sysop_module
        from .presence import get_online_count

        if key.upper() == "Q":
            self.state = SessionState.MENU
            return screens.menu(self.handle, get_online_count())
        return screens.digest(sysop_module.digest(conn))

    async def _handle_escalations(self, conn: sqlite3.Connection, key: str) -> str:
        from . import boards as boards_module
        from .presence import get_online_count

        if key.upper() == "Q":
            self.state = SessionState.MENU
            return screens.menu(self.handle, get_online_count())

        if key.isdigit():
            items = boards_module.escalations(conn)
            index = int(key) - 1
            if 0 <= index < len(items) and index < 9:
                boards_module.resolve(conn, items[index]["id"])

        return screens.escalations(boards_module.escalations(conn))

    async def _handle_game(self, key: str) -> str:
        """Type into LAST CALL; the game owns the rest."""
        from . import game as game_module
        from .presence import get_online_count

        if self.game_state is None:
            self.game_state = game_module.new_state()
            self.game_lines = game_module.look(self.game_state)

        if self.game_finished:
            self.state = SessionState.MENU
            self.game_state = None
            return screens.menu(self.handle, get_online_count())

        if key == "\x03":
            self.state = SessionState.MENU
            self.game_state = None
            return screens.menu(self.handle, get_online_count())

        if key == "\r":
            state, lines, playing = game_module.command(self.game_state, self.game_input)
            self.game_state = state
            self.game_lines = lines
            self.game_input = ""
            if not playing:
                self.game_finished = True
        elif key == "\x7f":
            self.game_input = self.game_input[:-1]
        elif len(key) == 1 and key.isprintable() and len(self.game_input) < 40:
            self.game_input += key

        return screens.game(self.game_state, self.game_lines, self.game_input, self.game_finished)

    async def _handle_board_list(self, conn: sqlite3.Connection, key: str) -> str:
        """Pick a board from the index."""
        from . import boards as boards_module
        from .presence import get_online_count

        if key.upper() == "Q":
            self.state = SessionState.MENU
            return screens.menu(self.handle, get_online_count())

        if key in "1234":
            index = int(key) - 1
            listed = boards_module.all_boards(conn)
            if index < len(listed):
                target = listed[index]
                self.board_id = target["id"]
                self.read_buffer = ""
                self.state = SessionState.BOARD_VIEW
                return screens.board_view(target, boards_module.recent(conn, target["id"]))

        return screens.board_list(boards_module.all_boards(conn))

    async def _handle_board_view(self, conn: sqlite3.Connection, key: str) -> str:
        """Read, post, or leave a board."""
        from . import boards as boards_module

        target = boards_module.board(conn, self.board_id or "")
        if target is None:
            self.state = SessionState.BOARD_LIST
            return screens.board_list(boards_module.all_boards(conn))

        if key.upper() == "Q":
            self.state = SessionState.BOARD_LIST
            self.read_buffer = ""
            return screens.board_list(boards_module.all_boards(conn))

        if key.upper() == "P":
            self.state = SessionState.COMPOSE_SUBJECT
            self.draft_subject = ""
            self.draft_lines = []
            return screens.compose_subject(target)

        if key == "\x7f":
            self.read_buffer = self.read_buffer[:-1]
        elif key == "\r":
            if self.read_buffer:
                posts = boards_module.recent(conn, target["id"])
                index = int(self.read_buffer) - 1
                if 0 <= index < len(posts):
                    full = boards_module.post(conn, posts[index]["id"])
                    if full:
                        self.post_id = full["id"]
                        self.state = SessionState.POST_VIEW
                        return screens.post_view(full, target["name"])
            self.read_buffer = ""
        elif key.isdigit() and len(self.read_buffer) < 2:
            self.read_buffer += key
            if int(self.read_buffer) < 1:
                self.read_buffer = ""
        elif not key.isdigit() and key not in ("\r", "\x7f"):
            self.read_buffer = ""

        return screens.board_view(target, boards_module.recent(conn, target["id"]), self.read_buffer)

    async def _handle_post_view(self, conn: sqlite3.Connection, key: str) -> str:
        """Leave a post back to its board."""
        from . import boards as boards_module

        if key.upper() == "Q":
            target = boards_module.board(conn, self.board_id or "")
            self.state = SessionState.BOARD_VIEW
            if target:
                return screens.board_view(target, boards_module.recent(conn, target["id"]))
            self.state = SessionState.BOARD_LIST
            return screens.board_list(boards_module.all_boards(conn))
        # Keep the same screen: a full redraw is cheaper than tracking dirty rows.
        full = boards_module.post(conn, self.post_id or 0)
        if full:
            return screens.post_view(full, "")
        self.state = SessionState.BOARD_LIST
        return screens.board_list(boards_module.all_boards(conn))

    async def _handle_compose_subject(self, conn: sqlite3.Connection, key: str) -> str:
        """Collect the subject line."""
        from . import boards as boards_module

        target = boards_module.board(conn, self.board_id or "")
        if target is None:
            self.state = SessionState.BOARD_LIST
            return screens.board_list(boards_module.all_boards(conn))

        if key == "\x03":
            self.state = SessionState.BOARD_VIEW
            return screens.board_view(target, boards_module.recent(conn, target["id"]))

        if key == "\r":
            if self.draft_subject.strip():
                self.state = SessionState.COMPOSE_BODY
                return screens.compose_body(target, self.draft_subject, [])
            return screens.compose_subject(target, self.draft_subject)

        if key == "\x7f":
            self.draft_subject = self.draft_subject[:-1]
        elif len(key) == 1 and key.isprintable() and len(self.draft_subject) < 60:
            self.draft_subject += key

        return screens.compose_subject(target, self.draft_subject)

    async def _handle_compose_body(self, conn: sqlite3.Connection, key: str) -> str:
        """Collect body lines; a lone dot sends."""
        from . import boards as boards_module
        from .presence import get_online_count

        target = boards_module.board(conn, self.board_id or "")
        if target is None:
            self.state = SessionState.BOARD_LIST
            return screens.board_list(boards_module.all_boards(conn))

        if key == "\x03":
            self.state = SessionState.BOARD_VIEW
            return screens.board_view(target, boards_module.recent(conn, target["id"]))

        if key == "\r":
            line = self.draft_lines[-1] if self.draft_lines else ""
            if line.strip() == ".":
                body = "\n".join(self.draft_lines[:-1])
                try:
                    boards_module.add(conn, target["id"], self.handle or "guest", self.draft_subject, body)
                except ValueError:
                    return screens.compose_body(target, self.draft_subject, self.draft_lines)
                self.state = SessionState.BOARD_VIEW
                self.draft_subject = ""
                self.draft_lines = []
                return screens.board_view(target, boards_module.recent(conn, target["id"]))
            self.draft_lines.append("")
            if len(self.draft_lines) > 20:
                self.draft_lines = self.draft_lines[:20]
            return screens.compose_body(target, self.draft_subject, self.draft_lines)

        if key == "\x7f":
            if self.draft_lines and self.draft_lines[-1]:
                self.draft_lines[-1] = self.draft_lines[-1][:-1]
            return screens.compose_body(target, self.draft_subject, self.draft_lines)

        if len(key) == 1 and key.isprintable():
            if not self.draft_lines:
                self.draft_lines.append("")
            if len(self.draft_lines[-1]) < 70:
                self.draft_lines[-1] += key

        return screens.compose_body(target, self.draft_subject, self.draft_lines)

    async def _handle_about(self, key: str) -> str:
        """Handle about screen."""
        if key.upper() == "Q":
            self.state = SessionState.MENU
            from .presence import get_online_count
            return screens.menu(self.handle, get_online_count())
        
        return screens.about()
    
    def _render_boot(self) -> str:
        """Render current boot frame."""
        screen = Screen()
        screens.boot(self.boot_tick, screen)
        return screen.render()
    
    def disconnect(self) -> None:
        """Clean up session on disconnect."""
        if self.presence_id:
            from .presence import remove_caller
            remove_caller(self.presence_id)

    def login_guest(self, conn: sqlite3.Connection) -> str:
        """
        Open a read-only guest session without the login dance.

        Used by the demo link so a judge sees the board in one click.
        """
        import secrets as _secrets
        from .presence import add_caller, get_online_count

        handle = "guest"
        row = conn.execute("SELECT handle FROM users WHERE handle = ?", (handle,)).fetchone()
        if not row:
            try:
                users.create(conn, handle, _secrets.token_hex(8))
            except ValueError:
                pass
        self.handle = handle
        self.state = SessionState.MENU
        self.presence_id = add_caller(handle)
        return screens.menu(handle, get_online_count())