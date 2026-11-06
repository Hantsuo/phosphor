# Requirements: terminal core

## Introduction

The terminal core is the part that makes PHOSPHOR feel like a BBS instead of a web app:
a fixed 80x24 screen, a byte stream, a handshake, and a menu tree. Everything else
(boards, mail, door game) renders into this layer.

## Requirements

### R1 — Session handshake

**User story:** As a caller, I want the modem handshake and the ANSI art, so that arriving
feels like dialling in rather than loading a page.

**Acceptance criteria**

1. WHEN a WebSocket session opens THEN the server SHALL send a boot frame within 200 ms.
2. The boot frame SHALL contain the system name, the node id, and a carrier line.
3. WHEN the carrier sequence completes THEN the server SHALL show the login prompt.
4. While booting, keystrokes SHALL be ignored except for a skip key.

### R2 — Fixed screen

**User story:** As a caller, I want the screen to stay 80x24, so that art and menus line up
exactly as the sysop drew them.

**Acceptance criteria**

1. Every rendered line SHALL be at most 80 characters.
2. Every rendered screen SHALL contain exactly 24 lines.
3. The renderer SHALL NOT emit characters outside CP437.
4. The final escape sequence of a frame SHALL position the cursor explicitly.

### R3 — Navigation

**User story:** As a caller, I want to move through menus with single keys, so that the
board feels like a terminal, not a form.

**Acceptance criteria**

1. WHEN a caller presses a menu key THEN the server SHALL navigate to that screen and
   render it as a whole frame.
2. WHEN a caller presses an unknown key THEN the server SHALL render the current screen and
   show a one-line hint.
3. WHEN a caller presses `Q` on any board screen THEN the server SHALL return to the main menu.
4. WHEN a caller disconnects THEN all per-session state SHALL be dropped.

### R4 — Login

**User story:** As a caller, I want a handle and a password, so that my posts have an author.

**Acceptance criteria**

1. WHEN a handle is new THEN the server SHALL create the account and log the caller in.
2. WHEN a handle exists THEN the server SHALL ask for the password and reject a wrong one
   after three attempts by disconnecting.
3. Passwords SHALL be stored as `scrypt` hashes with a per-user salt.
4. A logged-in caller's handle SHALL appear in the status bar of every frame.

### R5 — Presence

**User story:** As a caller, I want to see who else is on, so that the board feels alive.

**Acceptance criteria**

1. WHEN a caller logs in or out THEN the presence list SHALL update for all sessions.
2. The main menu SHALL show the number of callers online.
3. An idle session SHALL be dropped after 30 minutes with a "carrier lost" frame.

## Out of scope for this spec

Boards, mail, file area, door game, and the sysop agent have their own specs.
