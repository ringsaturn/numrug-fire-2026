"""slider/s2swir_ignition_{a,b}.jpg: the published ignition slider pair with the OSM 2026-10-25 overlay added.

The 10-10 Sentinel-2B window behind the published "after" image is no longer on disk, so the overlay is drawn on
the published JPGs themselves (data/s2/slider/, the files served at blog-assets …/slider/, md5 f35efbb7… and
8aa3d05b…). Their pixel grid is the 10 m grid of the ignition box 119.28-119.52°E, 46.78-46.97°N, resized to
1732 x 2000. One pair serves every language, so the overlay carries symbols, letters and a distance only:
OSM roads (white), the end of the nearest track (white square), a dashed cyan line from it to the ignition point
with its length, a magenta bracket beside each Sentinel-2 linear feature A/B/C (the feature itself left
uncovered) and the ignition point (cyan star).
"""

import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from common import D, lang
from figkit import osm, paths

lang.init(__file__, fonts=False)
NAME = "s2swir_ignition"
SRC = D("slider")
OUT = paths.OUT / "slider"
MAXKB = 600
FONT = os.path.join(os.path.dirname(__import__("matplotlib").__file__), "mpl-data/fonts/ttf/DejaVuSans-Bold.ttf")


def extent():
    """Pixel-edge extent of the 10 m ignition grid, as the slider script cut it."""
    l0, l1, b0, b1 = 119.28, 119.52, 46.78, 46.97
    dx = 10 / (111320 * math.cos(math.radians((b0 + b1) / 2)))
    dy = 10 / 110950
    w, h = int(round((l1 - l0) / dx)), int(round((b1 - b0) / dy))
    i1 = min(w, int(math.ceil((l1 - l0) / dx)))
    j1 = min(h, int(math.ceil((b1 - b0) / dy)))
    return (l0, l0 + i1 * dx, b1 - j1 * dy, b1)


EXT = extent()


def px(size, lon, lat):
    return ((lon - EXT[0]) / (EXT[1] - EXT[0]) * size[0], (EXT[3] - lat) / (EXT[3] - EXT[2]) * size[1])


def dashed(d, a, b, on, off, width, fill):
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    t = 0.0
    while t < L:
        u, v = t / L, min(t + on, L) / L
        d.line([(a[0] + u * (b[0] - a[0]), a[1] + u * (b[1] - a[1])), (a[0] + v * (b[0] - a[0]), a[1] + v * (b[1] - a[1]))],
               fill=fill, width=width)
        t += on + off


def halo_text(d, xy, s, font, fill, anchor, r=3):
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            if dx or dy:
                d.text((xy[0] + dx, xy[1] + dy), s, font=font, fill=(0, 0, 0), anchor=anchor)
    d.text(xy, s, font=font, fill=fill, anchor=anchor)


def star(cx, cy, R, r):
    pts = []
    for k in range(10):
        a = math.radians(-90 + 36 * k)
        rr = R if k % 2 == 0 else r
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


# Side of each feature its bracket and letter go on, as a unit vector in image pixels (y down): A runs W-E and
# gets its bracket above it, B and C run N-S and get theirs on the west.
SIDE = {"s2-line-a": (0, -1), "s2-line-b": (-1, 0), "s2-line-c": (-1, 0)}


def overlay(im):
    W, H = im.size
    d = ImageDraw.Draw(im)
    lw = max(3, int(W / 450))
    f = ImageFont.truetype(FONT, int(W / 48))
    box = EXT
    for w in osm.load()["roads"]:
        if w["hw"] not in ("unclassified", "track"):
            continue
        if not any(box[0] <= x <= box[1] and box[2] <= y <= box[3] for x, y in w["c"]):
            continue
        pts = [px(im.size, x, y) for x, y in w["c"]]
        d.line(pts, fill=(0, 0, 0), width=lw + 3, joint="curve")
        d.line(pts, fill=(255, 255, 255), width=lw, joint="curve")
    a, b = px(im.size, *osm.PLACES["track_end"]), px(im.size, *osm.IGNITION)
    dashed(d, a, b, 6 * lw, 4 * lw, lw + 3, (0, 0, 0))
    dashed(d, a, b, 6 * lw, 4 * lw, lw, (0, 255, 255))
    from pyproj import Geod

    km = Geod(ellps="WGS84").inv(*osm.PLACES["track_end"], *osm.IGNITION)[2] / 1000
    halo_text(d, ((a[0] + b[0]) / 2 + 3 * lw, (a[1] + b[1]) / 2), f"{km:.1f} km", f, (255, 255, 255), "lm")
    s = 5 * lw
    d.rectangle([a[0] - s, a[1] - s, a[0] + s, a[1] + s], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
    for k, c in sorted(osm.load()["s2_lines"].items()):
        # a bracket beside each feature (not on it), so the feature itself stays visible under the slider
        pts = [px(im.size, x, y) for x, y in c]
        (x0, y0), (x1, y1) = pts[0], pts[-1]
        nx, ny = SIDE[k]
        g = 9 * lw
        br = [(x0 + nx * g / 3, y0 + ny * g / 3), (x0 + nx * g, y0 + ny * g), (x1 + nx * g, y1 + ny * g),
              (x1 + nx * g / 3, y1 + ny * g / 3)]
        d.line(br, fill=(0, 0, 0), width=lw + 4, joint="curve")
        d.line(br, fill=(255, 61, 245), width=lw + 1, joint="curve")
        mx, my = (x0 + x1) / 2 + nx * (g + 4 * lw), (y0 + y1) / 2 + ny * (g + 4 * lw)
        anchor = ("r" if nx < -0.5 else "l" if nx > 0.5 else "m") + ("b" if ny < -0.5 else "t" if ny > 0.5 else "m")
        halo_text(d, (mx, my), k[-1].upper(), f, (255, 61, 245), anchor)
    st = star(*b, 11 * lw, 4.4 * lw)
    d.polygon(st, outline=(0, 0, 0), width=lw + 4)
    d.polygon(st, outline=(0, 255, 255), width=lw + 1)
    return km


OUT.mkdir(parents=True, exist_ok=True)
ims = []
for s in "ab":
    im = Image.open(SRC / f"{NAME}_{s}.jpg").convert("RGB")
    print(s, im.size, "extent", [round(v, 5) for v in EXT], "km %.2f" % overlay(im))
    ims.append(im)
for q in range(88, 69, -2):
    sizes = []
    for s, im in zip("ab", ims):
        p = OUT / f"{NAME}_{s}.jpg"
        im.save(p, "JPEG", quality=q, optimize=True, progressive=True)
        sizes.append(p.stat().st_size // 1024)
    if max(sizes) <= MAXKB:
        break
print("quality", q, "KB", sizes, OUT)
