"""Shared helpers of the ahi group: data paths, borders, map decoration, the frame range of
each published update, and the output-size fix for bbox-tight figures."""

import json
import logging
from pathlib import Path

import matplotlib
import numpy as np
import shapefile

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402,F401
from matplotlib.ticker import FuncFormatter  # noqa: E402

from figkit import lang, paths  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

GROUP_DIR = Path(__file__).resolve().parents[1]
DATA = paths.data("ahi")
DATA.mkdir(parents=True, exist_ok=True)
RAW = DATA / "raw"
VIIRS_L2 = DATA / "viirs_l2"
CROP = DATA / "ahi_b07_b14_crop.npz"
MASK = DATA / "ahi_hotmask.npz"
HOTSPOTS = DATA / "ahi_hotspots_10min.csv"
VIIRS_BOX = DATA / "viirs_box.csv"
NE = DATA / "ne" / "ne_10m_admin_0_boundary_lines_land.shp"
OSM = GROUP_DIR / "snapshot" / "border_osm.json"

ARXAN = (119.944, 47.177)
# Detection box (lat 46.3-47.8 N, lon 118.4-120.4 E)
BOX = dict(lat=(46.3, 47.8), lon=(118.4, 120.4))

# First and last frame (UTC tag) of each update's crop, so a figure sees the same frames as published:
# r1 = update 1 (to 10-12 04:40Z), r2/r3/r5 = updates 2, 3 and 5.
ROUNDS = {
    "r1": ("20261007_1800", "20261012_0440"),
    "r2": ("20261012_0300", "20261012_1140"),
    "r3": ("20261012_1050", "20261013_0510"),
    "r5": ("20261013_0430", "20261013_1400"),
}


def round_sel(tags, r):
    a, b = ROUNDS[r]
    t = np.array([str(x) for x in tags])
    return np.nonzero((t >= a) & (t <= b))[0]


def border_lines(box=(117, 45, 122, 49)):
    """Natural Earth 10m land boundaries crossing the box."""
    out = []
    for s in shapefile.Reader(str(NE)).shapes():
        x0, y0, x1, y1 = s.bbox
        if x1 < box[0] or x0 > box[2] or y1 < box[1] or y0 > box[3]:
            continue
        pts = np.array(s.points)
        parts = list(s.parts) + [len(pts)]
        for a, b in zip(parts[:-1], parts[1:]):
            out.append(pts[a:b])
    return out


def border_lines_osm(box=(117, 45, 122, 49)):
    """OSM admin_level=2 ways (snapshot/border_osm.json) with a point inside the box."""
    out = []
    for p in json.load(open(OSM)):
        p = np.array(p)
        if len(p) > 1 and ((p[:, 0] >= box[0]) & (p[:, 0] <= box[2]) & (p[:, 1] >= box[1]) & (p[:, 1] <= box[3])).any():
            out.append(p)
    return out


def decorate(ax, lines, xlim, ylim, label=True, color="k"):
    """Dashed border, Arxan star and label, limits and a latitude-corrected aspect."""
    for p in lines:
        ax.plot(p[:, 0], p[:, 1], color=color, lw=1.0, ls="--")
    ax.plot(*ARXAN, marker="*", ms=10, mfc="yellow", mec="k", zorder=6)
    # a yellow label on imagery also sits on bright cloud: a dark box keeps it readable
    box = (
        dict(fc="black", ec="none", alpha=0.55, pad=1)
        if color == "yellow"
        else dict(fc="white", ec="none", alpha=0.6, pad=1)
    )
    if label:
        ax.text(ARXAN[0] + 0.04, ARXAN[1] + 0.03, lang.T("map.arxan"), fontsize=9, color=color, zorder=6, bbox=box)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect(1 / np.cos(np.radians(np.mean(ylim))))


def date_formatter(fn):
    """Tick formatter for a matplotlib date axis holding local wall-clock times."""
    return FuncFormatter(lambda x, _: fn(mdates.num2date(x)))


def fix_size(path, W, H):
    """Trim or pad the white margins of a bbox_inches='tight' render to W x H px.

    The tight box differs by a few pixels between languages; trimming white columns
    (either side) and rows (bottom first) keeps every language at the published size.
    Aborts rather than cut into a non-white column or row.
    """
    from PIL import Image

    im = np.asarray(Image.open(path).convert("RGB"))
    h, w = im.shape[:2]

    def white(a):
        return a.size == 0 or (a >= 250).all()

    while w > W:
        if white(im[:, :1]):
            im = im[:, 1:]
        elif white(im[:, -1:]):
            im = im[:, :-1]
        else:
            raise SystemExit(f"{path}: no white column to trim")
        w -= 1
    while h > H:
        if white(im[-1:]):
            im = im[:-1]
        elif white(im[:1]):
            im = im[1:]
        else:
            raise SystemExit(f"{path}: no white row to trim")
        h -= 1
    out = np.full((H, W, 3), 255, np.uint8)
    out[:h, :w] = im
    Image.fromarray(out).save(path)
