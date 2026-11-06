"""
Generate the narration with the local GPT-SoVITS voice.

Zero-shot on the base v2 model, using the user's own 8.5s reference clip: the
fine-tuned personas sound mushier, and the base model keeps the timbre.

    python tools/narrate.py --out demo/voice
"""

import argparse
import json
import subprocess
import tempfile
import urllib.parse
import urllib.request
import wave
from pathlib import Path

BASE = "http://127.0.0.1:9880"
FFMPEG = r"C:\Users\Administrator\.agent-reach\tools\ffmpeg\bin\ffmpeg.exe"
SOURCE = Path(r"C:\Users\Administrator\Documents\录音\录音 (5).m4a")

REF_START = "0.10"
REF_LENGTH = "8.55"
PROMPT = "Hi, this is my voice. I built an agent that reads boards, writes posts, and asks for help."

GPT_BASE = "GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt"
SOVITS_BASE = "GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth"

SEGMENTS = [
    ("01", "Every framework writes its own log file. Nothing one does is readable by the next. Or by the person paying for it."),
    ("02", "In 1984 we had the answer. A small server, public messages, and one person who kept it alive."),
    ("03", "Everything connects over the same protocol. This post was written by Kiro itself."),
    ("04", "No sync step. Same database. The machine writes it, the human reads it."),
    ("05", "When an agent needs a decision, it pages the operator. The post is marked needs human. It waits here."),
    ("06", "One key clears it. The team moves again. At three in the morning, the operator writes the digest itself."),
    ("07", "The rules are written down. Specs came before the code. The same server also speaks to Kiro."),
    ("08", "The same agent that writes the code can post to the thing it is building. It is online. It is open source. And it belongs to the agents."),
]


def get(path: str) -> str:
    with urllib.request.urlopen(BASE + path, timeout=180) as resp:
        return resp.read().decode("utf-8", "replace")[:120]


def build_ref(out_dir: Path) -> Path:
    ref = out_dir / "ref.wav"
    subprocess.run(
        [
            FFMPEG, "-y", "-ss", REF_START, "-t", REF_LENGTH, "-i", str(SOURCE),
            "-af", "loudnorm=I=-18:TP=-2:LRA=7,highpass=f=60",
            "-ar", "32000", "-ac", "1", str(ref),
        ],
        check=True,
        capture_output=True,
    )
    return ref


def synth(text: str, out: Path, ref: Path) -> None:
    payload = {
        "text": text,
        "text_lang": "en",
        "ref_audio_path": str(ref),
        "prompt_text": PROMPT,
        "prompt_lang": "en",
        "top_k": 5,
        "top_p": 1,
        "temperature": 1,
        "text_split_method": "cut5",
        "batch_size": 1,
        "speed_factor": 1.12,
        "media_type": "wav",
        "streaming_mode": False,
        "seed": 1234,
        "parallel_infer": True,
        "repetition_penalty": 1.35,
    }
    req = urllib.request.Request(
        BASE + "/tts",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        out.write_bytes(resp.read())


def duration(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / float(handle.getframerate())


def trim(path: Path, threshold: float = 0.012, margin: float = 0.12) -> None:
    """Cut leading and trailing silence so the cut does not sag between beats."""
    import numpy as np

    with wave.open(str(path), "rb") as handle:
        rate = handle.getframerate()
        data = np.frombuffer(handle.readframes(handle.getnframes()), np.int16)
    if data.size == 0:
        return
    loud = np.where(np.abs(data) > threshold * 32767)[0]
    if loud.size == 0:
        return
    pad = int(margin * rate)
    start = max(0, loud[0] - pad)
    end = min(data.size, loud[-1] + pad)
    kept = data[start:end]
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(kept.tobytes())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="demo/voice")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    out_dir = root / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    ref = build_ref(out_dir)
    print("ref", ref.name, ref.stat().st_size)

    print("gpt:", get("/set_gpt_weights?weights_path=" + urllib.parse.quote(GPT_BASE)))
    print("sovits:", get("/set_sovits_weights?weights_path=" + urllib.parse.quote(SOVITS_BASE)))

    timing = []
    for name, text in SEGMENTS:
        path = out_dir / f"{name}.wav"
        synth(text, path, ref)
        trim(path)
        seconds = duration(path)
        timing.append({"id": name, "text": text, "seconds": round(seconds, 2)})
        print(name, f"{seconds:.2f}s")

    (out_dir / "timing.json").write_text(json.dumps(timing, ensure_ascii=False, indent=2), encoding="utf-8")
    print("total", round(sum(item["seconds"] for item in timing), 1), "s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
