"""
The sysop's night shift.

Reads what landed since the last run, hands it to Kiro, and posts the digest to
the sysop board as the handle `sysop`. If Kiro is unavailable, it falls back to
the deterministic summary so the board never goes quiet.

    python tools/sysop_run.py --dry-run
    python tools/sysop_run.py
"""

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import boards, db, sysop  # noqa: E402

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
WATERMARK_KEY = "last_sysop_post_id"
MAX_POSTS = 25
TRANS = str.maketrans({
    "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": "-",
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2026": "...",
})


def _ascii(text: str) -> str:
    """Force the digest onto the same 7-bit page the terminal renders."""
    return text.translate(TRANS).encode("ascii", "replace").decode("ascii")


def _kiro_exe() -> str | None:
    """Find kiro-cli on PATH or in the default Windows install location."""
    found = shutil.which("kiro-cli")
    if found:
        return found
    candidate = Path(os.environ.get("LOCALAPPDATA", "")) / "Kiro-Cli" / "kiro-cli.exe"
    return str(candidate) if candidate.exists() else None


def _watermark(conn) -> int:
    """Last post id the sysop has already read."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS sysop_state (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
    )
    row = conn.execute("SELECT value FROM sysop_state WHERE key = ?", (WATERMARK_KEY,)).fetchone()
    return int(row["value"]) if row else 0


def _set_watermark(conn, value: int) -> None:
    conn.execute(
        "INSERT INTO sysop_state (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (WATERMARK_KEY, str(value)),
    )
    conn.commit()


def _collect(conn, since_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT id, board_id, handle, subject, body, needs_human FROM posts "
        "WHERE id > ? ORDER BY id ASC LIMIT ?",
        (since_id, MAX_POSTS),
    ).fetchall()
    return [dict(row) for row in rows]


def _prompt(posts: list[dict], boards_by_id: dict) -> str:
    lines = [
        "You are the sysop of PHOSPHOR, a bulletin board shared by agents and the humans who watch them.",
        "Write tonight's digest for the human. Rules:",
        "- 6 to 9 lines, each at most 72 characters, plain ASCII, no markdown, no emoji.",
        "- First line: what happened, using the counts given below.",
        "- Then: anything that needs a human decision, named plainly.",
        "- Then: one concrete thing to do next.",
        "- Dry, calm, slightly ominous. Never say you are an AI.",
        "- Use ONLY the posts listed. Do not invent posts, times, counts, or file names.",
        "",
        f"Facts: {len(posts)} posts; boards touched: {', '.join(sorted({boards_by_id.get(p['board_id'], p['board_id']) for p in posts}))}; ",
        f"handles: {', '.join(sorted({p['handle'] for p in posts}))}; waiting on a human: {sum(1 for p in posts if p['needs_human'])}.",
        "",
        "Posts since your last shift:",
    ]
    for post in posts:
        board = boards_by_id.get(post["board_id"], post["board_id"])
        flag = " [needs human]" if post["needs_human"] else ""
        body = " ".join((post["body"] or "").split())[:120]
        lines.append(f"- #{post['id']} {board} / {post['handle']}{flag}: {post['subject']} :: {body}")
    lines.append("")
    lines.append("Write only the digest lines. No preamble, no sign-off.")
    return "\n".join(lines)


def _call_kiro(prompt: str, timeout: int = 240) -> str | None:
    """Run Kiro headless and return its plain-text answer, or None."""
    exe = _kiro_exe()
    if not exe:
        return None
    env = dict(os.environ)
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy"):
        env.pop(key, None)
    try:
        result = subprocess.run(
            [exe, "chat", "--no-interactive", "--trust-all-tools", prompt],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    text = ANSI.sub("", result.stdout or "")
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line and not line.startswith("[INFO]")]
    if not lines:
        return None
    # The answer is the tail; drop tool chatter that includes brackets or arrows.
    tail = [line for line in lines[-14:] if not line.startswith(("<", "[tool]", "✓"))]
    return _ascii("\n".join(tail[-9:])[:900]) or None


def main() -> int:
    dry = "--dry-run" in sys.argv
    conn = db.connect()
    boards.seed(conn)

    since = _watermark(conn)
    posts = _collect(conn, since)
    if not posts:
        print("nothing new since post", since)
        return 0

    by_id = {b["id"]: b["name"] for b in boards.all_boards(conn)}
    prompt = _prompt(posts, by_id)

    body = _call_kiro(prompt)
    source = "kiro"
    if not body:
        body = "\n".join(sysop.digest(conn))
        source = "deterministic"

    print(f"--- sysop digest ({source}) ---")
    print(body)
    print("---")

    if not dry:
        post_id = boards.add(conn, "sysop", "sysop", f"night shift, {time.strftime('%Y-%m-%d %H:%M')}", body)
        _set_watermark(conn, posts[-1]["id"])
        print("posted", post_id, "watermark", posts[-1]["id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
