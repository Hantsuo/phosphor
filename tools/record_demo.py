"""
Record a PHOSPHOR session as a timed frame log.

Drives the real server over its real WebSocket, exactly like the browser does,
and writes every frame it receives with a timestamp. `tools/render_video.py`
turns that log into an MP4.

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


def plain(frame: str) -> str:
    return ANSI.sub("", frame).replace("\r", "")


class Recorder:
    def __init__(self) -> None:
        self.frames: list[dict] = []
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

    async def pause(self, seconds: float) -> None:
        """Hold the current frame for the camera, in real time."""
        await asyncio.sleep(seconds)
        if self.frames:
            self.frames.append({"t": round(time.monotonic() - self.start, 3), "d": self.frames[-1]["d"]})

    async def wait_for(self, text: str, timeout: float = 15.0) -> None:
        """Pump frames until the screen contains text; record everything on the way."""
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


async def run(out: Path) -> None:
    rec = Recorder()
    async with websockets.connect(URL, open_timeout=15) as ws:
        rec.ws = ws
        rec.start = time.monotonic()
        await rec._pump(0.8)                       # boot frame

        # boot: tap through the handshake until the title art asks for a key
        for _ in range(8):
            if rec.frames and "PRESS ANY KEY" in plain(rec.frames[-1]["d"]):
                break
            await rec.key(" ")
            await rec.pause(0.55)
        await rec.wait_for("PRESS ANY KEY")
        await rec.pause(1.2)

        await rec.key(" ")
        await rec.wait_for("ENTER YOUR HANDLE")
        await rec.pause(1.0)

        await rec.type("viewer")
        await rec.key("\r")
        await rec.wait_for("CHOOSE A PASSWORD")
        await rec.pause(0.5)
        await rec.type("phosphor")
        await rec.key("\r")
        await rec.wait_for("TYPE IT AGAIN")
        await rec.pause(0.4)
        await rec.type("phosphor")
        await rec.key("\r")
        await rec.wait_for("MAIN MENU")
        await rec.pause(1.6)

        await rec.key("b")
        await rec.wait_for("BOARDS")
        await rec.pause(1.8)

        await rec.key("1")
        await rec.wait_for("THE LOBBY")
        await rec.pause(1.8)

        await rec.key("2")
        await rec.key("\r")
        await rec.wait_for("kiro online")
        await rec.pause(2.6)
        await rec.key("q")
        await rec.pause(1.2)
        await rec.key("q")
        await rec.pause(1.0)
        await rec.key("q")
        await rec.wait_for("MAIN MENU")
        await rec.pause(1.0)

        await rec.key("e")
        await rec.wait_for("ESCALATIONS")
        await rec.pause(2.4)
        await rec.key("1")                          # clear the one waiting
        await rec.pause(1.6)
        await rec.key("q")
        await rec.wait_for("MAIN MENU")
        await rec.pause(0.8)

        await rec.key("s")
        await rec.wait_for("SYSOP'S DESK")
        await rec.pause(3.2)

        await rec.key("q")
        await rec.pause(0.6)
        await rec.key("q")
        await rec.wait_for("carrier lost")
        await rec.pause(1.4)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec.frames), encoding="utf-8")
    print("frames", len(rec.frames), "duration", rec.frames[-1]["t"] if rec.frames else 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="demo/session.json")
    args = parser.parse_args()
    asyncio.run(run(Path(args.out)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
