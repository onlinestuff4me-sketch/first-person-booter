#!/usr/bin/env python3
"""Pack pk3/ into dist/FirstPersonBooter.pk3 (a pk3 is just a zip).
Optionally regenerate assets first:  python3 tools/build.py --regen"""

import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PK3_DIR = ROOT / "pk3"
DIST = ROOT / "dist" / "FirstPersonBooter.pk3"


def main():
    if "--regen" in sys.argv:
        for script in ("generate_sprites.py", "generate_sounds.py"):
            subprocess.run([sys.executable, str(ROOT / "tools" / script)],
                           check=True)

    DIST.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in PK3_DIR.rglob("*") if p.is_file())
    with zipfile.ZipFile(DIST, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, p.relative_to(PK3_DIR).as_posix())
    size = DIST.stat().st_size
    print(f"Wrote {DIST.relative_to(ROOT)} ({size/1024:.0f} KiB, {len(files)} lumps)")


if __name__ == "__main__":
    main()
