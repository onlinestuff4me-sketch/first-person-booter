#!/usr/bin/env python3
"""Synthesize every sound effect for First-Person Booter from scratch.
22 kHz mono WAVs into pk3/sounds/. Tweak seeds/params freely and re-run;
SNDINFO maps the lump names to logical names."""

import wave
from pathlib import Path

import numpy as np

SR = 22050
OUT = Path(__file__).resolve().parent.parent / "pk3" / "sounds"


# ---------------------------------------------------------------- plumbing --

def write(name, sig):
    OUT.mkdir(parents=True, exist_ok=True)
    sig = np.asarray(sig, dtype=np.float64)
    peak = float(np.max(np.abs(sig)))
    if peak < 1e-9:
        peak = 1.0
    sig = np.clip(sig / peak * 0.82, -1, 1)
    path = OUT / f"{name}.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((sig * 32767).astype("<i2").tobytes())
    print(f"  {path.name}  ({len(sig)/SR:.2f}s)")


def lowpass(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1.0 / (1.0 + (f / max(cutoff, 1.0)) ** 4)
    return np.fft.irfft(X, len(x))


def highpass(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    r = (f / max(cutoff, 1.0)) ** 2
    X *= r / (1.0 + r)
    return np.fft.irfft(X, len(x))


def bandpass(x, lo, hi):
    return highpass(lowpass(x, hi), lo)


def echo(sig, delay=0.11, fb=0.35, taps=2):
    d = int(delay * SR)
    out = np.concatenate([sig, np.zeros(d * taps + int(0.15 * SR))])
    for i in range(1, taps + 1):
        out[i * d:i * d + len(sig)] += sig * (fb ** i)
    return out


# --------------------------------------------------------------- the brass --

def fart(dur=0.55, f0=85, seed=1, sputter=0.55, squeak=False, sub=0.0):
    """The house specialty: wobbling detuned saws through a fluttering gate."""
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    t = np.arange(n) / SR

    wob = lowpass(rng.standard_normal(n), 7)
    wob /= max(1e-9, np.max(np.abs(wob)))
    freq = f0 * np.linspace(1.0, 0.72, n) * (1 + 0.22 * wob)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    raw = (2 * ((phase / (2 * np.pi)) % 1.0) - 1) \
        + 0.45 * (2 * (((2.03 * phase) / (2 * np.pi)) % 1.0) - 1)

    flut = 0.55 + 0.45 * np.sin(2 * np.pi * (9 + 7 * rng.random()) * t
                                + rng.random() * 6)

    gate = np.ones(n)
    for _ in range(int(sputter * 6)):
        s = int(rng.random() * n * 0.8)
        L = int(SR * (0.01 + 0.03 * rng.random()))
        gate[s:s + L] *= 0.12
    gate = np.clip(lowpass(gate, 60), 0, 1)

    env = np.ones(n)
    a = max(1, int(0.012 * SR))
    env[:a] = np.linspace(0, 1, a)
    d = max(1, int(0.30 * n))
    env[-d:] *= np.linspace(1, 0, d) ** 1.5

    sig = np.tanh(2.3 * raw * flut * gate) * env
    sig += lowpass(rng.standard_normal(n), 900) * 0.16 * env * gate
    if sub > 0:
        sig += sub * np.sin(phase * 0.5) * env
    if squeak:
        sn = int(0.12 * SR)
        st = np.arange(sn) / SR
        sig[-sn:] += np.sin(2 * np.pi * (300 + 7500 * st) * st) \
            * np.linspace(0.35, 0, sn)
    return sig


def whoosh(dur=0.26, lo=250, hi=900, seed=5):
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    a = bandpass(rng.standard_normal(n), lo, lo * 2.2)
    b = bandpass(rng.standard_normal(n), hi, hi * 2.2)
    x = np.linspace(0, 1, n)
    return (a * (1 - x) + b * x) * np.sin(np.pi * x) ** 1.5


def splat(dur=0.32, seed=9, boom=0.5):
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    t = np.arange(n) / SR
    fr = 150 * np.exp(-t * 9) + 42
    thump = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 11) * boom * 1.6
    crack = highpass(rng.standard_normal(n), 1500) * np.exp(-t * 38) * 0.9
    wobble = 0.6 + 0.4 * np.sin(2 * np.pi * 23 * t + 1)
    squish = lowpass(rng.standard_normal(n), 620) * np.exp(-t * 8) * wobble * 0.9
    return thump + crack + squish


def thud(dur=0.16, seed=3):
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    t = np.arange(n) / SR
    fr = 90 * np.exp(-t * 14) + 34
    body = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 16)
    tick = highpass(rng.standard_normal(n), 2500) * np.exp(-t * 120) * 0.4
    return body + tick


def squish_blip(dur=0.08, seed=12):
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    t = np.arange(n) / SR
    wobble = 0.5 + 0.5 * np.sin(2 * np.pi * 40 * t)
    return lowpass(rng.standard_normal(n), 700) * np.exp(-t * 30) * wobble


def choke(seed=21):
    rng = np.random.default_rng(seed)
    n = int(SR * 0.45)
    sig = np.zeros(n)
    for i, (at, amp) in enumerate([(0.0, 1.0), (0.13, 0.8), (0.28, 0.55)]):
        pn = int(SR * 0.09)
        pt = np.arange(pn) / SR
        puff = lowpass(rng.standard_normal(pn), 700) * np.exp(-pt * 26) * amp
        puff += np.sign(np.sin(2 * np.pi * 210 * pt)) * np.exp(-pt * 30) * 0.12 * amp
        s = int(at * SR)
        sig[s:s + pn] += puff
    return sig


def inhale(dur=0.5, seed=33):
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    x = np.linspace(0, 1, n)
    a = bandpass(rng.standard_normal(n), 280, 700)
    b = bandpass(rng.standard_normal(n), 1100, 2400)
    return (a * (1 - x) + b * x) * (x ** 1.2) * 0.9


def fanfare(seed=44):
    """Pickup jingle: triumphant arpeggio, then a small editorial comment."""
    notes = [262, 330, 392, 523]
    parts = []
    for i, f in enumerate(notes):
        n = int(SR * 0.095)
        t = np.arange(n) / SR
        tone = np.sign(np.sin(2 * np.pi * f * t)) * 0.5 \
            + 0.25 * np.sin(2 * np.pi * f * 2 * t)
        env = np.minimum(1, np.linspace(0, 12, n))
        env *= np.linspace(1, 0.55 if i < 3 else 0.2, n)
        parts.append(tone * env)
        parts.append(np.zeros(int(SR * 0.012)))
    parts.append(fart(0.3, 96, seed, sputter=0.3, squeak=True) * 0.8)
    return np.concatenate(parts)


def hiss_loop(dur=1.2, seed=55):
    rng = np.random.default_rng(seed)
    f = int(SR * 0.2)
    n = int(SR * dur)
    raw = lowpass(rng.standard_normal(n + f), 800) * 0.6
    out = raw[:n].copy()
    ramp = np.linspace(0, 1, f)
    out[:f] = raw[:f] * ramp + raw[n:n + f] * (1 - ramp)  # seamless loop
    return out


def sizzle(dur=0.9, seed=66):
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    t = np.arange(n) / SR
    crackle = highpass(rng.standard_normal(n), 1800) * (rng.random(n) ** 5)
    base = highpass(rng.standard_normal(n), 900) * 0.25
    return (crackle + base) * np.exp(-t * 3.2)


def leak(dur=0.3, seed=88):
    """The quiet betrayal: a small, apologetic squeak."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = 430 - 260 * t / dur
    flut = 0.6 + 0.4 * np.sin(2 * np.pi * 21 * t)
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.6
    return np.tanh(1.8 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * flut * env * 0.5


def eyesqueak(dur=0.18, seed=99):
    """Punted-eyeball flight noise: a small indignant rising squeak."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = 620 + 1400 * (t / dur) + 70 * np.sin(2 * np.pi * 36 * t)
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 0.8
    return np.tanh(1.6 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * env


def bubbles(seed=77):
    n = int(SR * 0.3)
    sig = np.zeros(n)
    for at, f0, f1 in [(0.0, 130, 320), (0.16, 160, 430)]:
        bn = int(SR * 0.09)
        bt = np.arange(bn) / SR
        chirp = np.sin(2 * np.pi * (f0 + (f1 - f0) * bt / 0.09) * bt)
        s = int(at * SR)
        sig[s:s + bn] += chirp * np.exp(-bt * 24)
    return sig


if __name__ == "__main__":
    print("Synthesizing sounds...")
    write("BWHOOSH", whoosh())
    write("BSPLAT", splat(seed=9))
    write("BTHUD", thud())
    write("BGIB", np.concatenate([splat(0.5, seed=14, boom=0.95),
                                  sizzle(0.25, seed=15) * 0.3]))
    write("SQUISH", squish_blip())
    write("FART1", fart(0.5, 92, seed=101, sputter=0.5))
    write("FART2", fart(0.72, 76, seed=202, sputter=0.75, squeak=True))
    write("FART3", fart(0.38, 108, seed=303, sputter=0.3))
    write("FART4", fart(0.3, 150, seed=505, sputter=0.2, squeak=True))
    write("FART5", fart(0.85, 88, seed=606, sputter=1.4))
    write("FARTPOP", fart(0.18, 170, seed=707, sputter=0.1))
    write("LEAK", leak())
    write("MEGAFART", echo(fart(1.6, 46, seed=404, sputter=0.85, sub=0.5)))
    write("INHALE", inhale())
    write("CHOKE", choke())
    write("CHEEKS", fanfare())
    write("GASHISS", hiss_loop())
    write("SIZZLE", sizzle())
    write("GOOBLUB", bubbles())
    write("EYESQK", eyesqueak())
    print("Done.")
