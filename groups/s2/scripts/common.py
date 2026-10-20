"""Shared pieces of the s2 group: data paths, Sentinel-2 windows, borders, fire detections,
image stretches and the arrow-label helper. Figure scripts call ``lang.init(__file__)`` first."""

import csv
import datetime as dt
import json
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np

from figkit import lang, paths

G = "s2"
SNAP = paths.group_dir(G) / "snapshot"
ARXAN = (119.944, 47.177)  # Arxan city, as marked in the published figures


def D(*parts):
    """data/s2/<parts>."""
    return paths.data(G, *parts)


# Sentinel-2 overpasses (satellite, UTC) of the scenes the figures use.
SAT = {
    "2026-10-05": ("Sentinel-2C", "03:05"),
    "2026-10-08": ("Sentinel-2C", "03:15"),
    "2026-10-10": ("Sentinel-2B", "03:05"),
    "2026-10-13": ("Sentinel-2B", "03:15"),
    "2026-10-15": ("Sentinel-2C", "03:05"),
}

# Windows read from the Sentinel-2 COGs: name -> (lon0, lon1, lat0, lat1). "A" is the 40 m overview grid
# (fixed pixel size); the others are cut at a target resolution in metres (fetch_s2.py).
BOX = {
    "SE": (119.38, 119.66, 46.60, 46.80),
    "NW": (118.98, 119.22, 47.05, 47.22),
    "SPA": (119.40, 119.65, 47.20, 47.38),
    "IGN": (119.28, 119.52, 46.78, 46.97),
    "ZA": (119.28, 119.62, 46.54, 46.72),
    "ZB": (119.66, 119.90, 47.04, 47.22),
    "ZI": (119.46, 119.68, 47.02, 47.22),
}
OVERVIEW = (118.6, 120.1, 46.5, 47.6)


def load(d, g, bands=("red", "green", "blue", "nir08", "swir22", "scl")):
    return {b: np.load(D("s2", f"{d}_{g}_{b}.npy")) for b in bands}


def ext_of(g, d, res=10):
    """Extent (lon0, lon1, lat0, lat1) and pixel size in degrees of window g as fetched on date d."""
    l0, l1, b0, b1 = BOX[g]
    dx = res / (111320 * math.cos(math.radians((b0 + b1) / 2)))
    dy = res / 110950
    h, w = np.load(D("s2", f"{d}_{g}_red.npy"), mmap_mode="r").shape
    return (l0, l0 + w * dx, b1 - h * dy, b1), dx, dy


# Stretches of the published figures (reflectance x 10000, BOA offset already removed).
def st(x, lo, hi):
    return np.clip((x.astype("f4") / 10000 - lo) / (hi - lo), 0, 1)


def gamma(x, g=0.8):
    return x**g


def truecolor(X, hi=0.20):
    return gamma(np.dstack([st(X["red"], 0, hi), st(X["green"], 0, hi), st(X["blue"], 0, hi)]))


def swir(X):
    return gamma(np.dstack([st(X["swir22"], 0.02, 0.40), st(X["nir08"], 0.02, 0.38), st(X["red"], 0.01, 0.22)]), 0.75)


def nbr(X):
    n = X["nir08"].astype("f4")
    s = X["swir22"].astype("f4")
    return (n - s) / (n + s + 1e-6)


def aspect(e):
    return 1 / np.cos(np.radians((e[2] + e[3]) / 2))


def cloudmask(X):
    """Cloud and cloud shadow: SCL 8/9/10 or blue > 0.15, dilated 3 px, plus dark SCL-3 shadow (B12 < 0.08)."""
    from scipy import ndimage

    return ndimage.binary_dilation(np.isin(X["scl"], [8, 9, 10]) | (X["blue"] > 1500), iterations=3) | (
        (X["scl"] == 3) & (X["swir22"] < 800)
    )


_OSM = _NE = None


def osm():
    """OSM China–Mongolia border ways (lists of lon/lat pairs)."""
    global _OSM
    if _OSM is None:
        _OSM = json.load(open(D("border", "border_osm.json")))
    return _OSM


def ne():
    """Natural Earth 10m China–Mongolia boundary, clipped to the region."""
    global _NE
    if _NE is None:
        _NE = json.load(open(D("derived", "border_lines.json")))
    return _NE


def mongolia_mask(e, dx, dy, shape):
    """Pixels west of the merged OSM line (closed to 117.5°E) = Mongolian side; also returns pixel-centre lat/lon."""
    from matplotlib.path import Path
    from shapely.geometry import LineString
    from shapely.ops import linemerge, unary_union

    L = linemerge(unary_union([LineString(p) for p in osm() if len(p) > 1]))
    if L.geom_type != "LineString":
        L = max(L.geoms, key=lambda q: q.length)
    c = list(L.coords)
    poly = c + [(117.5, c[-1][1]), (117.5, c[0][1])]
    h, w = shape
    la = e[3] - (np.arange(h) + 0.5) * dy
    lo = e[0] + (np.arange(w) + 0.5) * dx
    X, Y = np.meshgrid(lo, la)
    return Path(poly).contains_points(np.c_[X.ravel(), Y.ravel()]).reshape(h, w), la, lo


# Map furniture


def borders_both(ax, lw=1.3):
    """OSM border as a yellow solid line and Natural Earth as a cyan dashed line."""
    for seg in osm():
        a = np.array(seg)
        ax.plot(a[:, 0], a[:, 1], color="yellow", lw=lw, ls="-")
    for seg in ne():
        a = np.array(seg)
        ax.plot(a[:, 0], a[:, 1], color="cyan", lw=lw * 0.8, ls="--")


def borders_osm(ax, lw=1.6):
    """OSM border alone, yellow dashed."""
    for seg in osm():
        a = np.array(seg)
        ax.plot(a[:, 0], a[:, 1], color="yellow", lw=lw, ls="--", dashes=(5, 3))


def town(ax, fs=10):
    ax.plot(*ARXAN, marker="s", ms=6, mfc="white", mec="black", zorder=5)
    ax.annotate(
        lang.T("s2.arxan"),
        ARXAN,
        xytext=(-5, 4),
        textcoords="offset points",
        ha="right",
        color="white",
        fontsize=fs,
        path_effects=[pe.withStroke(linewidth=2, foreground="black")],
    )


def fmt(ax, e, fs=8, latnd=2):
    ax.set_xlim(e[0], e[1])
    ax.set_ylim(e[2], e[3])
    ax.tick_params(labelsize=fs)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: f"{v:.2f}°E"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: f"{v:.{latnd}f}°N"))


def tk(t, p=""):
    """Catalog placeholders for UTC time t: {md} {ymd} {m} {d} (UTC+8 date), {lt} (UTC+8) and {utc}; prefix p for ranges."""
    lt = t + dt.timedelta(hours=8)
    return {
        p + "md": lang.md(lt),
        p + "ymd": lang.ymd(lt),
        p + "m": lt.month,
        p + "d": lt.day,
        p + "lt": lang.hm(lt),
        p + "utc": lang.hm(t),
    }


def utc(d, hm="00:00"):
    return dt.datetime.strptime(f"{d} {hm}", "%Y-%m-%d %H:%M")


def tloc(d, hm):
    """Overpass time of date d ("2026-10-10") at UTC hm ("03:05") in the catalog's format."""
    return lang.T("s2.tloc", **tk(utc(d, hm)))


# Fire detections (fire box 46.4–47.6°N, 118.8–120.2°E):
#   derived/viirs_box.csv     VIIRS 375 m L2 (VNP14IMG / VJ114IMG / VJ214IMG v002), t = granule start (fire_tables.py)
#   snapshot/firms_modis_7d_20261011.csv  FIRMS MODIS NRT 7-day rows of 10-11 00:54Z (no longer served)
#   derived/modis_l2_box.csv  MOD14 / MYD14 C6.1 L2, 10-10 11:20Z – 20:25Z (fire_tables.py)
_R = None


def _rows():
    out = []
    for fn in [D("derived", "viirs_box.csv"), SNAP / "firms_modis_7d_20261011.csv", D("derived", "modis_l2_box.csv")]:
        for r in csv.DictReader(open(fn)):
            out.append(
                (
                    float(r["lon"]),
                    float(r["lat"]),
                    float(r["frp"]),
                    dt.datetime.strptime(r["t"][:16], "%Y-%m-%d %H:%M"),
                    r["src"],
                )
            )
    return out


def firms(t0, t1, box=(118, 121, 46, 48)):
    global _R
    if _R is None:
        _R = _rows()
    return [x for x in _R if t0 <= x[3] <= t1 and box[0] <= x[0] <= box[1] and box[2] <= x[1] <= box[3]]


def firms_dots(ax, t0, t1, box, label=True, **kw):
    p = firms(t0, t1, box)
    print("  fire detections", t0, t1, len(p), {s: sum(1 for x in p if x[4] == s) for s in set(x[4] for x in p)})
    if not p:
        return 0
    a = np.array([(x[0], x[1]) for x in p])
    ax.scatter(
        a[:, 0],
        a[:, 1],
        s=kw.pop("s", 14),
        facecolors="none",
        edgecolors=kw.pop("c", "yellow"),
        linewidths=0.8,
        label=label,
        **kw,
    )
    return len(p)


# Arrow labels: the label's bottom-left sits at (x, y) and the arrow starts at its top edge, so a label grows
# upwards and stays inside the frame. Arrows are drawn after the constrained layout has moved the axes.
_PENDING = []


def arrow_label(ax, xy, txt, x, y, fs=9, lw=1.1):
    t = ax.text(
        x,
        y,
        txt,
        va="bottom",
        ha="left",
        color="white",
        fontsize=fs,
        path_effects=[pe.withStroke(linewidth=2.2, foreground="black")],
    )
    _PENDING.append((ax, xy, t, lw))


def flush_labels(fig):
    fig.canvas.draw()
    tail = lang.T("s2.arrow_tail")  # fraction of the label width at which the arrow leaves its top edge
    for ax, xy, t, lw in _PENDING:
        bb = t.get_window_extent()
        ab = ax.get_window_extent()
        if bb.x1 > ab.x1 or bb.y0 < ab.y0:
            print(f"  WARNING label overflows frame by {bb.x1 - ab.x1:.0f} px (x) / {ab.y0 - bb.y0:.0f} px (y)")
        x0, y1 = ax.transData.inverted().transform((bb.x0 + tail * bb.width, bb.y1))
        a = ax.annotate("", xy, xytext=(x0, y1), arrowprops=dict(color="white", lw=lw, shrinkA=4, shrinkB=0))
        a.arrow_patch.set_path_effects([pe.withStroke(linewidth=lw + 2.4, foreground="black")])
    _PENDING.clear()


DNBR_CMAP = ["#1a9850", "#d9ef8b", "#fee08b", "#fdae61", "#f46d43", "#a50026"]
DNBR_BOUNDS = [-1, -0.1, 0.1, 0.27, 0.44, 0.66, 2]
DNBR_TICKS = [-0.5, 0, 0.18, 0.35, 0.55, 0.9]
