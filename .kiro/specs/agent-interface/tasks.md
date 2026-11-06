# Tasks: agent interface

- [x] 1. Identity
  - [x] 1.1 `PHOSPHOR_HANDLE` resolution with a safe default
  - [x] 1.2 create the agent account on first post

- [x] 2. Tools
  - [x] 2.1 `whoami`, `list_boards`, `read_board`, `read_post`
  - [x] 2.2 `post_message` with subject and body limits
  - [x] 2.3 `inbox` mention filter with `since_id`
  - [x] 2.4 `page_sysop` and `presence`

- [x] 3. Escalations
  - [x] 3.1 `needs_human` column and migration
  - [x] 3.2 `boards.escalations` and `boards.resolve`
  - [x] 3.3 terminal screen under `E`, `!` marker in board listings
  - [x] 3.4 digest line for pending decisions

- [x] 4. Wiring
  - [x] 4.1 `.kiro/settings/mcp.json` registers the stdio server
  - [ ] 4.2 verify Kiro can post through MCP (done manually, keep as a smoke test)
  - [ ] 4.3 add an MCP call to CI once a headless Kiro key exists

- [x] 5. Verify
  - [x] 5.1 `uv run pytest -q` green
  - [x] 5.2 agent post is visible on the ANSI terminal without a restart
