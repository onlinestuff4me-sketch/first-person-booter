#!/usr/bin/env python3
"""Static sanity checks for the pk3 tree. Not a ZScript compiler — GZDoom is
the final arbiter — but this catches the usual breakage after asset swaps:
missing sprite frames, sounds referenced but never defined, class name typos,
unbalanced braces, PNGs missing their grAb offsets. Exits nonzero on failure."""

import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PK3 = ROOT / "pk3"

# Engine-provided things we reference but don't define.
ENGINE_CLASSES = {
    "actor", "ammo", "weapon", "custominventory", "doomplayer", "eventhandler",
    "shotgun", "supershotgun", "chaingun", "rocketlauncher", "plasmarifle",
    "bfg9000", "chainsaw", "berserk", "clip", "shell", "rocketammo", "cell",
    "clipbox", "shellbox", "rocketbox", "cellpack",
}
ENGINE_SOUNDS = {"misc/i_pkup", "world/quake"}
INTERNAL_SPRITES = {"TNT1"}

errors = []
warns = []


def err(msg):
    errors.append(msg)


def zscript_files():
    return sorted(PK3.rglob("*.zs"))


def strip_comments(text):
    text = re.sub(r"//[^\n]*", "", text)
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def check_braces():
    for f in zscript_files():
        t = strip_comments(f.read_text())
        t_nostr = re.sub(r'"[^"]*"', '""', t)
        for ch, name in (("{}", "braces"), ("()", "parens")):
            bal = t_nostr.count(ch[0]) - t_nostr.count(ch[1])
            if bal != 0:
                err(f"{f.name}: unbalanced {name} ({bal:+d})")


def collect_classes():
    defined = {}
    for f in zscript_files():
        t = strip_comments(f.read_text())
        for m in re.finditer(r"\bclass\s+(\w+)\s*:\s*(\w+)(?:\s+replaces\s+(\w+))?", t):
            defined[m.group(1).lower()] = f.name
    return defined


def collect_refs():
    """Class names referenced as strings in spawn/give/fire/etc calls and props."""
    pat = re.compile(
        r'(?:Spawn|A_FireProjectile|A_GiveInventory|A_SelectWeapon|A_TakeInventory)'
        r'\s*\(\s*"(\w+)"'
        r'|(?:StartItem|WeaponSlot\s+\d+\s*,|AmmoType2?|PlayerClasses\s*=|'
        r'AddEventHandlers\s*=)\s*"(\w+)"'
        r'|A_Blast\s*\([^)]*?"(\w+)"')
    refs = set()
    files = zscript_files() + [PK3 / "mapinfo.txt"]
    for f in files:
        t = strip_comments(f.read_text())
        for m in pat.finditer(t):
            refs.add(next(g for g in m.groups() if g).lower())
    return refs


def collect_sprites_used():
    used = set()  # (SPR4, frameletter)
    state_pat = re.compile(r"^\s*([A-Z0-9\[\]\\]{4})\s+([A-Z\[\]\\]+)\s+-?\d+", re.M)
    for f in zscript_files():
        t = strip_comments(f.read_text())
        for m in state_pat.finditer(t):
            spr, frames = m.group(1), m.group(2)
            for fr in frames:
                used.add((spr, fr))
    for m in re.finditer(r'Inventory\.Icon\s+"(\w{4})(\w)0?"',
                         "\n".join(f.read_text() for f in zscript_files())):
        used.add((m.group(1).upper(), m.group(2).upper()))
    return used


def check_sprites():
    have = {p.stem.upper() for p in (PK3 / "sprites").glob("*.png")}
    for spr, fr in sorted(collect_sprites_used()):
        if spr in INTERNAL_SPRITES:
            continue
        lump = f"{spr}{fr}0"
        if lump not in have:
            err(f"missing sprite lump sprites/{lump}.png")


def check_sounds():
    snd_text = strip_comments((PK3 / "sndinfo.txt").read_text())
    defined = {}
    for line in snd_text.splitlines():
        line = line.strip()
        if not line or line.startswith("$"):
            continue
        parts = line.split()
        if len(parts) >= 2 and "/" in parts[0]:
            defined[parts[0]] = parts[1]
    for m in re.finditer(r"\$random\s+(\S+)", snd_text):
        defined[m.group(1)] = None

    have_wavs = {p.stem.upper() for p in (PK3 / "sounds").glob("*.wav")}
    for logical, lump in defined.items():
        if lump and lump.upper() not in have_wavs:
            err(f"SNDINFO '{logical}' points at missing sounds/{lump}.wav")

    used = set()
    body = "\n".join(strip_comments(f.read_text()) for f in zscript_files())
    for m in re.finditer(r'A_StartSound\s*\(\s*"([^"]+)"', body):
        used.add(m.group(1))
    for m in re.finditer(r'(?:SeeSound|DeathSound|BounceSound|PickupSound|AttackSound)'
                         r'\s+"([^"]+)"', body):
        used.add(m.group(1))
    for s in sorted(used):
        if s not in defined and s not in ENGINE_SOUNDS:
            err(f"sound '{s}' used but not in SNDINFO")


def check_classes():
    defined = collect_classes()
    for ref in sorted(collect_refs()):
        if ref not in defined and ref not in ENGINE_CLASSES:
            err(f"class '{ref}' referenced but never defined")


def check_grab():
    for p in sorted((PK3 / "sprites").glob("*.png")) + \
             sorted((PK3 / "graphics").glob("*.png")):
        data = p.read_bytes()
        if b"grAb" not in data[:64]:
            err(f"{p.name}: no grAb offset chunk (sprite will be misaligned)")
        else:
            i = data.index(b"grAb") + 4
            x, y = struct.unpack(">ii", data[i:i + 8])
            if abs(x) > 400 or abs(y) > 400:
                err(f"{p.name}: implausible offsets ({x},{y})")


def check_decals():
    text = strip_comments((PK3 / "decaldef.txt").read_text())
    have = {p.stem.upper() for p in (PK3 / "graphics").glob("*.png")}
    for m in re.finditer(r"\bpic\s+(\w+)", text):
        if m.group(1).upper() not in have:
            err(f"DECALDEF pic {m.group(1)} missing from graphics/")


if __name__ == "__main__":
    check_braces()
    check_classes()
    check_sprites()
    check_sounds()
    check_grab()
    check_decals()
    if errors:
        print("FAILED:")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)
    print("All consistency checks passed.")
