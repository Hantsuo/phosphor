"""
Lay the narration onto the video timeline.

Places each segment at the mark its beat started, fills the rest with silence,
and writes demo/narration.wav. Run after tools/record_demo.py.

    python tools/build_audio.py
"""

import json
import wave
from pathlib import Path

import numpy as np

RATE = 32000


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as handle:
        assert handle.getframerate() == RATE, f"{path} is {handle.getframerate()} Hz"
        data = handle.readframes(handle.getnframes())
    return np.frombuffer(data, np.int16).astype(np.float32) / 32768.0


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    voice = root / "demo" / "voice"
    timing = {item["id"]: item for item in json.loads((voice / "timing.json").read_text(encoding="utf-8"))}
    marks = json.loads((root / "demo" / "marks.json").read_text(encoding="utf-8"))
    frames = json.loads((root / "demo" / "session.json").read_text(encoding="utf-8"))
    total = frames[-1]["t"] + 0.8

    buffer = np.zeros(int(total * RATE) + RATE, np.float32)
    for beat, start in marks.items():
        wav = voice / f"{beat}.wav"
        if not wav.exists():
            continue
        audio = read_wav(wav)
        offset = int(start * RATE)
        end = min(len(buffer), offset + len(audio))
        buffer[offset:end] += audio[: end - offset]

    # keep peaks under control
    peak = float(np.max(np.abs(buffer))) or 1.0
    if peak > 0.95:
        buffer = buffer * (0.95 / peak)

    out = root / "demo" / "narration.wav"
    with wave.open(str(out), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes((buffer * 32767).astype(np.int16).tobytes())
    print("wrote", out, f"{total:.1f}s", "peak", round(peak, 3))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
