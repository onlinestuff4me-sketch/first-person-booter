#!/usr/bin/env python3
"""Pack pk3/ into dist/FirstPersonBooter.pk3 and, if present, pk3-mugshot/
into dist/FPB_CheekyMug.pk3 (a pk3 is just a zip).
Optionally regenerate all assets first:  python3 tools/build.py --regen"""

import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

GEN_SCRIPTS = ("generate_sprites.py", "generate_sounds.py",
               "generate_mugshot.py", "build_map.py")

TARGETS = (
    (ROOT / "pk3", ROOT / "dist" / "FirstPersonBooter.pk3"),
    (ROOT / "pk3-mugshot", ROOT / "dist" / "FPB_CheekyMug.pk3"),
)


def pack(src, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in src.rglob("*") if p.is_file())
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, p.relative_to(src).as_posix())
    size = dest.stat().st_size
    print(f"Wrote {dest.relative_to(ROOT)} ({size/1024:.0f} KiB, "
          f"{len(files)} lumps)")


def main():
    if "--regen" in sys.argv:
        for script in GEN_SCRIPTS:
            subprocess.run([sys.executable, str(ROOT / "tools" / script)],
                           check=True)

    for src, dest in TARGETS:
        if src.exists():
            pack(src, dest)


if __name__ == "__main__":
    main()
