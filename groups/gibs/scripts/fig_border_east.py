"""border-east-20261012-{falsecolor,truecolor}: the five 10-12 GIBS scenes of the eastern fire front 13–17 km west of Arxan,
with two check boxes east of the OSM border; the false-colour figure adds the FIRMS detections of the same overpass,
split by side of the line (3 x 2, legend in the sixth cell).

    fig_border_east.py falsecolor | truecolor

FIRMS points from firms/firms_20261012.csv (derive_firms.py).
"""

import sys

import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from common import OSM_STYLE, TC, ZoomGrid, data, deg_fmt, fc, init, local, osm_border, plot_lines, rgb, save, tile, utc

lang = init(__file__)
import matplotlib.pyplot as plt  # noqa: E402

T = lang.T
F = "border-east-20261012"
DAY = "2026-10-12"
SCENES = [
    ("MODIS_Terra", "Terra", "7-2-1", "01:32"),
    ("VIIRS_NOAA20", "NOAA-20", "M11-I2-I1", "03:47"),
    ("VIIRS_NOAA21", "NOAA-21", "M11-I2-I1", "04:32"),
    ("VIIRS_SNPP", "S-NPP", "M11-I2-I1", "05:10"),
    ("MODIS_Aqua", "Aqua", "7-2-1", "06:35"),
]
BOXES = {"S": (119.745, 119.80, 47.115, 47.140), "N": (119.715, 119.765, 47.150, 47.170)}
view = (119.62, 119.90, 47.04, 47.24)
asp = 1 / np.cos(np.radians(47.14))

kind = sys.argv[1]
truecol = kind == "truecolor"
ext = ZoomGrid.ext
OSM = osm_border()
FIRMS = pd.read_csv(data("firms", "firms_20261012.csv"), parse_dates=["t"])
FIRMS = FIRMS[FIRMS.t.dt.strftime("%m-%d") == "10-12"]

fig, axs = plt.subplots(3, 2, figsize=(7.2, 10.4), sharex=True, sharey=True, layout="constrained")
for ax, (sat, name, bands, t) in zip(axs.flat, SCENES):
    ax.imshow(rgb(tile("zoom", DAY, sat, TC if truecol else fc(sat))), extent=ext, aspect=asp, interpolation="nearest")
    plot_lines(ax, OSM, lw=1.6, **OSM_STYLE)
    if not truecol:
        p = FIRMS[FIRMS.t.dt.strftime("%H:%M") == t]
        cn = p.cty == "CHN"
        ax.scatter(p.longitude[~cn], p.latitude[~cn], s=34, facecolors="none", edgecolors="white", linewidths=1)
        ax.scatter(p.longitude[cn], p.latitude[cn], s=34, facecolors="none", edgecolors="cyan", linewidths=1.4)
    for x0, x1, y0, y1 in BOXES.values():
        ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec="magenta", lw=1.2, ls="--"))
    ax.set_xlim(view[0], view[1])
    ax.set_ylim(view[2], view[3])
    ax.set_xticks([119.65, 119.75, 119.85])
    ax.set_yticks([47.05, 47.10, 47.15, 47.20])
    deg_fmt(ax, "{:.2f}")
    ax.tick_params(labelsize=9)
    tl = local(utc(DAY, t))
    ax.set_title(
        T(f"{F}.panel", local=lang.hm(tl), sat=name, bands=T(f"{F}.true_colour") if truecol else bands), fontsize=10
    )
axs[1, 1].tick_params(labelbottom=True)
lg = axs.flat[-1]
lg.axis("off")
h = [
    Line2D([], [], lw=1.6, label=T(f"{F}.border_osm"), **OSM_STYLE),
    Line2D([], [], color="magenta", lw=1.2, ls="--", label=T(f"{F}.boxes")),
]
if not truecol:
    h += [
        Line2D([], [], ls="", marker="o", mfc="none", mec="white", mew=1, ms=7, label=T(f"{F}.firms_mng")),
        Line2D([], [], ls="", marker="o", mfc="none", mec="cyan", mew=1.4, ms=7, label=T(f"{F}.firms_east")),
    ]
lg.legend(
    handles=h, loc="center", fontsize=9, frameon=True, facecolor="0.4", edgecolor="none", labelcolor="w", framealpha=1
)
lg.text(0.5, 0.08, T(f"{F}.where", md=lang.md(tl)), ha="center", fontsize=9, transform=lg.transAxes)
fig.suptitle(T(f"{F}.title_{kind}", md=lang.md(tl)), fontsize=12)
save(fig, lang.out(f"{F}-{kind}"))
