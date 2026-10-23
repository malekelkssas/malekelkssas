#!/usr/bin/env python3
"""Recolour a Platane/snk SVG: the board and the snake take a mix of colours.

Usage: snake-mix.py <in.svg> <out.svg> <empty> <stop1,stop2,...> [across|levels]

across  the board runs through the stops from the first week to the last; a cell's level sets
        how far it goes from the empty colour to its column's colour. The snake takes the stops
        from head to tail.
levels  each contribution level gets one stop (level 1 the first stop ... level 4 the last).
"""
import re
import sys

LEVEL_MIX = {1: 0.5, 2: 0.68, 3: 0.86, 4: 1.0}


def rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def hexc(c):
    return "#" + "".join(f"{round(max(0, min(255, v))):02x}" for v in c)


def lerp(a, b, t):
    return [x + (y - x) * t for x, y in zip(a, b)]


def along(stops, t):
    if len(stops) == 1:
        return stops[0]
    pos = t * (len(stops) - 1)
    i = min(int(pos), len(stops) - 2)
    return lerp(stops[i], stops[i + 1], pos - i)


def main():
    src, dst, empty, stops = sys.argv[1:5]
    mode = sys.argv[5] if len(sys.argv) > 5 else "across"
    empty_c, stops_c = rgb(empty), [rgb(s) for s in stops.split(",")]
    svg = open(src).read()

    cells = {m[0]: float(m[1]) for m in re.findall(r'<rect class="c (c[0-9a-z]+)" x="([\d.]+)"', svg)}
    xs = [float(x) for x in re.findall(r'<rect class="c[^"]*" x="([\d.]+)"', svg)]
    lo, hi = min(xs), max(xs)

    def colour(cls, level):
        if mode == "levels":
            base = stops_c[min(level, len(stops_c)) - 1]
            return hexc(base)
        t = (cells[cls] - lo) / ((hi - lo) or 1)
        return hexc(lerp(empty_c, along(stops_c, t), LEVEL_MIX.get(level, 1.0)))

    def fix(m):
        cls, body = m.group(1), m.group(2)
        lvl = re.search(r"var\(--c([1-4])\)", body)
        if not lvl or cls not in cells:
            return m.group(0)
        return m.group(0).replace(f"var(--c{lvl.group(1)})", colour(cls, int(lvl.group(1))))

    # the cell's own rule and its keyframes both carry its level colour
    svg = re.sub(r"\.c\.(c[0-9a-z]+)(\{[^}]*\})", fix, svg)
    svg = re.sub(r"@keyframes (c[0-9a-z]+)(\{[^}]*\})", fix, svg)

    segs = sorted(set(re.findall(r'<rect class="s (s\d+)"', svg)), key=lambda s: int(s[1:]))
    css = "".join(f".s.{s}{{fill:{hexc(along(stops_c, i / max(1, len(segs) - 1)))}}}" for i, s in enumerate(segs))
    svg = svg.replace("</style>", css + "</style>", 1)
    open(dst, "w").write(svg)


if __name__ == "__main__":
    main()
