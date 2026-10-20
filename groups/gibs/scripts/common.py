"""Shared paths, grids, border lines, burn-scar thresholds and map helpers for the gibs group."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from functools import cached_property

import numpy as np

from figkit import paths

GROUP = "gibs"
ARXAN = (119.944, 47.177)  # lon, lat of Arxan city
CN_CLOSE_LON = 117.5  # the OSM border line is closed westward along this meridian to form the Mongolian side


def data(*parts: str):
    return paths.data(GROUP, *parts)


# ---------------------------------------------------------------- GIBS tiles

TC = "TrueColor"
FC_MODIS = "Bands721"
FC_VIIRS = "BandsM11-I2-I1"

# WMS boxes: bbox (W, S, E, N), size (w, h), format
BOXES = {
    "loc": ((118, 46, 121, 48), (1200, 1170), "jpeg"),
    "wide": ((114, 44, 124, 50), (1600, 1400), "jpeg"),
    "zoom": ((118.8, 46.5, 120.1, 47.5), (1300, 1460), "png"),
    "south": ((119.2, 46.3, 120.0, 46.75), (1000, 560), "png"),
    "anim": ((118.8, 46.4, 120.2, 47.6), (1400, 1600), "png"),
}


def fc(sat: str) -> str:
    """False-colour band combination GIBS serves for a satellite."""
    return FC_MODIS if sat.startswith("MODIS") else FC_VIIRS


def tile(box: str, day: str, sat: str, bands: str):
    """Local path of a GIBS tile, e.g. tile("zoom", "2026-10-12", "VIIRS_NOAA21", FC_VIIRS)."""
    ext = "jpg" if BOXES[box][2] == "jpeg" else "png"
    return data("raw", "gibs", f"{box}_{day}_{sat}_CorrectedReflectance_{bands}.{ext}")


def rgb(path) -> np.ndarray:
    from PIL import Image

    return np.asarray(Image.open(path).convert("RGB"))


# ------------------------------------------------------------------- borders


def osm_border():
    """China–Mongolia border ways from the OSM API (118.85–119.90°E, 46.40–47.50°N), list of [lon, lat] lists."""
    return json.load(open(data("border", "border_osm.json")))


def osm_border_south():
    """Same border from the Overpass query that also covers the south-scar map (118.5–120.5°E, 46.3–47.8°N)."""
    return json.load(open(data("border", "border_osm_south.json")))


def ne_border():
    """Natural Earth 10m land boundary lines touching 105–130°E, 40–55°N."""
    return json.load(open(data("border", "border_ne.json")))


def main_line(segs):
    """The longest merged line of the border ways (the China–Mongolia border through the fire area)."""
    from shapely.geometry import LineString
    from shapely.ops import linemerge, unary_union

    L = linemerge(unary_union([LineString(p) for p in segs if len(p) > 1]))
    if L.geom_type != "LineString":
        L = max(L.geoms, key=lambda g: g.length)
    return L


def mongolia_polygon(L):
    """Close the border line westward to 117.5°E: points inside are on the Mongolian side."""
    c = list(L.coords)
    return c + [(CN_CLOSE_LON, c[-1][1]), (CN_CLOSE_LON, c[0][1])]


def utm():
    from pyproj import Transformer

    return Transformer.from_crs(4326, 32650, always_xy=True).transform


# ------------------------------------------------------- zoom grid and scars


class ZoomGrid:
    """Pixel grid of the 'zoom' GIBS tiles (118.8–120.1°E, 46.5–47.5°N, 1300 x 1460) with the OSM border."""

    ext = (118.8, 120.1, 46.5, 47.5)
    W, H = 1300, 1460

    def __init__(self):
        self.lat = self.ext[3] - (np.arange(self.H) + 0.5) * (1 / self.H)
        self.lon = self.ext[0] + (np.arange(self.W) + 0.5) * (1.3 / self.W)
        self.pxa = ((1.3 / self.W) * 111.32 * np.cos(np.radians(self.lat)) * (1 / self.H) * 110.95)[:, None] * np.ones(
            (1, self.W)
        )
        self.px_km = np.sqrt((1.3 / self.W * 111.32 * np.cos(np.radians(47))) * (1 / self.H * 110.95))
        self.osm = osm_border()

    @cached_property
    def xx_yy(self):
        return np.meshgrid(self.lon, self.lat)

    @cached_property
    def in_mng(self) -> np.ndarray:
        """True on the Mongolian side of the OSM border line."""
        from matplotlib.path import Path

        xx, yy = self.xx_yy
        poly = mongolia_polygon(main_line(self.osm))
        return Path(poly).contains_points(np.c_[xx.ravel(), yy.ravel()]).reshape(self.H, self.W)

    @cached_property
    def _line_m(self):
        from shapely.ops import transform

        return transform(utm(), main_line(self.osm))

    def dist_km(self, ys, xs) -> np.ndarray:
        """Distance (km, UTM 50N) from pixels (rows ys, cols xs) to the OSM border line."""
        from shapely.geometry import Point

        X, Y = utm()(self.lon[xs], self.lat[ys])
        return np.array([self._line_m.distance(Point(a, b)) for a, b in zip(X, Y)]) / 1000

    def box(self, x0, x1, y0, y1) -> np.ndarray:
        xx, yy = self.xx_yy
        return (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1)

    def area(self, m) -> float:
        return float((m * self.pxa).sum())


def scar_layers(a: np.ndarray, pxa: np.ndarray, gmax: int = 75):
    """Burn scar on a GIBS false-colour tile.

    Threshold red/green > 1.4, green < gmax, red > 20; opening x2; keep patches >= 5 km²;
    closing x3 (raw); fill holes (filled). Returns raw, filled, the label image of
    filled, and main = the largest patch of filled.
    """
    from scipy import ndimage

    a = a.astype(int)
    R, G = a[..., 0], a[..., 1]
    m = (R > 1.4 * G) & (G < gmax) & (R > 20)
    m = ndimage.binary_opening(m, iterations=2)
    lab, n = ndimage.label(m)
    sz = ndimage.sum(m, lab, range(1, n + 1)) * pxa.mean()
    m = np.isin(lab, 1 + np.where(sz >= 5)[0])
    raw = ndimage.binary_closing(m, iterations=3)
    filled = ndimage.binary_fill_holes(raw)
    lab, n = ndimage.label(filled)
    sz = ndimage.sum(filled, lab, range(1, n + 1))
    main = lab == (1 + np.argmax(sz))
    return dict(raw=raw, filled=filled, lab=lab, main=main)


# The ten zoom scenes the scar steps use: (id, day, satellite, overpass time UTC)
SCENES = [
    ("20261012-terra", "2026-10-12", "MODIS_Terra", "01:32"),
    ("20261012-noaa20", "2026-10-12", "VIIRS_NOAA20", "03:47"),
    ("20261012-noaa21", "2026-10-12", "VIIRS_NOAA21", "04:32"),
    ("20261012-snpp", "2026-10-12", "VIIRS_SNPP", "05:10"),
    ("20261012-aqua", "2026-10-12", "MODIS_Aqua", "06:35"),
    ("20261013-terra", "2026-10-13", "MODIS_Terra", "00:35"),
    ("20261013-noaa20", "2026-10-13", "VIIRS_NOAA20", "04:2x"),
    ("20261013-aqua", "2026-10-13", "MODIS_Aqua", "05:5x"),
]


# -------------------------------------------------------------------- time


def utc(day: str, hm: str) -> datetime:
    return datetime.strptime(f"{day} {hm}", "%Y-%m-%d %H:%M")


def local(t: datetime) -> datetime:
    """UTC -> Beijing time (UTC+8), the time every figure prints."""
    return t + timedelta(hours=8)


# ------------------------------------------------------------- map helpers

STROKE_LW = 2


def stroke(lw=STROKE_LW):
    import matplotlib.patheffects as pe

    return [pe.withStroke(linewidth=lw, foreground="black")]


def deg_fmt(ax, fmt="{:g}"):
    import matplotlib.pyplot as plt

    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: fmt.format(v) + "°E"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: fmt.format(v) + "°N"))


def plot_lines(ax, segs, **kw):
    for seg in segs:
        s = np.array(seg)
        ax.plot(s[:, 0], s[:, 1], **kw)


# ------------------------------------------------------------- figure setup

# Text sizes of the blog layouts (7.2 in wide at 200 dpi)
BLOG_RC = {"font.size": 9, "xtick.labelsize": 9, "ytick.labelsize": 9, "axes.titlesize": 10, "legend.fontsize": 9}
W_IN, DPI = 7.2, 200

# House style for borders: OSM solid yellow, Natural Earth dashed cyan
OSM_STYLE = dict(color="yellow")
NE_STYLE = dict(color="cyan", ls="--")


def init(script: str, rc: dict | None = None):
    """Agg backend, figkit language/fonts, then the figure's rcParams. Returns the figkit lang module."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from figkit import lang

    lang.init(script)
    plt.rcParams["axes.unicode_minus"] = False
    if rc:
        plt.rcParams.update(rc)
    return lang


def mark_arxan(ax, label: str, fs=9, left=False, ms=4):
    ax.plot(*ARXAN, marker="s", ms=ms, mfc="white", mec="black")
    ax.annotate(
        label,
        ARXAN,
        xytext=(-3, 3) if left else (3, 3),
        ha="right" if left else "left",
        textcoords="offset points",
        color="white",
        fontsize=fs,
        path_effects=stroke(),
    )


def map_axes(ax, ext, left, bottom, xt, yt):
    """Limits, ticks in degrees, tick labels only on the outer panels."""
    ax.set_xlim(ext[0], ext[1])
    ax.set_ylim(ext[2], ext[3])
    ax.set_xticks(xt)
    ax.set_yticks(yt)
    deg_fmt(ax)
    if not left:
        ax.set_yticklabels([])
    if not bottom:
        ax.set_xticklabels([])


def save(fig, path):
    fig.savefig(path, dpi=DPI)
    w, h = fig.get_size_inches() * DPI
    print(path, int(w), int(h))


def line(lang, key: str, **kw) -> dict:
    """Line style from the catalog: the color / ls / lw / alpha values set under ``key`` (e.g. gibs-daily.osm), then kw.

    The published Chinese figures drew some borders differently from the English and Japanese ones
    (dashed OSM, pale-yellow Natural Earth), and the Chinese captions describe those lines, so the
    style lives in each language's catalog.
    """
    d = {a: lang.T(f"{key}.{a}") for a in ("color", "ls", "lw", "alpha") if lang.has(f"{key}.{a}")}
    d.update(kw)
    return d


def halo(width) -> dict:
    """path_effects kwargs for a black halo of the given width; none for 0."""
    return {"path_effects": stroke(width)} if width else {}
