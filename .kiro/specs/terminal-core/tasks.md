# Tasks: terminal core

- [ ] 1. Project skeleton
  - [ ] 1.1 `requirements.txt` with fastapi, uvicorn[standard], pytest, httpx
  - [ ] 1.2 `app/__init__.py`, `app/db.py` with schema bootstrap and a `connect()` helper
  - [ ] 1.3 `.gitignore` for `.venv/`, `__pycache__/`, `*.db`

- [ ] 2. Screen buffer (`app/terminal.py`)
  - [ ] 2.1 `Screen` with `text`, `center`, `hline`, `box`
  - [ ] 2.2 CP437 sanitiser: replace anything outside CP437 with `?`
  - [ ] 2.3 `render()` emits clear + 24 rows of exactly 80 columns + cursor restore
  - [ ] 2.4 tests for width, height, sanitiser, cursor

- [ ] 3. Users (`app/users.py`)
  - [ ] 3.1 `create(handle) -> (user, password)` generating a 10-char password on first call
  - [ ] 3.2 `verify(handle, password)` with `hashlib.scrypt` and `hmac.compare_digest`
  - [ ] 3.3 tests for create, verify, wrong password

- [ ] 4. Screens (`app/screens.py`)
  - [ ] 4.1 `boot(tick, screen)` — six handshake frames
  - [ ] 4.2 `art(screen)` — PHOSPHOR ANSI title block, CP437 only
  - [ ] 4.3 `login(handle, error)` and `password(handle, error)`
  - [ ] 4.4 `menu(handle, online, hint)` with key legend
  - [ ] 4.5 `about(screen)` telling the Resurrection story in eight lines

- [ ] 5. Session (`app/session.py`)
  - [ ] 5.1 state machine per design; `handle_key`, `handle_text`
  - [ ] 5.2 idle timeout at 30 minutes, `carrier lost` frame
  - [ ] 5.3 presence join/leave in `finally`

- [ ] 6. Server (`app/main.py`)
  - [ ] 6.1 `/healthz` returning `{"ok": true, "callers": n}`
  - [ ] 6.2 `/ws` accepting JSON keys, sending frames
  - [ ] 6.3 static mount for `static/`

- [ ] 7. Client (`static/`)
  - [ ] 7.1 `index.html` with CRT shell, vendored xterm.js
  - [ ] 7.2 `app.js` connecting, reconnecting, sending keys
  - [ ] 7.3 `phosphor.css`: scanlines, vignette, green glow, no external fonts

- [ ] 8. Verify
  - [ ] 8.1 `pytest -q` green
  - [ ] 8.2 manual: connect, log in, reach menu, `Q` quits cleanly
