# Tasks: terminal core

- [x] 1. Project skeleton
  - [x] 1.1 `requirements.txt` with fastapi, uvicorn[standard], pytest, httpx
  - [x] 1.2 `app/__init__.py`, `app/db.py` with schema bootstrap and a `connect()` helper
  - [x] 1.3 `.gitignore` for `.venv/`, `__pycache__/`, `*.db`

- [x] 2. Screen buffer (`app/terminal.py`)
  - [x] 2.1 `Screen` with `text`, `center`, `hline`, `box`
  - [x] 2.2 CP437 sanitiser: replace anything outside CP437 with `?`
  - [x] 2.3 `render()` emits clear + 24 rows of exactly 80 columns + cursor restore
  - [x] 2.4 tests for width, height, sanitiser, cursor

- [x] 3. Users (`app/users.py`)
  - [x] 3.1 `create(handle) -> (user, password)` generating a 10-char password on first call
  - [x] 3.2 `verify(handle, password)` with `hashlib.scrypt` and `hmac.compare_digest`
  - [x] 3.3 tests for create, verify, wrong password

- [x] 4. Screens (`app/screens.py`)
  - [x] 4.1 `boot(tick, screen)` 鈥?six handshake frames
  - [x] 4.2 `art(screen)` 鈥?PHOSPHOR ANSI title block, CP437 only
  - [x] 4.3 `login(handle, error)` and `password(handle, error)`
  - [x] 4.4 `menu(handle, online, hint)` with key legend
  - [x] 4.5 `about(screen)` telling the Resurrection story in eight lines

- [x] 5. Session (`app/session.py`)
  - [x] 5.1 state machine per design; `handle_key`, `handle_text`
  - [x] 5.2 idle timeout at 30 minutes, `carrier lost` frame
  - [x] 5.3 presence join/leave in `finally`

- [x] 6. Server (`app/main.py`)
  - [x] 6.1 `/healthz` returning `{"ok": true, "callers": n}`
  - [x] 6.2 `/ws` accepting JSON keys, sending frames
  - [x] 6.3 static mount for `static/`

- [x] 7. Client (`static/`)
  - [x] 7.1 `index.html` with CRT shell, vendored xterm.js
  - [x] 7.2 `app.js` connecting, reconnecting, sending keys
  - [x] 7.3 `phosphor.css`: scanlines, vignette, green glow, no external fonts

- [x] 8. Verify
  - [x] 8.1 `pytest -q` green
  - [x] 8.2 manual: connect, log in, reach menu, `Q` quits cleanly

