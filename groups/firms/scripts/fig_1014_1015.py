"""firms-20261014-1015: detections of ten overpasses from 10-14 daytime to 10-15 14:52 UTC+8 over the 10-14
NOAA-20 burn scar (GIBS M11-I2-I1, unfilled mask), with the OSM border. VIIRS from the L2 granules, Aqua MODIS
from the FIRMS MODIS NRT records; only detections north of 46.9°N (the main fire).

The S-NPP 10-15 05:48Z pass (1 detection, 4.12 MW) is in the LANCE NRT granule but was not yet in the FIRMS
7-day file when the published figure was drawn; it is marked * and labelled with the granule start time."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import pandas as pd

from common import (
    ANIM_BOX,
    ARXAN,
    BJ,
    SAT_NAME,
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
C = "firms-20261014-1015."
scar = scar_masks(scar_png("2026-10-14", "NOAA20"))[1]
v = in_box(viirs(), ANIM_BOX, strict=True)
m = in_box(modis_nrt(), ANIM_BOX, strict=True)
m = m.assign(src=m.satellite)
q = pd.concat([v, m])
q = q[q.latitude > 46.9]
# (FIRMS acq_time UTC, source, day/night key, colour, marker, base size, exact granule start instead of acq_time)
PASSES = [
    ("2026-10-14 04:32", "SUOMI", "day", "#8c564b", "o", 40, False),
    ("2026-10-14 06:12", "SUOMI", "day", "#bcbd22", "h", 40, False),
    ("2026-10-14 17:49", "J2", "night", "#9467bd", "D", 40, False),
    ("2026-10-14 18:26", "SUOMI", "night", "#17becf", "v", 45, False),
    ("2026-10-14 18:45", "J1", "night", "#2ca02c", "^", 45, False),
    ("2026-10-15 04:14", "SUOMI", "day", "#1f77b4", "s", 40, False),
    ("2026-10-15 04:32", "J1", "day", "#d62728", "o", 60, False),
    ("2026-10-15 05:16", "J2", "day", "#e377c2", "D", 40, False),
    ("2026-10-15 05:48", "SUOMI", "day", "#7f7f7f", "X", 110, True),
    ("2026-10-15 06:52", "A", "day_1km", "#ff7f0e", "P", 140, False),
]


def lonlat(ax, fs=9):
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x:.1f}°E"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f"{y:.1f}°N"))
    ax.tick_params(labelsize=fs)


fig, ax = plt.subplots(figsize=(7.2, 10.0), constrained_layout=True)
draw_scar(ax, scar)
draw_border(ax, color="k", ls="--", lw=1.2)
for t, s, dn, c, mk, sz, start in PASSES:
    g = q[q.src == s]
    g = g[g.t == pd.Timestamp(t)] if start else pick_pass(g, t)
    sat = "Aqua MODIS" if s == "A" else SAT_NAME[s]
    name = lang.T("places." + dn, **{"pass": f"{sat} {lang.mdhm(pd.Timestamp(t) + BJ)}"})
    if start:
        name = lang.T(C + "file_start", **{"pass": name})
    ax.scatter(
        g.longitude,
        g.latitude,
        s=sz + g.frp * 3,
        c=c,
        marker=mk,
        edgecolor="k",
        lw=0.6,
        zorder=7 if start else (6 if s == "A" else 5),
        label=lang.T(
            "places.entry_one" if len(g) == 1 else "places.entry",
            **{"pass": name},
            n=lang.num(len(g)),
            mw=lang.num(g.frp.sum()),
        ),
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
lonlat(ax)
h, l = ax.get_legend_handles_labels()
fig.legend(
    h,
    l,
    loc="outside lower center",
    ncol=1,
    fontsize=8.5,
    title=lang.T(C + "legend_title"),
    title_fontsize=8.5,
    markerscale=0.8,
    frameon=False,
)
fig.suptitle(lang.T(C + "title"), fontsize=10)
fig.get_layout_engine().set(h_pad=0.06)
fig.savefig(lang.out("firms-20261014-1015"), dpi=200)
