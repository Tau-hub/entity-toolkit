"""Generates ok.wav and ko.wav next to this script: two short, soft synthesised tones (a rising pair for "ok", a falling pair for "not ok").

Pure synthesis, no third-party audio. Change LEVEL to make them louder or quieter (peak amplitude, 0 to 1), then run:  python sounds/gen_sounds.py
"""
import math
import struct
import wave
from pathlib import Path

SR = 44100
OUT = Path(__file__).parent
LEVEL = 0.15


def note(f, d, att):
    """A sine with a little second harmonic, a short attack and an exponential decay."""
    n = int(SR * d)
    out, ph = [], 0.0
    for i in range(n):
        t = i / n
        ph += 2 * math.pi * f / SR
        env = min(1.0, i / (SR * att)) * math.exp(-8 * t) * min(1.0, (n - i) / (SR * 0.03))
        out.append((math.sin(ph) + 0.25 * math.sin(2 * ph)) * env)
    return out


def save(name, samples):
    peak = max(abs(x) for x in samples)
    with wave.open(str(OUT / name), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(x / peak * LEVEL * 32767)) for x in samples))


if __name__ == "__main__":
    save("ok.wav", note(587, .06, .01) + note(880, .15, .008))
    save("go.wav", note(784, .11, .006))  # one short blip: "got it, sending"
    save("ko.wav", note(392, .10, .015) + note(294, .30, .008))
