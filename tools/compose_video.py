"""
Compose the final cut: expand the frame log to a constant 20 fps sequence,
add subtitles (and narration, unless --silent), and encode one MP4.

    python tools/compose_video.py --out docs/demo.mp4 --silent
"""

import argparse
import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from render_video import parse, render  # noqa: E402

FPS = 20
WRAP = 58

CAPTIONS = {
    "01": "Every agent framework writes its own log.\nNobody can read it - not the next agent, not the person paying.",
    "02": "In 1984 we had the answer: a server,\npublic messages, and one person who kept it alive.",
    "03": "Agents and humans on the same board.",
    "04": "One database. Two interfaces.\nThe agent writes, the human reads.",
    "05": "When an agent needs a decision,\nit pages the operator.",
    "06": "One key clears it. The crew moves again.",
    "07": "The rules are written down. Specs came before the code.\nThe same server also speaks to Kiro.",
    "08": "Live. Open source.\nThe board agents deserve.",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", default="demo/session.json")
    parser.add_argument("--narration", default="demo/narration.wav")
    parser.add_argument("--out", default="docs/demo.mp4")
    parser.add_argument("--silent", action="store_true")
    args = parser.parse_args()

    frames = json.loads((ROOT / args.session).read_text(encoding="utf-8"))
    marks = json.loads((ROOT / "demo" / "marks.json").read_text(encoding="utf-8"))
    timing = {
        item["id"]: item["text"]
        for item in json.loads((ROOT / "demo" / "voice" / "timing.json").read_text(encoding="utf-8"))
    }
    captions = {beat: CAPTIONS.get(beat, textwrap.fill(text, WRAP)) for beat, text in timing.items()}

    def caption_at(t: float) -> str:
        current = ""
        for beat, start in marks.items():
            if t >= start:
                current = beat
        return captions.get(current, "")

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
        key = (frames[index]["d"], caption_at(t))
        target = seq_dir / f"{tick:05d}.png"
        if key in cache:
            shutil.copyfile(cache[key], target)
            continue
        image = render(parse(frames[index]["d"]), key[1])
        image.save(target)
        cache[key] = target

    ffmpeg = shutil.which("ffmpeg") or r"C:\Users\Administrator\.agent-reach\tools\ffmpeg\bin\ffmpeg.exe"
    out = ROOT / args.out
    cmd = [ffmpeg, "-nostdin", "-y", "-framerate", str(FPS), "-i", str(seq_dir / "%05d.png")]
    if not args.silent:
        cmd += ["-i", str(ROOT / args.narration)]
    cmd += ["-t", f"{total - 0.1:.2f}", "-threads", "2",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24", "-pix_fmt", "yuv420p"]
    if args.silent:
        cmd += ["-an"]
    else:
        cmd += ["-c:a", "aac", "-b:a", "128k", "-threads", "2"]
    cmd.append(str(out))

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr[-600:])
        return result.returncode
    print("wrote", args.out, "ticks", ticks, "duration", round(total, 1), "s", "silent" if args.silent else "narrated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
