# Tech steering

## Stack

- Python 3.13, FastAPI, uvicorn, `websockets` through FastAPI.
- Standard library `sqlite3` only. No ORM, no Alembic.
- Front-end is static HTML/CSS/JS plus a vendored `xterm.js`; no build step, no bundler.
- Tests: `pytest`, no network, no sleeps longer than 50 ms.

## Architecture rules

- The server owns the screen. Clients do not compose UI; they render the byte stream the
  server sends, exactly like a terminal emulator.
- One `Terminal` per session, 80x24, CP437-safe output. The session is a state machine of
  `Screen` objects; each screen renders a full frame on entry.
- All state that must survive a restart goes to SQLite. In-memory only for presence.
- No blocking I/O inside the event loop. SQLite calls stay short and synchronous.
- Any LLM call is behind `app/sysop.py` with a deterministic fallback, so the demo works
  with the network down.

## Commands

```bash
uv venv && uv pip install -r requirements.txt
uv run uvicorn app.main:app --reload --port 8010
uv run pytest -q
```

## Windows note

Local development runs on Windows; deployment runs on Linux in Docker. Path handling must
use `pathlib`, never string concatenation with `/`.
