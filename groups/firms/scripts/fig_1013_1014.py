"""firms-20261013-1014-0911: detections of six overpasses from 10-13 daytime to 10-14 09:11 UTC+8 over the 10-12
NOAA-21 burn scar (main patch from GIBS M11-I2-I1, 4,450 km²), with the OSM border. VIIRS from the L2 granules,
Terra MODIS from the FIRMS MODIS NRT records; each pass is selected by its FIRMS acq_time."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import pandas as pd

from common import (
    ARXAN,
    BJ,
    SAT_NAME,
    TABLE_BOX,
    draw_border,
    draw_scar,
    in_box,
    modis_nrt,
    pick_pass,
    scar_masks,
    scar_png,
    viirs,
)
from figkit import lang

lang.init(__file__)
C = "firms-20261013-1014-0911."
scar = scar_masks(scar_png("2026-10-12", "NOAA21"))[3]
v = in_box(viirs(), TABLE_BOX)
m = in_box(modis_nrt(), TABLE_BOX)
# (source, FIRMS acq_time UTC, day/night key, colour, marker, base size)
PASSES = [
    ("J1", "2026-10-13 03:30", "day", "#d62728", "o", 60),
    ("SUOMI", "2026-10-13 17:05", "night", "#1f77b4", "s", 40),
    ("J1", "2026-10-13 17:24", "night", "#2ca02c", "^", 45),
    ("J2", "2026-10-13 18:09", "night", "#9467bd", "D", 40),
    ("SUOMI", "2026-10-13 18:45", "night", "#17becf", "v", 45),
    ("MODIS", "2026-10-14 01:11", "day_1km", "#ff7f0e", "P", 140),
]

fig, ax = plt.subplots(figsize=(8.5, 7.2), constrained_layout=True)
draw_scar(ax, scar)
draw_border(ax, color="k", ls="--", lw=1.2)
for s, t, dn, c, mk, sz in PASSES:
    q = pick_pass(m if s == "MODIS" else v[v.src == s], t)
    sat = "Terra MODIS" if s == "MODIS" else SAT_NAME[s]
    name = lang.T("places." + dn, **{"pass": f"{sat} {lang.mdhm(pd.Timestamp(t) + BJ)}"})
    ax.scatter(
        q.longitude,
        q.latitude,
        s=sz + q.frp * 3,
        c=c,
        marker=mk,
        edgecolor="k",
        lw=0.6,
        zorder=6 if s == "MODIS" else 5,
        label=lang.T("places.entry", **{"pass": name}, n=lang.num(len(q)), mw=lang.num(q.frp.sum())),
    )
ax.plot(*ARXAN, "k*", ms=12)
ax.text(
    119.925,
    47.19,
    lang.T("places.arxan"),
    fontsize=10,
    ha="right",
    zorder=7,
    path_effects=[pe.withStroke(linewidth=3, foreground="white")],
)
ax.set_xlim(118.9, 120.1)
ax.set_ylim(46.55, 47.45)
ax.grid(alpha=0.3)
h, l = ax.get_legend_handles_labels()
fig.legend(
    h,
    l,
    loc="outside lower center",
    ncol=2,
    fontsize=8,
    frameon=False,
    markerscale=0.8,
    title=lang.T(C + "legend_title"),
    title_fontsize=8,
)
ax.set_title(lang.T(C + "title"), fontsize=lang.T(C + "title_size"))
ax.set_xlabel(lang.T(C + "lon"))
ax.set_ylabel(lang.T(C + "lat"))
fig.savefig(lang.out("firms-20261013-1014-0911"), dpi=150)
