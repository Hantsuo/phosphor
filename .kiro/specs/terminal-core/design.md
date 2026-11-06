# Design: terminal core

## Overview

One WebSocket per caller. The server keeps a `Session` and renders whole frames into a
`Screen` buffer; the browser runs a dumb terminal emulator that writes the bytes it gets.

```
browser (xterm.js)  <-- ANSI bytes --  FastAPI /ws  -->  Session  -->  Screen
        |                                   |
        +-- keystrokes as JSON ------------> +--> login / menu state machine
                                            +--> SQLite users, in-memory presence
```

## Modules

| Module | Responsibility |
|---|---|
| `app/main.py` | FastAPI app, static mount, `/ws` endpoint, `/healthz` |
| `app/terminal.py` | `Screen` buffer, CP437 sanitiser, ANSI frame encoder |
| `app/session.py` | Per-connection state machine, input dispatch, idle timeout |
| `app/screens.py` | Boot, login, main menu, about — pure render functions |
| `app/users.py` | Handle creation, scrypt password hashing, verification |
| `app/presence.py` | In-memory set of logged-in callers, broadcast on change |
| `app/db.py` | SQLite connection factory and schema bootstrap |

## Screen buffer

```python
class Screen:
    width = 80
    height = 24
    def __init__(self) -> None: ...
    def clear(self) -> None: ...
    def text(self, row: int, col: int, s: str, fg: str = "green") -> None: ...
    def hline(self, row: int, ch: str = "-") -> None: ...
    def box(self, top: int, left: int, bottom: int, right: int, title: str = "") -> None: ...
    def center(self, row: int, s: str, fg: str = "green") -> None: ...
    def render(self) -> str: ...
```

`render()` emits:

1. `ESC[2J` (clear), `ESC[H`
2. 24 rows of 80 columns, colour changes inline with `ESC[32m` etc., reset at line end
3. `ESC[<row>;<col>H` to restore the cursor the session asked for

Missing cells render as spaces in the default green-on-black.

## Wire protocol

Server to client, one JSON object per WebSocket text frame:

```json
{"t": "frame", "d": "\u001b[2J\u001b[H..."}
{"t": "ping"}
```

Client to server:

```json
{"t": "key", "d": "a"}
```

`d` is one logical key: a printable character, `\r` for enter, or one of
`ESC`, `UP`, `DOWN`, `LEFT`, `RIGHT`, `BACKSPACE`.

## Session state machine

States: `BOOT -> LOGIN -> MENU -> (BOARD|MAIL|FILES|GAME|ABOUT) -> MENU`.

- `BOOT` plays the handshake as up to 6 frames, 120 ms apart, skipped when
  `?fast=1` is present on the WebSocket URL or `PHOSPHOR_FAST=1` is set.
- `LOGIN` collects a handle (2-20 chars, `[a-z0-9_]`), then either creates the user or
  asks for the password; three failures disconnect.
- `MENU` reacts to `B`, `M`, `F`, `G`, `A`, `W`, `Q` and always shows the presence count.

## Persistence

```sql
CREATE TABLE IF NOT EXISTS users (
  handle      TEXT PRIMARY KEY,
  pw_salt     BLOB NOT NULL,
  pw_hash     BLOB NOT NULL,
  created_at  TEXT NOT NULL,
  last_call   TEXT NOT NULL,
  calls       INTEGER NOT NULL DEFAULT 1
);
```

## Failure handling

- WebSocket disconnect at any point drops the session; presence is updated in a `finally`.
- SQLite errors are logged and surfaced as `carrier lost` rather than a 500 page.
- A frame that fails to encode is replaced by a minimal error screen so the client is never stuck.

## Testing

`tests/test_terminal.py` covers width, height, CP437 sanitising, and cursor placement.
`tests/test_users.py` covers create/verify/reject. Both run without a browser.
