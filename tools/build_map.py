#!/usr/bin/env python3
"""Generate BUTTEST, "The Proving Rounds" — a small UDMF test arena packed as
pk3/maps/buttest.wad. Load the mod and run `map buttest` in the console.

Features under test:
  * a DESTRUCTIBLE wall (health via GZDoom destructible geometry) sealing a
    loot bunker on the north side — fart it (or kick it) until it gives way
  * a classic door on the west side for door-fart practice
  * monsters, barrels, and one of every pickup on the north shelf
  * an exit switch on the east wall

Geometry is authored right here; regenerate after tweaking."""

import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "pk3" / "maps" / "buttest.wad"

# ---------------------------------------------------------------- builders --

verts = {}
vlist = []
sides = []
lines = []
sectors = []
things = []


def V(x, y):
    key = (x, y)
    if key not in verts:
        verts[key] = len(vlist)
        vlist.append(key)
    return verts[key]


def SD(sector, mid=None, top=None, bot=None):
    sides.append({"sector": sector, "mid": mid, "top": top, "bot": bot})
    return len(sides) - 1


def L(p1, p2, front, back=None, **props):
    lines.append({"v1": V(*p1), "v2": V(*p2), "front": front, "back": back,
                  "props": props})


def SEC(hfloor, hceil, floor, ceil, light, tag=0):
    sectors.append({"hf": hfloor, "hc": hceil, "tf": floor, "tc": ceil,
                    "light": light, "tag": tag})
    return len(sectors) - 1


def T(x, y, angle, ttype):
    things.append((x, y, angle, ttype))


# ------------------------------------------------------------ the geometry --

ARENA = SEC(0, 192, "FLOOR4_8", "CEIL3_5", 176)
STRIP = SEC(0, 0, "FLAT1", "FLAT1", 176, tag=7)     # the destructible wall
BUNKER = SEC(0, 160, "FLOOR0_1", "FLAT1", 144)
DOOR = SEC(0, 0, "FLAT1", "FLAT1", 176)             # classic door
ALCOVE = SEC(0, 128, "FLOOR0_1", "FLAT1", 128)
LANE = SEC(0, 176, "FLOOR0_1", "CEIL3_5", 150)      # the bowling lane
NSTRIP = SEC(0, 0, "FLAT1", "FLAT1", 150, tag=8)    # pro-shop breakable wall
NOOK = SEC(0, 128, "FLOOR0_1", "FLAT1", 136)        # the pro shop

WALL = "STARTAN2"
DOORFACE = "BIGDOOR2"
BREAKABLE = dict(special=11, arg0=7, arg1=64, health=90, healthgroup=7,
                 deathspecial=True)                  # Door_Open the strip
BREAKABLE2 = dict(special=11, arg0=8, arg1=64, health=90, healthgroup=8,
                  deathspecial=True)                 # pro-shop wall
USEDOOR = dict(special=12, arg0=0, arg1=16, arg2=150,
               playeruse=True, repeatspecial=True)   # Door_Raise behind line

# Arena boundary, clockwise so front sides face inward.
L((0, 0), (0, 384), SD(ARENA, mid=WALL), blocking=True)
L((0, 384), (0, 640), SD(ARENA, top=DOORFACE), SD(DOOR), twosided=True,
  **USEDOOR)
L((0, 640), (0, 1024), SD(ARENA, mid=WALL), blocking=True)
L((0, 1024), (1152, 1024), SD(ARENA, mid=WALL), blocking=True)
L((1152, 1024), (1536, 1024), SD(ARENA, top=DOORFACE), SD(STRIP),
  twosided=True, **BREAKABLE)
L((1536, 1024), (1536, 576), SD(ARENA, mid=WALL), blocking=True)
L((1536, 576), (1536, 448), SD(ARENA, mid="SW1COMP"), blocking=True,
  special=243, playeruse=True)                       # Exit_Normal
L((1536, 448), (1536, 0), SD(ARENA, mid=WALL), blocking=True)
L((1536, 0), (896, 0), SD(ARENA, mid=WALL), blocking=True)
L((896, 0), (640, 0), SD(ARENA, top=WALL), SD(LANE), twosided=True)
L((640, 0), (0, 0), SD(ARENA, mid=WALL), blocking=True)

# The bowling lane: punt a demon south, through the pins. Mind the gutters.
L((640, -704), (640, 0), SD(LANE, mid=WALL), blocking=True)
L((896, -704), (640, -704), SD(LANE, mid=WALL), blocking=True)
L((896, 0), (896, -240), SD(LANE, mid=WALL), blocking=True)
L((896, -240), (896, -400), SD(LANE, top=DOORFACE), SD(NSTRIP),
  twosided=True, **BREAKABLE2)
L((896, -400), (896, -704), SD(LANE, mid=WALL), blocking=True)

# The pro shop: a cracked wall off the lane hiding the good stuff.
L((896, -240), (912, -240), SD(NSTRIP, mid=WALL), blocking=True)
L((912, -240), (912, -400), SD(NSTRIP), SD(NOOK, top=DOORFACE),
  twosided=True, **BREAKABLE2)
L((912, -400), (896, -400), SD(NSTRIP, mid=WALL), blocking=True)
L((912, -240), (1072, -240), SD(NOOK, mid=WALL), blocking=True)
L((1072, -240), (1072, -400), SD(NOOK, mid=WALL), blocking=True)
L((1072, -400), (912, -400), SD(NOOK, mid=WALL), blocking=True)

# Destructible strip's own edges (visible once it opens).
L((1152, 1024), (1152, 1040), SD(STRIP, mid=WALL), blocking=True)
L((1152, 1040), (1536, 1040), SD(STRIP), SD(BUNKER, top=DOORFACE),
  twosided=True, **BREAKABLE)
L((1536, 1040), (1536, 1024), SD(STRIP, mid=WALL), blocking=True)

# Bunker walls.
L((1152, 1040), (1152, 1296), SD(BUNKER, mid=WALL), blocking=True)
L((1152, 1296), (1536, 1296), SD(BUNKER, mid=WALL), blocking=True)
L((1536, 1296), (1536, 1040), SD(BUNKER, mid=WALL), blocking=True)

# Door strip rails and the alcove-side door line.
L((0, 384), (-16, 384), SD(DOOR, mid="DOORTRAK"), blocking=True)
L((-16, 640), (0, 640), SD(DOOR, mid="DOORTRAK"), blocking=True)
L((-16, 640), (-16, 384), SD(ALCOVE, top=DOORFACE), SD(DOOR), twosided=True,
  **USEDOOR)

# Alcove walls.
L((-16, 384), (-272, 384), SD(ALCOVE, mid=WALL), blocking=True)
L((-272, 384), (-272, 640), SD(ALCOVE, mid=WALL), blocking=True)
L((-272, 640), (-16, 640), SD(ALCOVE, mid=WALL), blocking=True)

# Two pillars (void squares, wound so fronts face the arena).
for x0, y0 in ((384, 384), (1088, 576)):
    x1, y1 = x0 + 64, y0 + 64
    L((x0, y1), (x0, y0), SD(ARENA, mid=WALL), blocking=True)
    L((x0, y0), (x1, y0), SD(ARENA, mid=WALL), blocking=True)
    L((x1, y0), (x1, y1), SD(ARENA, mid=WALL), blocking=True)
    L((x1, y1), (x0, y1), SD(ARENA, mid=WALL), blocking=True)

# ---------------------------------------------------------------- the cast --

T(192, 128, 45, 1)          # player 1 start
for x, y, a, t in [
    (768, 512, 180, 3004), (900, 640, 225, 3004), (1100, 860, 200, 3004),
    (640, 760, 270, 9),                                   # shotgun guy
    (1024, 320, 90, 3001), (1216, 512, 180, 3001),        # imps
    (400, 820, 315, 3002),                                # demon
]:
    T(x, y, a, t)
for x, y in ((760, 440), (800, 470), (730, 472)):
    T(x, y, 0, 2035)        # barrels
# the pickup shelf (all get replaced by the mod's versions)
for x, t in ((480, 2007), (540, 2008), (620, 2001), (700, 2023),
             (780, 2047), (860, 17)):
    T(x, 960, 270, t)
# bunker loot
T(1344, 1200, 270, 2013)    # soulsphere
T(1280, 1160, 270, 8)       # backpack
T(1408, 1160, 270, 17)      # cell pack
# alcove loot
T(-144, 512, 0, 2005)       # chainsaw spot -> cheeks
T(-208, 460, 0, 2012)       # medikit
# spare beans mid-arena
T(1000, 700, 0, 2007)
T(1060, 700, 0, 2007)
# the bowling lane: gutter barrels, one ball-return demon, four zombie pins
for y in (-160, -352, -544):
    T(700, y, 0, 2035)
    T(836, y, 0, 2035)
T(768, -420, 90, 3002)      # the demon (your ball, technically)
for x, y in ((768, -592), (732, -644), (804, -644), (768, -676)):
    T(x, y, 90, 3004)       # the pins
T(700, -64, 90, 2007)
T(836, -64, 90, 2007)
# pro-shop loot, behind the cracked wall
T(960, -320, 180, 83)       # megasphere
T(1024, -320, 180, 2047)    # cells -> chili
T(1024, -272, 180, 2007)    # clip -> beans


# ------------------------------------------------------------------- emit --

def fmt_props(props):
    out = []
    for k, v in props.items():
        if v is True:
            out.append(f"{k}=true;")
        elif v is not False and v is not None:
            out.append(f"{k}={v};")
    return "".join(out)


def build_textmap():
    o = ['namespace="zdoom";']
    for x, y, angle, ttype in things:
        o.append(f'thing{{x={x};y={y};angle={angle};type={ttype};'
                 'skill1=true;skill2=true;skill3=true;skill4=true;'
                 'skill5=true;single=true;coop=true;dm=true;}')
    for x, y in vlist:
        o.append(f"vertex{{x={x};y={y};}}")
    for ln in lines:
        props = fmt_props(ln["props"])
        back = f'sideback={ln["back"]};' if ln["back"] is not None else ""
        o.append(f'linedef{{v1={ln["v1"]};v2={ln["v2"]};'
                 f'sidefront={ln["front"]};{back}{props}}}')
    for sd in sides:
        tex = ""
        if sd["mid"]:
            tex += f'texturemiddle="{sd["mid"]}";'
        if sd["top"]:
            tex += f'texturetop="{sd["top"]}";'
        if sd["bot"]:
            tex += f'texturebottom="{sd["bot"]}";'
        o.append(f'sidedef{{sector={sd["sector"]};{tex}}}')
    for s in sectors:
        tag = f'id={s["tag"]};' if s["tag"] else ""
        o.append(f'sector{{heightfloor={s["hf"]};heightceiling={s["hc"]};'
                 f'texturefloor="{s["tf"]}";textureceiling="{s["tc"]}";'
                 f'lightlevel={s["light"]};{tag}}}')
    return "\n".join(o) + "\n"


def write_wad(path, lumps):
    body = b""
    directory = []
    offset = 12
    for name, data in lumps:
        directory.append((offset, len(data), name))
        body += data
        offset += len(data)
    header = b"PWAD" + struct.pack("<II", len(lumps), offset)
    dirdata = b"".join(
        struct.pack("<II", off, ln) + nm.encode("ascii").ljust(8, b"\0")
        for off, ln, nm in directory)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + body + dirdata)


if __name__ == "__main__":
    textmap = build_textmap()
    write_wad(OUT, [("BUTTEST", b""), ("TEXTMAP", textmap.encode("ascii")),
                    ("ENDMAP", b"")])
    print(f"wrote {OUT.relative_to(ROOT)} "
          f"({len(vlist)} verts, {len(lines)} lines, {len(sectors)} sectors, "
          f"{len(things)} things)")
