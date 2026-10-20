"""firms-east-20261012: the 10-12 daytime VIIRS passes along the border west of Arxan, marker size by FRP and
colour by overpass time, over the earlier detections in grey (r2 table)."""

import datetime as dt

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import BJ, D, draw_border
from figkit import lang

lang.init(__file__)
C = "firms-east-20261012."
HALO = [pe.withStroke(linewidth=3, foreground="white")]
NAMES = {"SUOMI": "S-NPP VIIRS", "J1": "NOAA-20 VIIRS", "J2": "NOAA-21 VIIRS"}
# (lat, lon, key, label left of the dot); Yirshi sits below its dot because the legend is above it
PLACES = [(47.177, 119.944, "arxan_city", True), (47.289, 119.84, "yirshi", False)]

d = pd.read_csv(D / "main_r2.csv", parse_dates=["t"])
z = d[(d.t >= "2026-10-12 00:00") & (d.src != "MODIS")]
o = d[(d.t < "2026-10-12 00:00") & (d.src != "MODIS")]
fig, ax = plt.subplots(figsize=(9, 8))
ax.scatter(
    o.longitude,
    o.latitude,
    s=5,
    c="0.8",
    edgecolors="none",
    zorder=2,
    label=lang.T(C + "before", time=lang.mdhm(dt.datetime(2026, 10, 12, 8)), day=lang.md(dt.datetime(2026, 10, 12))),
)
for s, mk in [("J1", "o"), ("J2", "s"), ("SUOMI", "^")]:
    q = z[z.src == s]
    if len(q):
        sc = ax.scatter(
            q.longitude,
            q.latitude,
            s=10 + q.frp.clip(0, 300) / 3,
            c=(q.t + BJ).dt.hour + (q.t.dt.minute / 60),
            cmap="autumn_r",
            vmin=11,
            vmax=14,
            marker=mk,
            edgecolors="k",
            linewidths=0.3,
            zorder=4,
            label=lang.T(C + "entry", sat=NAMES[s], day=lang.md(dt.datetime(2026, 10, 12)), n=lang.num(len(q))),
        )
draw_border(ax, color="k", lw=1.4, ls="--", zorder=5)
for la, lo, key, left in PLACES:
    ax.plot(lo, la, "ko", ms=6, zorder=6)
    ax.text(
        lo - 0.01 if left else lo + 0.01,
        la + 0.008 if left else la - 0.006,
        lang.T("places." + key),
        fontsize=10,
        zorder=6,
        ha="right" if left else "left",
        va="baseline" if left else "top",
        path_effects=HALO,
    )
ax.set_xlim(119.55, 120.02)
ax.set_ylim(46.9, 47.35)
ax.set_aspect(1 / np.cos(np.radians(47)))
hours = [11, 11.5, 12, 12.5, 13, 13.5, 14]
cb = plt.colorbar(sc, ax=ax, shrink=0.7, label=lang.T("common.local_time_axis"))
cb.set_ticks(hours)
cb.set_ticklabels([lang.hm(dt.datetime(2026, 10, 12, int(h), int(round(h % 1 * 60)))) for h in hours])
ax.legend(loc="upper right", fontsize=8, borderaxespad=0.3)
ax.grid(alpha=0.3)
ax.set_title(lang.T(C + "title"), fontsize=lang.T(C + "title_size"))
ax.set_xlabel(lang.T("places.lon"))
ax.set_ylabel(lang.T("places.lat"))
fig.tight_layout()
fig.savefig(lang.out("firms-east-20261012"), dpi=150)
