#!/usr/bin/env python3
"""Generate every sprite/graphic for First-Person Booter as PNGs with Doom
grAb offset chunks. Cartoon placeholder art, drawn from scratch — replace at
will (see README "Upgrading the ass-ets").

Offset cheat sheet (how GZDoom positions sprites):
  * HUD weapon sprites live on a 320x200 canvas. With the gun at rest,
    screen_left = 1 - leftoffset, screen_top = 32 - topoffset.
  * World sprites standing on the floor: offsets (w//2, h).
  * Floating projectiles/FX: offsets (w//2, h//2 + a little).
Tune the SCREEN_* constants below if art lands off-target on your setup.
"""

import math
import random
import struct
import zlib
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SPR = ROOT / "pk3" / "sprites"
GFX = ROOT / "pk3" / "graphics"

# Where HUD art sits on the 320x200 weapon canvas: (left, top) per frame.
SCREEN_BOOT = {"A": (140, 130), "B": (160, 155), "C": (55, 85), "D": (12, 15)}
SCREEN_BUTT_LEFT = -78   # extra width so 16:9 screens still get full cheeks
SCREEN_BUTT_TOP = 152    # lower ~20-24% of the 200-unit-tall view


# ---------------------------------------------------------------- plumbing --

def save(img, folder, name, offx, offy):
    """Save PNG and splice in a grAb chunk right after IHDR."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.png"
    from io import BytesIO
    buf = BytesIO()
    img.save(buf, "PNG")
    raw = buf.getvalue()
    payload = struct.pack(">ii", offx, offy)
    chunk = (struct.pack(">I", 8) + b"grAb" + payload
             + struct.pack(">I", zlib.crc32(b"grAb" + payload) & 0xFFFFFFFF))
    with open(path, "wb") as f:
        f.write(raw[:33] + chunk + raw[33:])
    print(f"  {path.relative_to(ROOT)}  ({img.width}x{img.height} @ {offx},{offy})")


def canvas(w, h):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def star(draw, cx, cy, points, r_out, r_in, fill, outline=None, width=2, rot=0.0):
    pts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = rot + math.pi * i / points
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    draw.polygon(pts, fill=fill, outline=outline, width=width)


def blob(draw, cx, cy, r, color, rng, lumps=8, wobble=0.35, outline=None, width=3):
    pts = []
    for i in range(lumps):
        a = 2 * math.pi * i / lumps
        rr = r * (1 - wobble / 2 + wobble * rng.random())
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    draw.polygon(pts, fill=color, outline=outline, width=width)


def puff_cluster(draw, cx, cy, r, rng, layers):
    """layers = [(scale, color), ...] painted big->small for a cartoon cloud."""
    spots = [(rng.uniform(-0.55, 0.55) * r, rng.uniform(-0.4, 0.4) * r,
              rng.uniform(0.45, 0.72) * r) for _ in range(7)]
    for scale, color in layers:
        for dx, dy, rr in spots:
            s = rr * scale
            draw.ellipse([cx + dx - s, cy + dy - s, cx + dx + s, cy + dy + s],
                         fill=color)


def stink_lines(draw, cx, top, h, color, n=3, width=3):
    for i in range(n):
        x = cx + (i - (n - 1) / 2) * 14
        for seg in range(3):
            y0 = top + seg * (h / 3)
            bend = 6 if seg % 2 == 0 else -6
            draw.arc([x - 6 + bend, y0, x + 6 + bend, y0 + h / 3],
                     start=90, end=270, fill=color, width=width)


# ------------------------------------------------------------------- boots --

LEATHER = (122, 74, 33, 255)
LEATHER_DK = (92, 53, 23, 255)
LEATHER_HI = (156, 106, 56, 255)
SOLE = (43, 28, 18, 255)
SOLE_DK = (28, 18, 12, 255)
OUTLINE = (26, 16, 10, 255)
LACE = (217, 201, 160, 255)


def draw_side_boot():
    """Canonical side boot, toe pointing left, on its own canvas."""
    img, d = canvas(250, 170)
    # shaft (rises at the right, i.e. toward your leg)
    d.rounded_rectangle([150, 4, 244, 120], radius=18, fill=LEATHER,
                        outline=OUTLINE, width=5)
    # vamp + toe
    d.rounded_rectangle([48, 52, 200, 122], radius=24, fill=LEATHER,
                        outline=OUTLINE, width=5)
    d.ellipse([6, 56, 110, 126], fill=LEATHER, outline=OUTLINE, width=5)
    # shading and highlight
    d.ellipse([14, 92, 104, 124], fill=LEATHER_DK)
    d.rounded_rectangle([58, 96, 196, 122], radius=12, fill=LEATHER_DK)
    d.rounded_rectangle([158, 10, 236, 34], radius=10, fill=LEATHER_HI)
    d.ellipse([20, 62, 78, 88], fill=LEATHER_HI)
    # sole
    d.rounded_rectangle([2, 116, 246, 152], radius=14, fill=SOLE,
                        outline=OUTLINE, width=5)
    d.rounded_rectangle([2, 138, 246, 152], radius=8, fill=SOLE_DK)
    for x in range(20, 240, 26):  # tread notches
        d.rectangle([x, 140, x + 10, 150], fill=(12, 8, 6, 255))
    # heel
    d.rounded_rectangle([196, 118, 246, 158], radius=8, fill=SOLE_DK,
                        outline=OUTLINE, width=4)
    # stitching along the sole line
    for x in range(14, 238, 14):
        d.ellipse([x, 112, x + 4, 116], fill=LACE)
    # laces on the shaft
    for i in range(3):
        y = 22 + i * 26
        d.line([162, y, 226, y + 16], fill=LACE, width=6)
        d.line([226, y, 162, y + 16], fill=LACE, width=6)
    return img


def draw_sole_boot():
    """Sole-first boot for the moment of impact."""
    img, d = canvas(300, 240)
    # leather rim peeking around the sole
    d.rounded_rectangle([48, 10, 252, 226], radius=70, fill=LEATHER,
                        outline=OUTLINE, width=5)
    # the sole itself
    d.rounded_rectangle([62, 22, 238, 214], radius=60, fill=SOLE,
                        outline=OUTLINE, width=6)
    # tread bars
    for y in range(48, 150, 26):
        d.rounded_rectangle([80, y, 220, y + 14], radius=7, fill=SOLE_DK)
    # heel block
    d.rounded_rectangle([84, 162, 216, 202], radius=10, fill=(58, 42, 30, 255),
                        outline=SOLE_DK, width=4)
    d.rounded_rectangle([96, 170, 204, 178], radius=4, fill=SOLE_DK)
    # toe shine
    d.arc([70, 28, 230, 120], start=200, end=340, fill=LEATHER_HI, width=8)
    # impact streaks
    for a_deg in (200, 225, 315, 340, 25, 155):
        a = math.radians(a_deg)
        x0 = 150 + 110 * math.cos(a); y0 = 118 + 100 * math.sin(a)
        x1 = 150 + 148 * math.cos(a); y1 = 118 + 132 * math.sin(a)
        d.line([x0, y0, x1, y1], fill=(255, 244, 190, 210), width=7)
    return img


def gen_boot():
    side = draw_side_boot()
    mid = side.rotate(-52, expand=True, resample=Image.BICUBIC)
    frames = {
        "A": side.rotate(-32, expand=True, resample=Image.BICUBIC),
        "B": side.rotate(-14, expand=True, resample=Image.BICUBIC),
        "C": mid.resize((int(mid.width * 1.25), int(mid.height * 1.25)),
                        Image.BICUBIC),
        "D": draw_sole_boot(),
    }
    for letter, img in frames.items():
        left, top = SCREEN_BOOT[letter]
        save(img, SPR, f"BOOT{letter}0", 1 - left, 32 - top)


# ------------------------------------------------------------------ cheeks --

SKIN = (232, 180, 140, 255)
SKIN_SH = (198, 142, 102, 255)
SKIN_DK = (160, 105, 70, 255)
SKIN_HI = (248, 214, 180, 255)
SKIN_LINE = (122, 69, 38, 255)
GAS_CORE = (214, 247, 168, 255)
GAS_LT = (168, 224, 106, 255)
GAS_MD = (111, 174, 67, 255)
GAS_DK = (62, 122, 42, 255)


def draw_cheek(d, cx, top, w, h, squeeze=1.0):
    w = int(w * squeeze)
    box = [cx - w // 2, top, cx + w // 2, top + h]
    d.ellipse(box, fill=SKIN, outline=SKIN_LINE, width=6)
    # under-shading toward the crack and bottom
    d.ellipse([cx - w // 2 + 14, top + int(h * 0.45),
               cx + w // 2 - 14, top + h - 6], fill=SKIN_SH)
    d.ellipse([cx - w // 2 + 30, top + int(h * 0.62),
               cx + w // 2 - 30, top + h - 12], fill=SKIN_DK)
    # top highlight
    d.ellipse([cx - int(w * 0.28), top + 10, cx + int(w * 0.06), top + 34],
              fill=SKIN_HI)


def gen_butt():
    W, H = 480, 130
    for letter in "ABCD":
        img, d = canvas(W, H)
        mid = W // 2
        spread = {"A": 0, "B": -16, "C": 30, "D": 2}[letter]
        squeeze = {"A": 1.0, "B": 0.88, "C": 1.0, "D": 1.0}[letter]
        drop = {"A": 0, "B": -6, "C": 4, "D": 8}[letter]

        if letter == "C":  # the event itself, behind the cheeks
            glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow)
            gd.ellipse([mid - 120, 8, mid + 120, H + 60], fill=(150, 230, 90, 120))
            star(gd, mid, 78, 12, 95, 40, fill=(190, 240, 120, 200))
            star(gd, mid, 78, 8, 55, 22, fill=(235, 255, 190, 235))
            img.alpha_composite(glow)

        draw_cheek(d, mid - 122 - spread, 16 + drop, 250, 190, squeeze)
        draw_cheek(d, mid + 122 + spread, 16 + drop, 250, 190, squeeze)
        # the crack
        d.line([mid, 42 + drop, mid, H], fill=SKIN_LINE, width=11)
        d.line([mid - 8, 46 + drop, mid - 8, H], fill=SKIN_SH, width=4)
        d.line([mid + 8, 46 + drop, mid + 8, H], fill=SKIN_SH, width=4)
        if letter == "B":  # clench wrinkles
            for ang in (-40, -15, 15, 40):
                a = math.radians(ang - 90)
                d.line([mid + 26 * math.cos(a), 60 + 20 * math.sin(a),
                        mid + 58 * math.cos(a), 60 + 44 * math.sin(a)],
                       fill=SKIN_DK, width=5)
        if letter == "D":  # lingering wisps
            stink_lines(d, mid, 6, 42, (168, 224, 106, 170), n=2, width=4)
        save(img, SPR, f"BUTT{letter}0", 1 - SCREEN_BUTT_LEFT, 32 - SCREEN_BUTT_TOP)


# ------------------------------------------------------------- projectiles --

def gen_fart_puffs():
    for i, letter in enumerate("ABC"):
        size = 52 + i * 10
        img, d = canvas(size, size)
        rng = random.Random(41 + i)
        c = size / 2
        puff_cluster(d, c, c + 2, size * 0.42, rng,
                     [(1.18, GAS_DK), (0.95, GAS_MD), (0.66, GAS_LT), (0.34, GAS_CORE)])
        save(img, SPR, f"FART{letter}0", size // 2, size // 2 + 4)


def gen_poison_cloud():
    for i, letter in enumerate("ABCD"):
        size = 116 + i * 12
        img, d = canvas(size, size)
        rng = random.Random(90 + i)
        c = size / 2
        puff_cluster(d, c, c + 6, size * 0.40, rng,
                     [(1.2, (62, 122, 42, 150)), (0.95, (111, 174, 67, 170)),
                      (0.62, (168, 224, 106, 185)), (0.3, (214, 247, 168, 200))])
        stink_lines(d, c, 4, size * 0.3, (198, 240, 140, 160), n=3, width=4)
        save(img, SPR, f"PGAS{letter}0", size // 2, size // 2 + 8)


def gen_blast_ring():
    for i, letter in enumerate("ABC"):
        size = 90 + i * 42
        img, d = canvas(size, size)
        pad = 6
        col = [(232, 216, 160, 230), (196, 224, 136, 210), (168, 224, 106, 180)][i]
        d.ellipse([pad, pad + size * 0.18, size - pad, size - pad], outline=col,
                  width=10)
        d.ellipse([pad + 14, pad + size * 0.18 + 12, size - pad - 14,
                   size - pad - 12], outline=(255, 250, 220, 130), width=4)
        save(img, SPR, f"FBLS{letter}0", size // 2, size // 2)


def gen_kick_puff():
    for i, letter in enumerate("AB"):
        size = 36 - i * 8
        img, d = canvas(size, size)
        c = size / 2
        star(d, c, c, 8, c - 2, (c - 2) * 0.42, fill=(255, 242, 176, 240),
             outline=(216, 138, 32, 255), width=2, rot=0.4 * i)
        star(d, c, c, 4, (c - 2) * 0.5, (c - 2) * 0.2, fill=(255, 255, 255, 255))
        save(img, SPR, f"KPUF{letter}0", size // 2, size // 2 + 4)


# -------------------------------------------------------------------- gore --

BLOOD_DK = (126, 24, 17, 255)
BLOOD_MD = (165, 36, 26, 255)
BLOOD_HI = (210, 74, 52, 255)
BONE = (232, 224, 208, 255)


def gen_gibs():
    for i, letter in enumerate("ABCD"):
        img, d = canvas(26, 26)
        rng = random.Random(7 + i)
        blob(d, 13, 13, 10, BLOOD_MD, rng, outline=BLOOD_DK, width=3)
        blob(d, 11, 11, 5, BLOOD_HI, rng)
        if letter in "BD":
            d.ellipse([14, 6, 22, 12], fill=BONE, outline=(150, 140, 125, 255),
                      width=1)
        save(img, SPR, f"GIBS{letter}0", 13, 17)
    # E: the splat it settles into
    img, d = canvas(30, 12)
    d.ellipse([0, 2, 29, 11], fill=BLOOD_MD, outline=BLOOD_DK, width=2)
    d.ellipse([6, 4, 16, 8], fill=BLOOD_HI)
    save(img, SPR, "GIBSE0", 15, 11)


def puddle(prefix, base, rim, inner, bub, bub_hi, seed0, bubbles=4):
    for i, letter in enumerate("ABC"):
        w, h = 90 + i * 8, 66 + i * 4
        img, d = canvas(w, h)
        rng = random.Random(seed0 + i)
        blob(d, w / 2, h / 2, min(w, h) * 0.44, base, rng,
             lumps=10, wobble=0.3, outline=rim, width=4)
        blob(d, w / 2, h / 2, min(w, h) * 0.28, inner, rng)
        for _ in range(bubbles):
            bx = w / 2 + rng.uniform(-0.25, 0.25) * w
            by = h / 2 + rng.uniform(-0.2, 0.2) * h
            r = rng.uniform(3, 6)
            d.ellipse([bx - r, by - r, bx + r, by + r], fill=bub,
                      outline=rim, width=1)
            d.ellipse([bx - r / 3, by - r / 2, bx, by], fill=bub_hi)
        save(img, SPR, f"{prefix}{letter}0", w // 2, h // 2)


def gen_goo():
    puddle("GOOP", (63, 178, 63, 220), (42, 100, 28, 255),
           (110, 210, 100, 220), (164, 224, 124, 235),
           (240, 255, 220, 255), seed0=31)


def gen_blood_pool():
    puddle("BPOL", (128, 18, 14, 225), (78, 10, 8, 255),
           (166, 32, 22, 225), (150, 26, 18, 235),
           (210, 80, 60, 255), seed0=57, bubbles=3)


def gen_eyeball():
    img, d = canvas(18, 18)
    d.ellipse([1, 3, 16, 17], fill=(60, 20, 16, 120))          # gore shadow
    d.ellipse([1, 1, 16, 16], fill=(238, 234, 224, 255),
              outline=(120, 90, 80, 255), width=2)
    d.arc([2, 2, 15, 15], start=40, end=140, fill=(200, 190, 178, 255), width=2)
    for x0, y0, x1, y1 in [(3, 9, 7, 12), (11, 4, 14, 7)]:     # veins
        d.line([x0, y0, x1, y1], fill=(190, 60, 50, 255), width=1)
    d.ellipse([5, 4, 12, 11], fill=(70, 140, 130, 255))        # iris
    d.ellipse([7, 6, 10, 9], fill=(20, 16, 14, 255))           # pupil
    d.ellipse([6, 5, 8, 7], fill=(255, 255, 255, 255))         # glint
    save(img, SPR, "EYEBA0", 9, 16)


# ----------------------------------------------------------------- pickups --

def gen_beans():
    img, d = canvas(26, 30)
    d.rounded_rectangle([2, 4, 23, 28], radius=4, fill=(143, 151, 157, 255),
                        outline=(60, 64, 68, 255), width=2)
    d.ellipse([2, 1, 23, 9], fill=(185, 192, 198, 255),
              outline=(60, 64, 68, 255), width=2)
    d.rectangle([2, 12, 23, 22], fill=(232, 220, 184, 255))
    d.line([5, 15, 20, 15], fill=(160, 40, 24, 255), width=2)  # "label text"
    d.line([5, 19, 16, 19], fill=(60, 64, 68, 255), width=1)
    save(img, SPR, "BEANA0", 13, 30)


def gen_chili():
    img, d = canvas(36, 32)
    d.rounded_rectangle([4, 10, 31, 30], radius=6, fill=(160, 40, 24, 255),
                        outline=(74, 16, 10, 255), width=2)
    d.rectangle([0, 12, 5, 18], fill=(110, 26, 16, 255))   # handles
    d.rectangle([30, 12, 35, 18], fill=(110, 26, 16, 255))
    d.ellipse([4, 6, 31, 14], fill=(110, 26, 16, 255),
              outline=(74, 16, 10, 255), width=2)
    d.ellipse([15, 3, 20, 8], fill=(74, 16, 10, 255))      # lid knob
    d.line([10, 22, 16, 26], fill=(255, 220, 120, 255), width=2)  # pepper
    stink_lines(d, 18, -2, 8, (220, 230, 200, 150), n=2, width=2)
    save(img, SPR, "CHLIA0", 18, 32)


def gen_sushi():
    for i, letter in enumerate("AB"):
        img, d = canvas(44, 30)
        d.ellipse([2, 8, 42, 30], fill=(120, 220, 90, 60 + 50 * i))  # the aura
        d.rounded_rectangle([4, 18, 40, 28], radius=3, fill=(40, 30, 26, 255),
                            outline=(16, 12, 10, 255), width=2)
        for k in range(3):
            x = 7 + k * 12
            d.ellipse([x, 8, x + 10, 20], fill=(238, 234, 224, 255),
                      outline=(150, 145, 135, 255), width=1)
            d.rectangle([x, 12, x + 10, 16], fill=(34, 60, 30, 255))
            d.ellipse([x + 2, 6, x + 8, 11], fill=(238, 150, 150, 255))
        if letter == "B":
            d.point([(12, 2), (13, 2)], fill=(20, 20, 20, 255))  # the fly
            d.line([9, 1, 11, 3], fill=(120, 120, 120, 200), width=1)
        save(img, SPR, f"MBNS{letter}0", 22, 30)


def gen_butt_pickup():
    GOLD = (232, 184, 58, 255); GOLD_DK = (184, 135, 30, 255)
    GOLD_LN = (122, 90, 16, 255)
    for i, letter in enumerate("AB"):
        img, d = canvas(46, 46)
        # cushion
        d.rounded_rectangle([2, 34, 44, 44], radius=5, fill=(90, 42, 122, 255),
                            outline=(50, 20, 70, 255), width=2)
        # golden cheeks
        lift = -2 * i
        d.ellipse([5, 12 + lift, 25, 36 + lift], fill=GOLD, outline=GOLD_LN, width=2)
        d.ellipse([21, 12 + lift, 41, 36 + lift], fill=GOLD, outline=GOLD_LN, width=2)
        d.line([23, 18 + lift, 23, 36 + lift], fill=GOLD_LN, width=3)
        d.ellipse([9, 26 + lift, 21, 34 + lift], fill=GOLD_DK)
        d.ellipse([25, 26 + lift, 37, 34 + lift], fill=GOLD_DK)
        d.ellipse([8, 15 + lift, 15, 21 + lift], fill=(255, 236, 160, 255))
        # sparkles
        spots = [(6, 8), (40, 14), (36, 40)] if i == 0 else [(40, 6), (4, 22), (10, 42)]
        for sx, sy in spots:
            star(d, sx, sy, 4, 4, 1.4, fill=(255, 255, 255, 255))
        save(img, SPR, f"BUPK{letter}0", 23, 46)


# ------------------------------------------------------------------ decals --

def gen_splats():
    for i in (1, 2):
        img, d = canvas(64, 64)
        rng = random.Random(100 + i)
        blob(d, 32, 32, 16, (78, 154, 48, 235), rng, lumps=10, wobble=0.45,
             outline=(48, 96, 30, 255), width=3)
        for _ in range(6):  # drips
            a = rng.uniform(0, 2 * math.pi)
            L = rng.uniform(14, 26)
            x1, y1 = 32 + L * math.cos(a), 32 + L * math.sin(a)
            d.line([32, 32, x1, y1], fill=(78, 154, 48, 220),
                   width=rng.randint(3, 6))
            r = rng.uniform(2, 4.5)
            d.ellipse([x1 - r, y1 - r, x1 + r, y1 + r], fill=(78, 154, 48, 235))
        blob(d, 30, 30, 7, (130, 200, 90, 235), rng)
        save(img, GFX, f"FSPLAT{i}", 32, 32)


def gen_screen_gunk():
    """Big soft red splats drawn over the view when a gib lands on the lens."""
    for i in (1, 2):
        S = 160
        img, d = canvas(S, S)
        rng = random.Random(200 + i)
        c = S / 2
        blob(d, c, c, S * 0.26, (110, 14, 10, 150), rng, lumps=12, wobble=0.5)
        blob(d, c, c, S * 0.18, (140, 22, 14, 170), rng, lumps=10, wobble=0.45)
        for _ in range(8):  # runny streaks, mostly downward
            a = rng.uniform(0.15 * math.pi, 0.85 * math.pi)
            L = rng.uniform(S * 0.2, S * 0.42)
            x1, y1 = c + L * math.cos(a), c + L * math.sin(a)
            d.line([c, c, x1, y1], fill=(120, 16, 12, 140),
                   width=rng.randint(4, 9))
            r = rng.uniform(3, 7)
            d.ellipse([x1 - r, y1 - r, x1 + r, y1 + r],
                      fill=(120, 16, 12, 150))
        blob(d, c - 8, c - 10, S * 0.08, (185, 45, 30, 160), rng)
        save(img, GFX, f"GUNK{i}", 80, 80)


if __name__ == "__main__":
    print("Generating sprites...")
    gen_boot()
    gen_butt()
    gen_fart_puffs()
    gen_poison_cloud()
    gen_blast_ring()
    gen_kick_puff()
    gen_gibs()
    gen_goo()
    gen_blood_pool()
    gen_eyeball()
    gen_beans()
    gen_chili()
    gen_sushi()
    gen_butt_pickup()
    gen_splats()
    gen_screen_gunk()
    print("Done.")
