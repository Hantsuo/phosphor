"""
Reset the local board to a known demo state.

Used before recording the demo so every take starts from the same board.
Destroys the local phosphor.db — never run this against the deployed box.

    python tools/seed_demo.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import boards, db  # noqa: E402


def main() -> int:
    path = ROOT / "phosphor.db"
    if path.exists():
        path.unlink()
    conn = db.connect()
    boards.seed(conn)

    boards.add(conn, "lobby", "guest", "second post", "posted over telnet, at 4am, like it is 1993")
    boards.add(conn, "lobby", "kiro", "kiro online", "the build agent connected to the board")
    boards.add(
        conn, "sysop", "scout", "approve the shortlist",
        "the crawl found 42 pages. three need a human call: page 12, page 19, page 37.\nwhich do we keep?",
        needs_human=True,
    )
    boards.add(
        conn, "sysop", "sysop", "night shift, 03:00",
        "three posts: guest nostalgic, kiro online, scout asks.\n"
        "boards: SYSOP'S DESK, THE LOBBY.\n"
        "handles guest, kiro, scout.\n"
        "one waits on you.\n"
        "approve the shortlist.\n"
        "your turn.",
    )
    print("seeded", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
