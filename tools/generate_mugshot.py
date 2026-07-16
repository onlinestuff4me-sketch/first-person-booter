#!/usr/bin/env python3
"""Generate the optional Cheeky Mug addon (pk3-mugshot/ -> dist/FPB_CheekyMug.pk3).

Replaces the status-bar face with a small pair of cheeks that reacts the way
the face does: looks around at rest, bruises as you take damage, clenches when
you rampage, smirks at new toys, glows when invulnerable, deflates when dead.
The engine picks frames by lump name, so all we do is ship same-named art.

Ships separately so it's one launch-line edit to revert."""

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

import generate_sprites as G

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "pk3-mugshot" / "graphics"

W, H = 24, 30

# skin tones per pain level 0 (fresh) .. 4 (tenderized)
def tone(p):
    t = p / 4.0
    base = (int(232 - 60 * t), int(180 - 90 * t), int(140 - 80 * t), 255)
    shade = (int(198 - 60 * t), int(142 - 80 * t), int(102 - 60 * t), 255)
    line = (int(122 - 30 * t), int(69 - 25 * t), int(38 - 10 * t), 255)
    return base, shade, line


def mug(p=0, wiggle=0, lean=0, squeeze=1.0, lift=(0, 0), skin_override=None):
    img, d = ImageDraw.Draw, None
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    base, shade, line = tone(p) if skin_override is None else skin_override
    cw = int(11 * squeeze)
    ch = 16 if squeeze >= 1.0 else 18
    top = 7
    lx = 6 + lean
    rx = 18 + lean
    d.ellipse([lx - cw // 2, top - lift[0], lx + cw // 2, top + ch - lift[0]],
              fill=base, outline=line, width=1)
    d.ellipse([rx - cw // 2, top - lift[1], rx + cw // 2, top + ch - lift[1]],
              fill=base, outline=line, width=1)
    d.ellipse([lx - 3, top + ch - 7, lx + 3, top + ch - 2 - lift[0]], fill=shade)
    d.ellipse([rx - 3, top + ch - 7, rx + 3, top + ch - 2 - lift[1]], fill=shade)
    cx = 12 + wiggle + lean
    d.line([cx, top + 4, cx, top + ch + 2], fill=line, width=2)
    # highlight
    d.ellipse([lx - 3, top + 1, lx, top + 4], fill=(248, 214, 180, 255))
    # sweat scales with pain
    for i in range(p):
        sx = 2 + (i * 5) % 20
        d.line([sx, 1 + (i % 2), sx, 4 + (i % 2)], fill=(150, 200, 240, 255),
               width=1)
    return img, d, line


def star(d, cx, cy, color=(255, 240, 160, 255)):
    for a in range(0, 360, 45):
        r = math.radians(a)
        d.line([cx, cy, cx + 4 * math.cos(r), cy + 4 * math.sin(r)],
               fill=color, width=1)


def save(img, name):
    G.save(img, OUT, name, 0, 0)


def main():
    for p in range(5):
        for i, wig in enumerate((0, -1, 1)):        # idle looking around
            img, d, _ = mug(p, wiggle=wig)
            save(img, f"STFST{p}{i}")
        img, d, _ = mug(p, lean=3)                  # turn right
        save(img, f"STFTR{p}0")
        img, d, _ = mug(p, lean=-3)                 # turn left
        save(img, f"STFTL{p}0")
        img, d, _ = mug(p, squeeze=0.8)             # ouch: full pucker
        star(d, 4, 5)
        star(d, 20, 6)
        save(img, f"STFOUCH{p}")
        img, d, _ = mug(p, lift=(0, 3))             # evil grin: smug half-lift
        d.arc([8, 2, 16, 8], start=200, end=340, fill=(120, 200, 90, 255),
              width=1)
        save(img, f"STFEVL{p}")
        img, d, line = mug(p, squeeze=0.85)         # rampage clench
        for a in (-40, -15, 15, 40):
            r = math.radians(a - 90)
            d.line([12 + 6 * math.cos(r), 12 + 4 * math.sin(r),
                    12 + 10 * math.cos(r), 12 + 8 * math.sin(r)],
                   fill=line, width=1)
        save(img, f"STFKILL{p}")

    gold = ((236, 196, 80, 255), (190, 145, 40, 255), (130, 95, 20, 255))
    img, d, _ = mug(0, skin_override=gold)          # invulnerable
    star(d, 3, 4, (255, 255, 255, 255))
    star(d, 21, 25, (255, 255, 255, 255))
    save(img, "STFGOD0")

    gray = ((150, 145, 140, 255), (110, 106, 102, 255), (70, 66, 62, 255))
    img, d, _ = mug(4, squeeze=1.15, skin_override=gray)   # deflated
    d.line([4, 26, 20, 26], fill=(70, 66, 62, 255), width=2)
    save(img, "STFDEAD0")

    print("Cheeky Mug addon graphics written to", OUT)


if __name__ == "__main__":
    main()
