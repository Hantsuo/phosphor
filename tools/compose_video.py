"""
Compose the final cut: expand the frame log to a constant 20 fps sequence,
add the narration, and encode one MP4.

    python tools/compose_video.py --out docs/demo.mp4
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from render_video import caption_at, parse, render  # noqa: E402

FPS = 20


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", default="demo/session.json")
    parser.add_argument("--narration", default="demo/narration.wav")
    parser.add_argument("--out", default="docs/demo.mp4")
    args = parser.parse_args()

    frames = json.loads((ROOT / args.session).read_text(encoding="utf-8"))
    marks_path = ROOT / "demo" / "marks.json"
    marks = json.loads(marks_path.read_text(encoding="utf-8")) if marks_path.exists() else {}

    total = frames[-1]["t"]
    ticks = int(total * FPS) + 1

    seq_dir = ROOT / "demo" / "seq"
    if seq_dir.exists():
        shutil.rmtree(seq_dir)
    seq_dir.mkdir(parents=True)

    index = 0
    cache: dict[tuple[str, str], Path] = {}
    for tick in range(ticks):
        t = tick / FPS
        while index + 1 < len(frames) and frames[index + 1]["t"] <= t:
            index += 1
        key = (frames[index]["d"], caption_at(t, marks))
        target = seq_dir / f"{tick:05d}.png"
        if key in cache:
            shutil.copyfile(cache[key], target)
            continue
        grid = parse(frames[index]["d"])
        image = render(grid, key[1])
        image.save(target)
        cache[key] = target

    ffmpeg = shutil.which("ffmpeg") or r"C:\Users\Administrator\.agent-reach\tools\ffmpeg\bin\ffmpeg.exe"
    out = ROOT / args.out
    cmd = [
        ffmpeg, "-nostdin", "-y",
        "-framerate", str(FPS), "-i", str(seq_dir / "%05d.png"),
        "-i", str(ROOT / args.narration),
        "-t", f"{total - 0.1:.2f}",
        "-threads", "2",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-threads", "2", str(out),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr[-600:])
        return result.returncode
    print("wrote", args.out, "ticks", ticks, "duration", round(total, 1), "s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
