# Design: boards

## Schema

Added to `db.SCHEMA`, all `CREATE TABLE IF NOT EXISTS`:

```sql
CREATE TABLE IF NOT EXISTS boards (
  id         TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  blurb      TEXT NOT NULL,
  position   INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS posts (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  board_id   TEXT NOT NULL REFERENCES boards(id),
  handle     TEXT NOT NULL,
  subject    TEXT NOT NULL,
  body       TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_posts_board ON posts(board_id, id DESC);
```

Seed four rows in `boards.seed(conn)`: `lobby` (THE LOBBY), `graveyard` (DEAD TECH
OBITUARIES), `sightings` (SIGHTINGS), `sysop` (SYSOP'S DESK). `INSERT OR IGNORE`.

## Modules

| Module | Responsibility |
|---|---|
| `app/boards.py` | seed, list, get, recent posts, add post, digest query |
| `app/screens.py` | add `board_list`, `board_view`, `post_view`, `compose_subject`, `compose_body`, `who`, `digest` |
| `app/session.py` | new states and input handlers |
| `app/sysop.py` | `digest(conn) -> list[str]`, deterministic |

## API

```python
def seed(conn) -> None
def all_boards(conn) -> list[dict]          # id, name, blurb, posts
def board(conn, board_id) -> dict | None
def recent(conn, board_id, limit=20) -> list[dict]   # id, handle, subject, created_at
def post(conn, post_id) -> dict | None      # id, handle, subject, body, created_at
def add(conn, board_id, handle, subject, body) -> int
def digest(conn) -> list[str]
```

`add` truncates subject to 60, body to 20 lines x 70 chars, strips trailing blank lines,
and rejects an empty subject with `ValueError`.

## Session states

```
MENU --B--> BOARD_LIST --1..4--> BOARD_VIEW --P--> COMPOSE_SUBJECT --> COMPOSE_BODY
             ^                        |                                    |
             +--------Q---------------+                                    |
                                      +-------------------.---------------+
MENU --W--> WHO --Q--> MENU
```

New state names: `BOARD_LIST`, `BOARD_VIEW`, `POST_VIEW`, `COMPOSE_SUBJECT`,
`COMPOSE_BODY`, `WHO`. The session keeps `board_id`, `post_id`, `draft_subject`,
`draft_lines: list[str]`.

## Screens

- `board_list(boards)`: header, four rows `1  LOBBY ......... 12 posts`, `Q  BACK`.
- `board_view(board, posts)`: header with board name and count; rows
  ` 3  2026-11-06  guest      first post`; footer `P POST   # READ   Q BACK`.
- `post_view(post)`: subject, author + date rule, body wrapped to 72 columns,
  footer `Q BACK`.
- `compose_subject(board)` / `compose_body(board, subject, lines)`: box with the
  prompt and a caret; body shows the lines typed so far, last five.
- `who(callers)`: handle, node number, and the total.
- `digest(lines)`: titled `SYSOP'S DESK`, the digest lines, `Q BACK`.

## Wrapping

`app/terminal.py` gains `wrap(text: str, width: int = 72) -> list[str]` that breaks on
spaces, keeps existing newlines as breaks, and never returns a line longer than width.

## Failure handling

- A missing board id from a stale menu SHALL fall back to the board list, not a 500.
- A post that fails to insert SHALL keep the caller in compose with a one-line error.
- Board screens SHALL render even with zero posts ("no messages. the board is listening.").

## Testing

`tests/test_boards.py`: seed idempotency, add/recent round trip, subject truncation,
empty-subject rejection, digest shape. `tests/test_terminal.py` gains wrap tests.
