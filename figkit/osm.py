"""OpenStreetMap snapshot of 2026-10-25 (Overpass, © OpenStreetMap contributors, ODbL) shared by several groups:
Mongolian-side roads, rivers, the Numrug reserve boundary, national border ways, places, the shortest road routes
to the end of the track nearest the ignition point, and three Sentinel-2 linear features digitised by hand.

    from figkit import osm
    S = osm.load()          # dict, see build() for the layers
    osm.T(key)              # bilingual place label in the current language (catalog key "osm.<key>")

The snapshot file is snapshot/osm-20261025.json. It was cut from Overpass ``out geom`` downloads with

    python -m figkit.osm build DIR

where DIR holds roads_mn.json (highway ways in Khalkhgol sum), water.json (waterway=river, 46.4-47.8°N,
118.0-120.3°E), border.json (admin_level=2 ways, 45.5-48.5°N, 116.5-121.5°E), spa_poly.geojson (relation
21785019 assembled), pois2.json and routes.geojson (routes computed on the roads_mn graph by shortest path).
"""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

from . import paths

FILE = paths.ROOT / "snapshot" / "osm-20261025.json"

# Points used by the figures, lon/lat (OSM element in the comment).
IGNITION = (119.40, 46.88)  # ignition point used in the text (not an OSM element)
PLACES = {
    "sumber": (119.4644209, 47.3250903),  # way 1344889485 Сүмбэр боомт
    "arxan_port": (119.5267492, 47.3257193),  # way 1265623442 阿尔山口岸
    "zastav": (119.3211868, 47.4166423),  # node 4450389994 Нөмрөгийн застав
    "bag": (119.35887, 46.983805),  # node 3774795861 Нөмрөг баг
    "sum": (118.6245846, 47.629254),  # node 1478274074 Халхгол (sum centre)
    "ford": (119.3578598, 46.97478),  # node 14316335076 ford=yes
    "track_end": (119.3715405, 46.9409528),  # last node of way 1571401319 (highway=track)
}
# Banner boundaries meeting the national border (shared end nodes of admin_level=2 ways).
JUNCTIONS = {
    "ujimqin_horqin": (119.8986, 46.6651),
    "horqin_arxan": (119.9213, 46.9026),
    "arxan_barag": (119.4793, 47.3337),
}
NEAREST = {
    "arxan_segment": (119.7948, 47.0083),  # 33.3 km, way 762201571
    "border": (119.4305, 46.6386),  # 26.9 km, way 161028055 (East Ujimqin)
}


@lru_cache(maxsize=1)
def load() -> dict:
    return json.load(open(FILE))


def T(key: str, wrap: bool = False) -> str:
    """Place label; wrap=True puts the translation on a second line."""
    from . import lang

    s = lang.T("osm." + key)
    return s.replace("（", "\n（").replace(" (", "\n(") if wrap else s


def font() -> list[str]:
    """Font family list for labels with Cyrillic: the CJK fonts of the zh/ja catalogs draw Cyrillic full-width,
    so DejaVu Sans goes first and the language's own fonts fill in the CJK glyphs."""
    import matplotlib.pyplot as plt

    return ["DejaVu Sans"] + [f for f in plt.rcParams["font.family"] if f != "DejaVu Sans"]


def roads(ax, kinds=("unclassified", "track"), box=None, label=None, **kw):
    """Mongolian-side roads of the given highway classes; box (lon0, lon1, lat0, lat1) drops ways outside it."""
    first = True
    for w in load()["roads"]:
        if w["hw"] not in kinds:
            continue
        c = w["c"]
        if box and not any(box[0] <= x <= box[1] and box[2] <= y <= box[3] for x, y in c):
            continue
        x, y = zip(*c)
        ax.plot(x, y, label=label if first else None, **kw)
        first = False


def spa(ax, label=None, **kw):
    for i, ring in enumerate(load()["spa"]):
        x, y = zip(*ring)
        ax.plot(x, y, label=label if i == 0 else None, **kw)


def rivers(ax, names=None, **kw):
    for w in load()["rivers"]:
        if names is not None and w["name"] not in names:
            continue
        x, y = zip(*w["c"])
        ax.plot(x, y, **kw)


# Where each letter sits: (vertex index, offset in points, ha, va). A runs W-E, B and C N-S; A and B start 0.4 km apart.
LETTER_AT = {
    "s2-line-a": (0, (-3, -2), "right", "top"),
    "s2-line-b": (0, (0, 3), "center", "bottom"),
    "s2-line-c": (0, (-3, 0), "right", "center"),
}


def legend_handles(handles):
    """Copies of legend handles with white lines drawn grey, so roads stay visible on a white legend."""
    import copy

    out = []
    for h in handles:
        h = copy.copy(h)
        if hasattr(h, "get_color") and h.get_color() == "white":
            h.set_color("0.45")
        out.append(h)
    return out


def ignition_marks(ax, fs=8, lw=1.0, star=13, legend=True, letters=True):
    """Around the ignition point: OSM roads, the end of the nearest track (way 1571401319), a dashed line from it to
    the ignition point with its length, the Sentinel-2 linear features A/B/C and the ignition star."""
    import matplotlib.patheffects as pe
    from pyproj import Geod

    from . import lang

    halo = [pe.withStroke(linewidth=2, foreground="black")]
    e = (*ax.get_xlim(), *ax.get_ylim())
    roads(ax, ("unclassified", "track"), box=e, color="white", lw=0.8 * lw, alpha=0.9, zorder=4,
          label=lang.T("osm.roads") if legend else None)
    (x0, y0), (x1, y1) = PLACES["track_end"], IGNITION
    km = Geod(ellps="WGS84").inv(x0, y0, x1, y1)[2] / 1000
    ax.plot([x0, x1], [y0, y1], color="cyan", lw=1.2 * lw, ls=(0, (4, 2.5)), zorder=5)
    ax.annotate(f"{km:.1f} km", ((x0 + x1) / 2, (y0 + y1) / 2), xytext=(5, 0), textcoords="offset points",
                color="white", fontsize=fs, va="center", path_effects=halo, zorder=7)
    ax.plot(x0, y0, "s", ms=5 * lw, mfc="white", mec="black", mew=0.8, zorder=6,
            label=lang.T("osm.track_end") if legend else None, ls="")
    for i, (k, c) in enumerate(sorted(load()["s2_lines"].items())):
        x, y = zip(*c)
        ax.plot(x, y, color="#ff3df5", lw=1.6 * lw, zorder=5, solid_capstyle="round",
                label=lang.T("osm.s2_lines") if legend and i == 0 else None)
        if letters:
            at, off, ha, va = LETTER_AT[k]
            ax.annotate(k[-1].upper(), c[at], xytext=off, textcoords="offset points", ha=ha, va=va,
                        color="#ff3df5", fontsize=fs, weight="bold", path_effects=halo, zorder=7)
    ax.plot(x1, y1, marker="*", ms=star, mfc="none", mec="cyan", mew=1.4, ls="", zorder=7,
            label=lang.T("osm.ignition") if legend else None)
    return km


def _r(c):
    return [round(c[0], 5), round(c[1], 5)]


def build(src: Path) -> None:
    skip = {"path", "footway", "steps", "pedestrian", "construction"}
    roads = [
        {"id": e["id"], "hw": e["tags"].get("highway"), "c": [_r((p["lon"], p["lat"])) for p in e["geometry"]]}
        for e in json.load(open(src / "roads_mn.json"))["elements"]
        if e["tags"].get("highway") not in skip
    ]
    rivers = [
        {
            "id": e["id"],
            "name": e["tags"].get("name:mn") or e["tags"].get("name"),
            "c": [_r((p["lon"], p["lat"])) for p in e["geometry"]],
        }
        for e in json.load(open(src / "water.json"))["elements"]
        if e["tags"].get("waterway") == "river"
    ]
    border = [
        {"id": e["id"], "c": [_r((p["lon"], p["lat"])) for p in e["geometry"]]}
        for e in json.load(open(src / "border.json"))["elements"]
        if e["type"] == "way" and "geometry" in e
    ]
    spa = json.load(open(src / "spa_poly.geojson"))
    spa = [[_r(c) for c in ring] for ring in spa["coordinates"]]
    routes, lines = {}, {}
    for f in json.load(open(src / "routes.geojson"))["features"]:
        p = f["properties"]
        (routes if p["kind"] == "route" else lines)[p["id"]] = [_r(c) for c in f["geometry"]["coordinates"]]
    out = {
        "source": "OpenStreetMap via Overpass API, snapshot 2026-10-25 (osm_base 2026-10-25T01:25Z), ODbL",
        "roads": roads,
        "rivers": rivers,
        "border": border,
        "spa": spa,
        "routes": routes,
        "s2_lines": lines,
        "s2_lines_note": "Sentinel-2 L2A 2026-10-05/10-08, hand-digitised, about ±50 m; nature unknown",
    }
    FILE.parent.mkdir(exist_ok=True)
    json.dump(out, open(FILE, "w"), separators=(",", ":"), ensure_ascii=False)
    print(FILE, FILE.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    if sys.argv[1:2] == ["build"]:
        build(Path(sys.argv[2]))
