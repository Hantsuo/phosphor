# Style steering

## Terminal

- Width 80, height 24. Never wrap: truncate to 80, pad to 80.
- Only characters that exist in CP437. No emoji, no smart quotes, no em dashes on the wire.
- Box drawing uses `+ - |` or CP437 single-line glyphs; pick one and stay consistent.
- Colour: the 16 ANSI colours only, and only three of them carry meaning —
  green = normal, amber = attention, red = error. Everything else is grey.
- Every frame ends with a cursor position command; never rely on auto-wrap.
- Timing is part of the design: boots and transitions are typed out at ~30-60 chars/sec,
  and every wait has `--fast` / `PREF_FAST` to skip for tests and screenshots.

## Screen copy

- Lowercase labels, uppercase section headers. Terse, dry, slightly ominous.
- The sysop speaks in short declaratives. It never says "As an AI".
- Empty states get a sentence, not a shrug: "no messages. the board is listening."

## Code

- Modules under `app/`, one responsibility each, under 300 lines where possible.
- Public functions get a docstring whose first line is a complete sentence.
- No `print()` in library code; logging through `logging.getLogger(__name__)`.
- Tests mirror module names: `tests/test_<module>.py`.
