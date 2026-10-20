"""Shared inputs of the firms group: file locations, the OSM border, the Mongolian-side polygon,
VIIRS/MODIS detection tables, the GIBS burn-scar mask and the 10-12 place names."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from figkit import paths

D = paths.data("firms")
RAW = D / "raw"
SNAPSHOT = Path(__file__).resolve().parents[1] / "snapshot"
GIBS = RAW / "gibs"

# The fire box of the case-anim tables (detections strictly inside it) and of the r2/r3 FIRMS tables.
ANIM_BOX = (46.4, 47.6, 118.8, 120.2)  # S, N, W, E
TABLE_BOX = (46.3, 47.9, 118.3, 120.6)
WIDE_BOX = (44, 50.5, 110, 124)  # FIRMS pre-filter, kept for the derived CSVs

ARXAN = (119.944, 47.177)  # Arxan city, as in the FIRMS figures
ASPECT = 1 / np.cos(np.radians(47))
BJ = pd.Timedelta(hours=8)

# VIIRS platform -> FIRMS source code (SUOMI/J1/J2) and the satellite name drawn on the figures.
SRC = {"SUOMI-NPP": "SUOMI", "NPP": "SUOMI", "JPSS-1": "J1", "NOAA-20": "J1", "JPSS-2": "J2", "NOAA-21": "J2"}
SAT_NAME = {"SUOMI": "S-NPP", "J1": "NOAA-20", "J2": "NOAA-21", "T": "Terra", "A": "Aqua"}


def border(kind: str = "mapbbox") -> list[np.ndarray]:
    """OSM admin_level=2 ways as [lon, lat] arrays.

    mapbbox: from the four OSM API map tiles (FIRMS figures); overpass: from the Overpass bbox query (animation).
    """
    return [np.array(p) for p in json.load(open(D / f"border_osm_{kind}.json")) if len(p) > 1]


def mongolia(kind: str = "mapbbox"):
    """(prepared Mongolian-side polygon, border line in UTM 50N, lon/lat -> UTM transform).

    The longest merged border line is closed westwards at 117.5°E; points inside are on the Mongolian side.
    """
    from pyproj import Transformer
    from shapely.geometry import LineString, Polygon
    from shapely.ops import linemerge, transform, unary_union
    from shapely.prepared import prep

    T = Transformer.from_crs(4326, 32650, always_xy=True).transform
    L = linemerge(unary_union([LineString(p) for p in border(kind)]))
    if L.geom_type != "LineString":
        L = max(L.geoms, key=lambda g: g.length)
    c = list(L.coords)
    return prep(Polygon(c + [(117.5, c[-1][1]), (117.5, c[0][1])])), transform(T, L), T


def viirs() -> pd.DataFrame:
    """VIIRS 375 m detections from the L2 granules (prepare step viirs-l2); t = granule start, UTC."""
    return pd.read_csv(D / "viirs_l2.csv", parse_dates=["t"])


def modis_nrt() -> pd.DataFrame:
    """FIRMS MODIS C6.1 NRT 7-day rows (10-11 to 10-16) inside the wide box, with t = acquisition time, UTC."""
    m = pd.read_csv(SNAPSHOT / "MODIS_C6_1_Global_7d_box.csv")
    m["t"] = pd.to_datetime(m.acq_date + " " + m.acq_time.astype(str).str.zfill(4), format="%Y-%m-%d %H%M")
    return m


def in_box(q: pd.DataFrame, box, strict: bool = False) -> pd.DataFrame:
    s, n, w, e = box
    if strict:
        return q[(q.latitude > s) & (q.latitude < n) & (q.longitude > w) & (q.longitude < e)]
    return q[q.latitude.between(s, n) & q.longitude.between(w, e)]


def pick_pass(q: pd.DataFrame, t: str) -> pd.DataFrame:
    """Detections of one overpass given its FIRMS acq_time; the L2 granule start is up to 8 min earlier."""
    t = pd.Timestamp(t)
    return q[(q.t > t - pd.Timedelta(minutes=8)) & (q.t <= t)]


# GIBS "zoom" box of the burn-scar figures: 118.8-120.1°E, 46.5-47.5°N, 1300 x 1460 px.
SCAR_EXT = (118.8, 120.1, 46.5, 47.5)


def scar_masks(png: Path):
    """Burn scar on a GIBS VIIRS M11-I2-I1 image: R > 1.4 G, G < 75, R > 20, opening x2, components >= 5 km²,
    closing x3. Returns (rgb, raw, filled, main) where main is the largest component after hole filling."""
    from PIL import Image
    from scipy import ndimage

    a = np.asarray(Image.open(png).convert("RGB")).astype(int)
    h, w = a.shape[:2]
    W, E, S, N = SCAR_EXT
    lat = N - (np.arange(h) + 0.5) * ((N - S) / h)
    pxa = (((E - W) / w) * 111.32 * np.cos(np.radians(lat)) * ((N - S) / h) * 110.95)[:, None] * np.ones((1, w))
    R, G = a[..., 0], a[..., 1]
    m = (R > 1.4 * G) & (G < 75) & (R > 20)
    m = ndimage.binary_opening(m, iterations=2)
    lab, n = ndimage.label(m)
    sz = ndimage.sum(m, lab, range(1, n + 1)) * pxa.mean()
    m = np.isin(lab, 1 + np.where(sz >= 5)[0])
    raw = ndimage.binary_closing(m, iterations=3)
    fill = ndimage.binary_fill_holes(raw)
    lab, n = ndimage.label(fill)
    sz = ndimage.sum(fill, lab, range(1, n + 1))
    main = lab == (1 + np.argmax(sz))
    return a, raw, fill, main, pxa


def scar_png(day: str, sat: str) -> Path:
    return GIBS / f"zoom_{day}_VIIRS_{sat}_CorrectedReflectance_BandsM11-I2-I1.png"


def draw_scar(ax, mask):
    ax.imshow(
        np.where(mask, 1, np.nan),
        extent=SCAR_EXT,
        cmap="Greys",
        vmin=0,
        vmax=1.6,
        alpha=0.55,
        origin="upper",
        aspect=ASPECT,
    )


def draw_border(ax, **kw):
    for p in border("mapbbox"):
        ax.plot(p[:, 0], p[:, 1], **kw)
