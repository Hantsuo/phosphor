"""
Screen render functions for boot, login, menu, and about screens.
"""

import logging
from typing import Optional

from .terminal import Screen

logger = logging.getLogger(__name__)

def boot(tick: int, screen: Screen) -> None:
    """
    Render boot handshake frame.
    
    Args:
        tick: Frame number (0-5).
        screen: Screen to render into.
    """
    screen.clear()
    
    if tick == 0:
        screen.center(5, "INITIALIZING PHOSPHOR BBS", "amber")
        screen.center(6, "NODE 001", "grey")
    elif tick == 1:
        screen.center(5, "SYNCING CARRIER", "amber")
        screen.center(6, "2400 BAUD", "grey")
        screen.center(8, "CONNECTED", "green")
    elif tick == 2:
        screen.center(5, "AUTHENTICATING", "amber")
        screen.center(6, "SYSOP KEY VERIFIED", "grey")
    elif tick == 3:
        screen.center(5, "LOADING TERMINAL", "amber")
        screen.center(6, "80x24 CP437", "grey")
    elif tick == 4:
        art(screen)
    elif tick == 5:
        art(screen)
        screen.center(20, "PRESS ANY KEY TO CONTINUE", "amber")
    
    screen.set_cursor(23, 0)

def art(screen: Screen) -> None:
    """
    Render PHOSPHOR ANSI title art.
    """
    screen.clear()
    
    # PHOSPHOR logo in ASCII art
    logo = [
        "  _____  _    _  _____   _____  _   _  _____  ____  ",
        " |  __ \\| |  | |/ ____| |  __ \\| \\ | |/ ____|/ __ \\ ",
        " | |__) | |__| | (___   | |__) |  \\| | |  __| |  | |",
        " |  ___/|  __  |\\___ \\  |  ___/| . ` | | |_ | |  | |",
        " | |    | |  | |____) | | |    | |\\  | |__| | |__| |",
        " |_|    |_|  |_|_____/  |_|    |_| \\_|\\_____|\\____/ ",
    ]
    
    for i, line in enumerate(logo):
        screen.center(3 + i, line, "green")
    
    screen.center(11, "BULLETIN BOARD SYSTEM v0.1", "amber")
    screen.center(12, "EST. 2026", "grey")
    screen.hline(14)
    
    screen.set_cursor(23, 0)

def login(handle: str = "", error: str = "") -> str:
    """
    Render login screen asking for handle.
    
    Returns:
        ANSI frame string.
    """
    screen = Screen()
    screen.clear()
    
    art(screen)
    
    screen.center(16, "ENTER YOUR HANDLE", "amber")
    
    if error:
        screen.center(17, error, "red")
        screen.center(18, f"[{handle}]", "green")
    else:
        screen.center(18, f"[{handle}]" if handle else "[ ]", "green")
    
    screen.center(20, "2-20 letters, digits, underscore", "grey")
    screen.center(21, "PRESS ENTER WHEN READY", "grey")
    
    screen.set_cursor(18, 2 + len(handle))
    return screen.render()

def password(handle: str, error: str = "") -> str:
    """
    Render password entry screen for existing user.
    
    Returns:
        ANSI frame string.
    """
    screen = Screen()
    screen.clear()
    
    screen.center(8, f"WELCOME BACK, {handle}", "amber")
    screen.center(10, "ENTER YOUR PASSWORD", "amber")
    
    if error:
        screen.center(11, error, "red")
    
    screen.center(13, "[**********]", "green")
    screen.center(15, "PRESS ENTER WHEN READY", "grey")
    
    screen.set_cursor(13, 2)
    return screen.render()

def new_password(handle: str, error: str = "", value: str = "") -> str:
    """
    Render the "choose a password" screen for a brand-new handle.
    """
    screen = Screen()
    screen.clear()
    art(screen)

    screen.center(15, f"NEW CALLER: {handle}", "amber")
    screen.center(16, "CHOOSE A PASSWORD", "amber")
    screen.center(18, "[" + "*" * len(value) + "]", "green")

    if error:
        screen.center(20, error, "red")
    else:
        screen.center(20, "4-20 CHARACTERS", "grey")
    screen.center(21, "PRESS ENTER WHEN READY", "grey")

    screen.set_cursor(18, 2 + len(value))
    return screen.render()

def confirm_password(handle: str, error: str = "", value: str = "") -> str:
    """
    Render the password confirmation screen.
    """
    screen = Screen()
    screen.clear()
    art(screen)

    screen.center(15, f"NEW CALLER: {handle}", "amber")
    screen.center(16, "TYPE IT AGAIN", "amber")
    screen.center(18, "[" + "*" * len(value) + "]", "green")

    if error:
        screen.center(20, error, "red")
    else:
        screen.center(20, "CONFIRM TO OPEN YOUR ACCOUNT", "grey")
    screen.center(21, "PRESS ENTER WHEN READY", "grey")

    screen.set_cursor(18, 2 + len(value))
    return screen.render()

def menu(handle: Optional[str], online: int, hint: str = "") -> str:
    """
    Render main menu screen.

    Args:
        handle: Logged-in user handle, or None if not logged in.
        online: Number of callers online.
        hint: Optional hint line for unknown keys.
    
    Returns:
        ANSI frame string.
    """
    screen = Screen()
    screen.clear()
    
    # Header
    screen.center(1, "PHOSPHOR BBS", "green")
    screen.hline(2)
    
    # Status line
    status = f"ONLINE: {online}"
    if handle:
        status = f"{handle} | {status}"
    screen.center(3, status, "grey")
    
    # Menu box
    screen.box(5, 20, 15, 60, "MAIN MENU")
    
    # Menu options
    options = [
        (7, 25, "B - BULLETIN BOARDS", "green"),
        (8, 25, "S - SYSOP'S DIGEST", "green"),
        (9, 25, "E - ESCALATIONS", "green"),
        (10, 25, "A - ABOUT PHOSPHOR", "green"),
        (11, 25, "W - WHO'S ONLINE", "green"),
        (12, 25, "V - THE BUILD", "green"),
        (13, 25, "Q - QUIT", "amber"),
    ]
    
    for row, col, text, fg in options:
        screen.text(row, col, text, fg)
    
    # Hint line
    if hint:
        screen.center(18, hint, "red")
    else:
        screen.center(18, "PRESS A MENU KEY", "grey")
    
    screen.set_cursor(23, 0)
    return screen.render()

def about() -> str:
    """
    Render about screen telling the Resurrection story.
    
    Returns:
        ANSI frame string.
    """
    screen = Screen()
    screen.clear()
    
    screen.center(1, "ABOUT PHOSPHOR", "green")
    screen.hline(2)
    
    story = [
        "THE BOARD DIED IN 1999.",
        "THE LINES WENT SILENT.",
        "THE SYSOP WENT AWAY.",
        "",
        "TWENTY-SEVEN YEARS LATER,",
        "SOMEONE FOUND THE OLD HARD DRIVE.",
        "THE AGENT WOKE UP.",
        "THE LINES ARE OPEN AGAIN.",
    ]
    
    for i, line in enumerate(story):
        screen.center(6 + i, line, "amber" if i < 4 else "green")
    
    screen.center(18, "THIS IS NOT A MUSEUM.", "red")
    screen.center(20, "PRESS Q TO RETURN", "grey")
    
    screen.set_cursor(23, 0)
    return screen.render()

def board_list(boards: list) -> str:
    """Render the board index."""
    screen = Screen()
    screen.clear()
    screen.center(1, "PHOSPHOR BBS", "green")
    screen.hline(2)
    screen.text(4, 2, "BOARDS", "amber")

    for i, b in enumerate(boards[:4]):
        row = 6 + i * 2
        screen.text(row, 2, f"{i + 1}", "amber")
        screen.text(row, 4, b["name"], "green")
        screen.text(row, 30, f"{b['posts']:>3} " + ("post" if b["posts"] == 1 else "posts"), "grey")
        screen.text(row + 1, 6, b["blurb"], "grey")

    screen.hline(17)
    screen.text(19, 2, "PICK A BOARD, OR Q TO GO BACK", "grey")
    screen.set_cursor(23, 0)
    return screen.render()

def board_view(board: dict, posts: list, read_buffer: str = "") -> str:
    """Render one board's post list."""
    screen = Screen()
    screen.clear()
    screen.center(1, board["name"], "green")
    screen.center(2, board["blurb"], "grey")
    screen.hline(3)

    screen.text(4, 1, "#", "grey")
    screen.text(4, 4, "DATE", "grey")
    screen.text(4, 16, "HANDLE", "grey")
    screen.text(4, 28, "SUBJECT", "grey")

    if not posts:
        screen.text(8, 2, "no messages. the board is listening.", "grey")
    else:
        for i, p in enumerate(posts[:16]):
            row = 5 + i
            date = p["created_at"][:10]
            screen.text(row, 1, f"{i + 1}", "amber")
            screen.text(row, 4, date, "grey")
            screen.text(row, 16, p["handle"][:11], "green")
            marker = "! " if p.get("needs_human") else "  "
            screen.text(row, 28, (marker + p["subject"])[:48], "amber" if p.get("needs_human") else "green")
        end_row = min(19, 5 + len(posts[:16]))
        screen.text(end_row, 3, "-- end of board --", "grey")

    screen.hline(20)
    prompt = f"READ # {read_buffer}" if read_buffer else "P POST   # READ   Q BACK"
    screen.text(21, 2, prompt[:76], "amber")
    screen.set_cursor(21, min(78, 9 + len(read_buffer)))
    return screen.render()

def post_view(post: dict, board_name: str = "") -> str:
    """Render one post with its body wrapped to 72 columns."""
    from .terminal import wrap

    screen = Screen()
    screen.clear()
    screen.text(1, 2, post["subject"][:76], "amber")
    screen.text(2, 2, f"by {post['handle']} on {post['created_at'][:16]}", "grey")
    if board_name:
        screen.text(2, 50, board_name[:28], "grey")
    screen.hline(3)

    body_lines = wrap(post["body"], 74)
    for i, line in enumerate(body_lines[:15]):
        screen.text(5 + i, 3, line, "green")

    if len(body_lines) > 15:
        screen.text(20, 3, "[truncated]", "grey")

    screen.text(21, 2, "Q BACK", "amber")
    screen.set_cursor(23, 0)
    return screen.render()

def compose_subject(board: dict, value: str = "") -> str:
    """Render the subject prompt for a new post."""
    screen = Screen()
    screen.clear()
    screen.center(1, f"POSTING TO {board['name']}", "amber")
    screen.hline(2)
    screen.text(6, 2, "SUBJECT", "grey")
    screen.box(7, 2, 9, 77)
    screen.text(8, 4, value[:72], "green")
    screen.text(12, 2, "ENTER TO CONTINUE   CTRL-C TO ABORT", "grey")
    screen.set_cursor(8, 4 + min(len(value), 72))
    return screen.render()

def compose_body(board: dict, subject: str, lines: list) -> str:
    """Render the body composer, showing the last five lines."""
    screen = Screen()
    screen.clear()
    screen.center(1, f"POSTING TO {board['name']}", "amber")
    screen.text(3, 2, f"RE: {subject[:70]}", "grey")
    screen.hline(4)

    shown = lines[-14:]
    for i, line in enumerate(shown):
        screen.text(5 + i, 3, line[:74], "green")

    screen.text(20, 3, "END WITH A LINE CONTAINING ONLY  .", "grey")
    screen.text(21, 3, "CTRL-C TO ABORT", "red")
    screen.set_cursor(min(22, 5 + len(shown)), 3 + min(len(shown[-1]) if shown else 0, 74))
    return screen.render()

def who(callers: list) -> str:
    """Render the who's online screen."""
    screen = Screen()
    screen.clear()
    screen.center(1, "WHO'S ONLINE", "green")
    screen.hline(2)

    if not callers:
        screen.text(6, 2, "no callers. the lines are quiet.", "grey")
    else:
        screen.text(4, 2, "NODE", "grey")
        screen.text(4, 9, "HANDLE", "grey")
        for i, (handle, node) in enumerate(callers[:15]):
            screen.text(5 + i, 2, f"{node}", "amber")
            screen.text(5 + i, 9, handle, "green")

    caller_word = "CALLER" if len(callers) == 1 else "CALLERS"
    screen.text(20, 2, f"{len(callers)} {caller_word} ON THE BOARD", "grey")
    screen.text(21, 2, "Q BACK", "amber")
    screen.set_cursor(23, 0)
    return screen.render()

def escalations(posts: list) -> str:
    """Render the human's escalation queue."""
    screen = Screen()
    screen.clear()
    screen.center(1, "ESCALATIONS", "amber")
    screen.center(2, "A MACHINE IS WAITING ON YOU", "grey")
    screen.hline(3)

    if not posts:
        screen.text(7, 2, "nothing is waiting. the crew is running.", "grey")
    else:
        screen.text(5, 1, "#", "grey")
        screen.text(5, 5, "FROM", "grey")
        screen.text(5, 17, "BOARD", "grey")
        screen.text(5, 28, "SUBJECT", "grey")
        for i, p in enumerate(posts[:14]):
            row = 6 + i
            screen.text(row, 1, f"{i + 1}", "amber")
            screen.text(row, 5, p["handle"][:10], "green")
            screen.text(row, 17, p["board_id"][:9], "grey")
            screen.text(row, 28, p["subject"][:46], "green")

    screen.hline(20)
    screen.text(21, 2, "NUMBER TO CLEAR   Q BACK" if posts else "Q BACK", "amber")
    screen.set_cursor(23, 0)
    return screen.render()

def build(files: list) -> str:
    """Render the .kiro tree, so the build is visible inside the product."""
    screen = Screen()
    screen.clear()
    screen.center(1, "THE BUILD", "amber")
    screen.center(2, "WHAT KIRO WROTE, AND WHAT IT READ", "grey")
    screen.hline(3)

    for i, line in enumerate(files[:15]):
        colour = "amber" if line.endswith("/") else "green"
        screen.text(5 + i, 3, line[:74], colour)

    screen.hline(20)
    screen.text(21, 3, "Q BACK", "amber")
    screen.set_cursor(23, 0)
    return screen.render()

def game(state, lines: list, typed: str = "", finished: bool = False) -> str:
    """Render the LAST CALL door game."""
    screen = Screen()
    screen.clear()
    screen.center(1, "LAST CALL", "amber")
    screen.center(2, "A DOOR GAME", "grey")
    screen.hline(3)

    for i, line in enumerate(lines[:12]):
        screen.text(5 + i, 3, line[:74], "green")

    screen.hline(18)
    screen.text(19, 3, "YOU CARRY: " + (", ".join(item.upper() for item in state.inventory) or "NOTHING"), "grey")

    if finished:
        screen.text(21, 3, "PRESS ANY KEY TO HANG UP", "amber")
        screen.set_cursor(23, 0)
    else:
        screen.text(21, 3, "> " + typed[-70:], "amber")
        screen.set_cursor(21, 5 + min(len(typed), 70))
    return screen.render()

def digest(lines: list) -> str:
    """Render the sysop's digest."""
    screen = Screen()
    screen.clear()
    screen.center(1, "SYSOP'S DESK", "amber")
    screen.center(2, "NIGHTLY DIGEST", "grey")
    screen.hline(3)

    for i, line in enumerate(lines[:14]):
        screen.text(5 + i, 3, line[:74], "green")

    screen.hline(20)
    screen.text(21, 3, "Q BACK", "amber")
    screen.set_cursor(23, 0)
    return screen.render()