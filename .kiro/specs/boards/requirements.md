# Requirements: boards

## Introduction

Boards are why anyone dialled a BBS. This spec adds the four boards, reading them,
posting to them, and the presence screen. The sysop digest lives in the same spec
because it reads the same data.

## Requirements

### R1 — Board list

**User story:** As a caller, I want to see the boards and how alive each one is.

**Acceptance criteria**

1. WHEN the caller presses `B` on the menu THEN the server SHALL show four boards with
   name, one-line description, and post count.
2. The board keys SHALL be `1`-`4`; `Q` SHALL return to the menu.
3. The list SHALL be ordered by the order the boards were seeded, not alphabetically.

### R2 — Reading a board

**User story:** As a caller, I want to read the last twenty posts without scrolling forever.

**Acceptance criteria**

1. WHEN a board is opened THEN the server SHALL show the twenty newest posts, newest last,
   each with author, date (`YYYY-MM-DD`), and subject.
2. WHEN a post is selected by its number THEN the server SHALL show the full body, wrapped
   at 72 columns, with the original line breaks preserved as breaks.
3. `Q` SHALL return to the board list; `P` SHALL start a post.

### R3 — Posting

**User story:** As a caller, I want to post without a mouse, the way a BBS worked.

**Acceptance criteria**

1. WHEN composing THEN the server SHALL ask for a subject (max 60 chars) and then body lines.
2. A body line containing only `.` SHALL send the post, trim trailing blank lines, and
   return to the board with the new post visible.
3. Ctrl-C (`\x03`) at any compose prompt SHALL abort and return to the board.
4. A post SHALL NOT be stored if the subject is empty.
5. Body SHALL be capped at 20 lines of 70 characters; extra input SHALL be ignored.

### R4 — Who is online

**User story:** As a caller, I want to see who else is holding the line.

**Acceptance criteria**

1. `W` SHALL show one line per logged-in caller, with handle and node number.
2. The screen SHALL show the total and a "no other callers" line when alone.

### R5 — Persistence and defaults

**User story:** As the operator, I want a fresh database to look alive on first boot.

**Acceptance criteria**

1. The four boards SHALL be seeded on first connection: `lobby`, `graveyard`,
   `sightings`, `sysop`.
2. Seeding SHALL be idempotent.
3. Posts SHALL survive a server restart.

### R6 — Sysop digest

**User story:** As a caller, I want the board to feel kept, even at 3am.

**Acceptance criteria**

1. The digest SHALL be computed from the last 24 hours of posts: count, most active board,
   and up to three handles that posted.
2. When there are no posts the digest SHALL say so in one line, without filler.
3. The digest SHALL be deterministic for the same data.
