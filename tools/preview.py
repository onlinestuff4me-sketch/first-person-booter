#!/usr/bin/env python3
"""Render docs/preview.png — a labeled contact sheet of the current sprites.
Re-run after swapping art to eyeball everything in one place."""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SPR = ROOT / "pk3" / "sprites"
OUT = ROOT / "docs" / "preview.png"

ROWS = [
    ("The Boot (HUD)", ["BOOTA0", "BOOTB0", "BOOTC0", "BOOTD0"], 0.45),
    ("Cheeks of Doom (HUD)", ["BUTTA0", "BUTTB0", "BUTTC0", "BUTTD0"], 0.6),
    ("Gas cloud / stink cloud", ["FARTA0", "FARTB0", "FARTC0",
                                 "PGASA0", "PGASC0"], 0.8),
    ("Blast ring / kick puff", ["FBLSA0", "FBLSB0", "FBLSC0",
                                "KPUFA0", "KPUFB0"], 0.7),
    ("Gore & goo", ["GIBSA0", "GIBSB0", "GIBSE0", "GOOPA0", "GOOPC0"], 1.0),
    ("Pickups", ["BUPKA0", "BEANA0", "CHLIA0", "MBNSA0"], 1.6),
]


def main():
    pad, label_h = 14, 22
    row_imgs = []
    for title, names, zoom in ROWS:
        imgs = []
        for n in names:
            p = SPR / f"{n}.png"
            if not p.exists():
                continue
            im = Image.open(p).convert("RGBA")
            im = im.resize((max(1, int(im.width * zoom)),
                            max(1, int(im.height * zoom))), Image.NEAREST)
            imgs.append((n, im))
        w = sum(im.width for _, im in imgs) + pad * (len(imgs) + 1)
        h = max(im.height for _, im in imgs) + pad * 2 + label_h
        row = Image.new("RGBA", (w, h), (34, 30, 38, 255))
        d = ImageDraw.Draw(row)
        d.text((pad, 6), title, fill=(235, 225, 200, 255))
        x = pad
        for n, im in imgs:
            row.alpha_composite(im, (x, label_h + pad))
            x += im.width + pad
        row_imgs.append(row)

    W = max(r.width for r in row_imgs)
    H = sum(r.height for r in row_imgs)
    sheet = Image.new("RGBA", (W, H), (34, 30, 38, 255))
    y = 0
    for r in row_imgs:
        sheet.alpha_composite(r, (0, y))
        y += r.height
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(OUT)
    print(f"wrote {OUT.relative_to(ROOT)} ({sheet.width}x{sheet.height})")


if __name__ == "__main__":
    main()
