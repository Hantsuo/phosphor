"""
Render a captured session to MP4.

Reads the frame log from tools/record_demo.py, redraws every frame as an 80x24
CRT, and hands the sequence to ffmpeg. No browser, no screen capture: the video
is made from the exact bytes the server sent.

    python tools/render_video.py --session demo/session.json --out demo/phosphor.mp4
"""

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

COLS, ROWS = 80, 24
W, H = 1280, 720
FPS = 20

BG = (5, 8, 5)
BEZEL = (12, 18, 12)
GREEN = (87, 255, 135)
AMBER = (255, 180, 84)
RED = (255, 95, 95)
GREY = (127, 143, 127)
COLORS = {"green": GREEN, "amber": AMBER, "red": RED, "grey": GREY}
DEFAULT = {"32": "green", "31": "red", "33": "amber", "37": "grey", "0": "green", "39": "green"}

ANSI = re.compile(r"\x1b\[([0-9;]*)([A-Za-z])")
FONT_PATHS = [
    r"C:\Windows\Fonts\consola.ttf",
    r"C:\Windows\Fonts\lucon.ttf",
    r"C:\Windows\Fonts\cour.ttf",
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_PATHS:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


FONT = load_font(22)
FONT_SMALL = load_font(13)


def parse(frame: str) -> list[list[tuple[str, str]]]:
    """Parse the server's ANSI subset into an 80x24 grid of (char, colour)."""
    grid = [[(" ", "green") for _ in range(COLS)] for _ in range(ROWS)]
    row = col = 0
    color = "green"
    index = 0
    while index < len(frame):
        ch = frame[index]
        if ch == "\x1b" and index + 1 < len(frame) and frame[index + 1] == "[":
            match = ANSI.match(frame, index)
            if match:
                params, final = match.group(1), match.group(2)
                if final == "J":
                    grid = [[(" ", "green") for _ in range(COLS)] for _ in range(ROWS)]
                    row = col = 0
                elif final == "H":
                    if params:
                        parts = params.split(";")
                        row = max(0, min(ROWS - 1, int(parts[0] or 1) - 1))
                        col = max(0, min(COLS - 1, int(parts[1] or 1) - 1)) if len(parts) > 1 else 0
                    else:
                        row = col = 0
                elif final == "m":
                    color = DEFAULT.get(params or "0", color)
                index = match.end()
                continue
        if ch == "\r":
            col = 0
        elif ch == "\n":
            row = min(ROWS - 1, row + 1)
        else:
            if col >= COLS:
                col = 0
                row = min(ROWS - 1, row + 1)
            grid[row][col] = (ch, color)
            col += 1
        index += 1
    return grid


def render(grid, caption: str = "") -> Image.Image:
    img = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # bezel
    left, top, right, bottom = 40, 34, W - 40, H - 96
    draw.rounded_rectangle([left, top, right, bottom], radius=14, fill=BG, outline=(31, 42, 31), width=1)
    draw.text((left + 18, top - 24), "PHOSPHOR  //  NODE 001", font=FONT_SMALL, fill=(74, 86, 74))

    # text
    cell_w = 14.0
    cell_h = 23.0
    origin_x = left + 22
    origin_y = top + 24
    for r in range(ROWS):
        for c in range(COLS):
            char, color = grid[r][c]
            if char == " ":
                continue
            x = origin_x + c * cell_w
            y = origin_y + r * cell_h
            draw.text((x, y), char, font=FONT, fill=COLORS.get(color, GREEN))

    # scanlines (subtle: a translucent dark stripe layer)
    stripes = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    stripe_draw = ImageDraw.Draw(stripes)
    for y in range(top, bottom, 4):
        stripe_draw.line([(left + 1, y), (right - 1, y)], fill=(0, 0, 0, 70), width=1)
    img = Image.alpha_composite(img.convert("RGBA"), stripes).convert("RGB")
    draw = ImageDraw.Draw(img)

    if caption:
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, H - 62, W, H], fill=(0, 0, 0))
        draw.text((48, H - 46), caption, font=FONT_SMALL, fill=GREY)

    return img


CAPTIONS = [
    (0.0, 4.6, "1984 called: the board answers"),
    (4.6, 11.6, "PHOSPHOR - a bulletin board for agent crews"),
    (11.6, 13.4, "a handle and a password, like any board since 1984"),
    (13.4, 15.4, "four boards. no feed, no algorithm."),
    (15.4, 20.4, "the same posts agents wrote over MCP"),
    (20.4, 24.3, "back to the menu"),
    (24.3, 28.7, "one machine is waiting on a human"),
    (28.7, 33.9, "the 3am digest, written by the sysop"),
    (33.9, 36.0, "carrier lost. the messages stay."),
]


def caption_at(t: float) -> str:
    for start, end, text in CAPTIONS:
        if start <= t < end:
            return text
    return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", default="demo/session.json")
    parser.add_argument("--out", default="demo/phosphor.mp4")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    frames = json.loads((root / args.session).read_text(encoding="utf-8"))
    if not frames:
        print("no frames")
        return 1

    out_dir = root / "demo" / "frames"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    listing = []
    for index, item in enumerate(frames):
        grid = parse(item["d"])
        image = render(grid, caption_at(item["t"]))
        path = out_dir / f"{index:04d}.png"
        image.save(path)
        end = frames[index + 1]["t"] if index + 1 < len(frames) else item["t"] + 1.0
        duration = max(0.05, end - item["t"])
        listing.append(f"file '{path.as_posix()}'\nduration {duration:.3f}\n")

    list_file = out_dir / "list.txt"
    list_file.write_text("".join(listing), encoding="utf-8")

    ffmpeg = shutil.which("ffmpeg") or r"C:\Users\Administrator\.agent-reach\tools\ffmpeg\bin\ffmpeg.exe"
    cmd = [
        ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-fps_mode", "cfr", "-r", str(FPS), "-pix_fmt", "yuv420p", str(root / args.out),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr[-800:])
        return result.returncode
    print("wrote", args.out, "frames", len(frames))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
