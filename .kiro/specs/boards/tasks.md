# Tasks: boards

- [x] 1. Schema and seed
  - [x] 1.1 add `boards` and `posts` tables plus index to `app/db.py`
  - [x] 1.2 `app/boards.py`: `seed`, `all_boards`, `board`, `recent`, `post`, `add`
  - [x] 1.3 seed on first connection from `app/main.py`

- [x] 2. Wrapping helper
  - [x] 2.1 `app/terminal.py`: `wrap(text, width=72)`
  - [x] 2.2 tests for long words, existing newlines, empty input

- [x] 3. Screens
  - [x] 3.1 `board_list(boards)`
  - [x] 3.2 `board_view(board, posts)`
  - [x] 3.3 `post_view(post)` with wrapping
  - [x] 3.4 `compose_subject(board)` and `compose_body(board, subject, lines)`
  - [x] 3.5 `who(callers)` and `digest(lines)`

- [x] 4. Session
  - [x] 4.1 new states and `handle_key` routing
  - [x] 4.2 `B` opens the list, `1`-`4` open boards, `P` composes, `W` shows callers
  - [x] 4.3 compose: subject, body lines, `.` sends, Ctrl-C aborts
  - [x] 4.4 `Q` unwinds one level at a time

- [x] 5. Sysop digest
  - [x] 5.1 `app/sysop.py: digest(conn) -> list[str]`, last 24 hours
  - [x] 5.2 menu shows `S` for the digest, or the digest is reachable from the sysop board

- [x] 6. Verify
  - [x] 6.1 `uv run pytest -q` green
  - [x] 6.2 manual: post to `lobby`, restart, post is still there

