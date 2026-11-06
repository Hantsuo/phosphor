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
        (8, 25, "M - MAIL", "green"),
        (9, 25, "F - FILE AREA", "green"),
        (10, 25, "G - DOOR GAME", "green"),
        (11, 25, "A - ABOUT PHOSPHOR", "green"),
        (12, 25, "W - WHO'S ONLINE", "green"),
        (14, 25, "Q - QUIT", "amber"),
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