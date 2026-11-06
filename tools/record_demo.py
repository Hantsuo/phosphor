"""
Record a PHOSPHOR session as a timed frame log, paced by the narration.

Reads demo/voice/timing.json so every beat stays on screen for as long as its
line takes, and writes demo/marks.json with the start time of each beat.

    python tools/record_demo.py --out demo/session.json
"""

import argparse
import asyncio
import json
import re
import time
from pathlib import Path

import websockets

URL = "ws://127.0.0.1:8010/ws"
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
PAD = 0.35


def plain(frame: str) -> str:
    return ANSI.sub("", frame).replace("\r", "")


class Recorder:
    def __init__(self, timing: dict) -> None:
        self.frames: list[dict] = []
        self.marks: dict[str, float] = {}
        self.timing = timing
        self.ws = None
        self.start = 0.0

    def add(self, frame: str) -> None:
        self.frames.append({"t": round(time.monotonic() - self.start, 3), "d": frame})

    async def _pump(self, settle: float) -> None:
        while True:
            try:
                msg = json.loads(await asyncio.wait_for(self.ws.recv(), settle))
            except asyncio.TimeoutError:
                return
            if msg.get("t") == "frame":
                self.add(msg["d"])

    async def key(self, key: str, settle: float = 0.2) -> None:
        await self.ws.send(json.dumps({"t": "key", "d": key}))
        await self._pump(settle)

    async def type(self, text: str, gap: float = 0.1) -> None:
        for ch in text:
            await self.key(ch, 0.03)
            await asyncio.sleep(gap)
        await asyncio.sleep(0.2)

    async def hold(self, beat: str) -> None:
        """Mark the beat and stay on it for the narration's length."""
        self.marks[beat] = round(time.monotonic() - self.start, 3)
        seconds = float(self.timing.get(beat, 6.0)) + PAD
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            await asyncio.sleep(0.25)
            if self.frames:
                self.add(self.frames[-1]["d"])

    async def wait_for(self, text: str, timeout: float = 20.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.frames and text in plain(self.frames[-1]["d"]):
                return
            try:
                msg = json.loads(await asyncio.wait_for(self.ws.recv(), 1.0))
            except asyncio.TimeoutError:
                continue
            if msg.get("t") == "frame":
                self.add(msg["d"])
        raise TimeoutError(text)


async def run(out: Path, timing: dict) -> None:
    rec = Recorder(timing)
    async with websockets.connect(URL, open_timeout=15) as ws:
        rec.ws = ws
        rec.start = time.monotonic()
        await rec._pump(0.8)
        await rec.hold("01")

        for _ in range(8):
            if rec.frames and "PRESS ANY KEY" in plain(rec.frames[-1]["d"]):
                break
            await rec.key(" ")
        await rec.key(" ")
        await rec.wait_for("ENTER YOUR HANDLE")
        await rec.type("viewer")
        await rec.key("\r")
        await rec.wait_for("CHOOSE A PASSWORD")
        await rec.type("phosphor")
        await rec.key("\r")
        await rec.wait_for("TYPE IT AGAIN")
        await rec.type("phosphor")
        await rec.key("\r")
        await rec.wait_for("MAIN MENU")
        await rec.hold("02")

        await rec.key("b")
        await rec.wait_for("BOARDS")
        await rec.key("1")
        await rec.wait_for("THE LOBBY")
        await rec.hold("03")

        await rec.key("2")
        await rec.key("\r")
        await rec.wait_for("kiro online")
        await rec.hold("04")

        await rec.key("q")
        await rec.key("q")
        await rec.key("q")
        await rec.wait_for("MAIN MENU")
        await rec.key("e")
        await rec.wait_for("ESCALATIONS")
        await rec.hold("05")

        await rec.key("1")
        await rec.hold("06")
        await rec.key("q")
        await rec.wait_for("MAIN MENU")

        await rec.key("v")
        await rec.wait_for("THE BUILD")
        await rec.hold("07")

        await rec.key("q")
        await rec.wait_for("MAIN MENU")
        await rec.key("q")
        await rec.wait_for("carrier lost")
        await rec.hold("08")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec.frames), encoding="utf-8")
    (out.parent / "marks.json").write_text(json.dumps(rec.marks, indent=2), encoding="utf-8")
    print("frames", len(rec.frames), "duration", rec.frames[-1]["t"] if rec.frames else 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="demo/session.json")
    parser.add_argument("--voice", default="demo/voice")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    timing_path = root / args.voice / "timing.json"
    timing = {item["id"]: item["seconds"] for item in json.loads(timing_path.read_text(encoding="utf-8"))}
    asyncio.run(run(root / args.out, timing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
