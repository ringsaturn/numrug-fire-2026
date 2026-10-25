"""firms-progression-20261013: VIIRS detections in the fire area coloured by UTC+8 day, 10-08 to 10-13 morning
(r3 table), with the OSM border, places and region names."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import BJ, D, draw_border
from figkit import lang, osm

lang.init(__file__)
C = "firms-progression-20261013."
HALO = [pe.withStroke(linewidth=3, foreground="white")]
# (lat, lon, key, marker, label left of the dot)
PLACES = [
    (47.177, 119.944, "places.arxan_city", "ko", True),
    (47.289, 119.84, "places.yirshi", "ko", False),
]
# OSM 2026-10-25 places: (key, marker, label offset in points, horizontal alignment)
OSM_PLACES = [
    ("bag", "ko", (6, -2), "left"),
    ("zastav", "ko", (-6, 5), "right"),
    ("sumber", "k^", (-6, -13), "right"),
    ("arxan_port", "k^", (6, 3), "left"),
]
COLOURS = ["#4575b4", "#91bfdb", "#fee090", "#fc8d59", "#d73027", "#67001f"]

d = pd.read_csv(D / "main_r3.csv", parse_dates=["t"])
d["bj"] = d.t + BJ
fig, ax = plt.subplots(figsize=(10, 8.2))
for k, c in enumerate(COLOURS):
    day = pd.Timestamp(2026, 10, 8 + k)
    q = d[(d.bj >= day) & (d.bj <= day + pd.Timedelta("23:59:00")) & (d.src != "MODIS")]
    if len(q):
        ax.scatter(
            q.longitude,
            q.latitude,
            s=7,
            c=c,
            label=lang.T(C + "legend", day=lang.md(day), n=lang.num(len(q))),
            edgecolors="none",
            zorder=3,
        )
draw_border(ax, color="k", lw=1.4, ls="--", zorder=5)
osm.roads(ax, ("unclassified",), color="0.45", lw=0.6, zorder=2, label=lang.T("osm.roads"))
osm.roads(ax, ("track",), color="0.45", lw=0.6, ls=(0, (2, 1.2)), zorder=2)
osm.spa(ax, color="#1a9641", lw=1.0, zorder=4, label=lang.T("osm.spa"))
for la, lo, key, mk, left in PLACES:
    ax.plot(lo, la, mk, ms=6, zorder=6)
    ax.text(
        lo - 0.02 if left else lo + 0.02,
        la + 0.015,
        lang.T(key),
        fontsize=10,
        zorder=6,
        ha="right" if left else "left",
        path_effects=HALO,
    )
for key, mk, off, ha in OSM_PLACES:
    lo, la = osm.PLACES[key]
    ax.plot(lo, la, mk, ms=6, zorder=6)
    ax.annotate(
        osm.T(key), (lo, la), xytext=off, textcoords="offset points", ha=ha, fontsize=9.5, zorder=6,
        bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.8),
        family=osm.font(),
    )
ax.plot(*osm.IGNITION, marker="*", ms=14, mfc="none", mec="cyan", mew=1.6, ls="", zorder=7, label=lang.T("osm.ignition"))
ax.text(118.76, 47.55, lang.T(C + "mongolia"), fontsize=12, color="0.3")
ax.text(120.13, 46.515, lang.T(C + "hinggan"), fontsize=10.5, color="0.3", ha="right", va="bottom")
# 119.0-119.85°E along the southern edge is East Ujimqin Banner (Xilin Gol League); east of ~119.87°E is Hinggan League
# (geoBoundaries gbOpen CHN ADM3, from OSM).
ax.text(119.3, 46.515, lang.T(C + "ujimqin"), fontsize=10.5, color="0.3", ha="center", va="bottom")
ax.set_xlim(118.7, 120.15)
ax.set_ylim(46.5, 47.65)
ax.set_aspect(1 / np.cos(np.radians(47)))
ax.set_xlabel(lang.T("places.lon"))
ax.set_ylabel(lang.T("places.lat"))
ax.grid(alpha=0.3)
ax.legend(loc="upper right", fontsize=9, markerscale=2.5)
for h in ax.get_legend().legend_handles:
    if getattr(h, "get_marker", lambda: None)() == "*":
        h.set_markersize(10)
fig.text(0.01, 0.006, lang.T("osm.credit"), ha="left", va="bottom", fontsize=7.5, color="0.35")
ax.set_title(lang.T(C + "title"))
fig.tight_layout()
fig.savefig(lang.out("firms-progression-20261013"), dpi=150)
