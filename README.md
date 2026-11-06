# PHOSPHOR

> A dead network, reconnected. An ANSI bulletin board from the other side, run by an AI sysop.

PHOSPHOR is a BBS — the pre-web bulletin board system — rebuilt as a live service in 2026.
You dial in from the browser (or plain `telnet`), land on an 80x24 ANSI screen, and a
machine sysop answers. Boards, mail, a file area, a door game, and a nightly digest that
the sysop writes itself.

Built for [Kiroween 2026](https://kiroween.devpost.com/) — category: **Resurrection**.

## Why it exists

BBSes were the first social networks: one phone line, one screen, a sysop who kept the
place alive. They died because the web was easier — not because the format was worse.
PHOSPHOR brings the format back with the one thing a 1993 sysop never had: an agent that
can actually read every post, moderate the board, keep the door game running, and write
the digest at 3am.

## Status

| Layer | State |
|---|---|
| ANSI terminal core (80x24, CP437) | done |
| Login, scrypt passwords, presence | done |
| CRT browser client | done |
| Boards + posting | next |
| Sysop agent | planned |
| Door game (`LAST CALL`) | planned |
| Telnet bridge | planned |
| Deployment | planned |

## Run

```bash
uv venv
uv pip install -r requirements.txt
uv run uvicorn app.main:app --reload --port 8010
```

Open http://127.0.0.1:8010 and dial in.

## Built with Kiro

The `.kiro/` directory is the project's memory, not decoration:

- `.kiro/steering/` — product, tech, and style rules the agent reads on every task
- `.kiro/specs/` — requirements → design → tasks for each subsystem
- `.kiro/hooks/` — the checks that run before anything lands

Every file in `app/` was written through Kiro, against those specs.

## License

MIT — see `LICENSE`.
