"""border-gibs-20261013-{south,west-arxan}: burn-scar edge and OSM border on four GIBS scenes (three of 10-12, 10-13 Terra
with green < 110) for one border section, 2 x 2. Each panel title gives the burned area on the Chinese side of the line
inside the box of interest and its farthest distance from the line.

    fig_border_gibs.py south | west-arxan

Masks from scar/scar_masks.npz (derive_scar.py).
"""

import sys

import numpy as np
from matplotlib.lines import Line2D

from common import ARXAN, ZoomGrid, data, deg_fmt, fc, init, line, local, osm_border, plot_lines, rgb, save, tile, utc

lang = init(__file__)
import matplotlib.pyplot as plt  # noqa: E402

T = lang.T
F = "border-gibs-20261013"
# (mask id, day, satellite, overpass UTC, name key or literal)
SCENES = [
    ("20261012-noaa21", "2026-10-12", "VIIRS_NOAA21", "04:32", "NOAA-21 M11-I2-I1"),
    ("20261012-snpp", "2026-10-12", "VIIRS_SNPP", "05:10", "S-NPP M11-I2-I1"),
    ("20261012-aqua", "2026-10-12", "MODIS_Aqua", "06:35", "Aqua 7-2-1"),
    ("20261013-terra-g110", "2026-10-13", "MODIS_Terra", "00:35", None),
]
# zone: letter, view (W, E, S, N), box of interest, figure height (in), x ticks
ZONES = {
    "south": ("a", (119.30, 119.60, 46.56, 46.70), (119.36, 119.55, 46.58, 46.66), 6.4, [119.35, 119.45, 119.55]),
    "west-arxan": ("b", (119.62, 119.92, 47.00, 47.24), (119.74, 119.82, 47.10, 47.16), 10.2, [119.70, 119.80, 119.90]),
}

zone = sys.argv[1]
letter, view, box, H, xt = ZONES[zone]
g = ZoomGrid()
M = np.load(data("scar", "scar_masks.npz"))
OSM = osm_border()
sel = g.box(*box)
fig, axs = plt.subplots(2, 2, figsize=(7.2, H), sharex=True, sharey=True, layout="constrained")
for ax, (sid, day, sat, t, name) in zip(axs.flat, SCENES):
    m = M[f"{sid}_main"]
    ax.imshow(
        rgb(tile("zoom", day, sat, fc(sat))),
        extent=g.ext,
        aspect=1 / np.cos(np.radians((view[2] + view[3]) / 2)),
        interpolation="nearest",
    )
    ax.contour(g.lon, g.lat, m.astype(float), [0.5], colors="magenta", linewidths=1.4)
    plot_lines(ax, OSM, **line(lang, f"{F}.osm"))
    ax.add_patch(
        plt.Rectangle((box[0], box[2]), box[1] - box[0], box[3] - box[2], fill=False, ec="cyan", lw=1.4, ls=":")
    )
    outside = m & ~g.in_mng & sel
    A = g.area(outside)
    ys, xs = np.where(outside)
    dmax = float(g.dist_km(ys[::2], xs[::2]).max()) if len(ys) else 0
    ax.set_xlim(view[0], view[1])
    ax.set_ylim(view[2], view[3])
    deg_fmt(ax, "{:.2f}")
    ax.set_xticks(xt)
    ax.tick_params(labelsize=9)
    tl = local(utc(day, t))
    ax.set_title(
        T(
            f"{F}.panel",
            md=lang.md(tl),
            local=lang.hm(tl),
            sat=name or T(f"{F}.terra_g110"),
            area=lang.num(A, 1),
            dmax=lang.num(dmax, 1),
        ),
        fontsize=10,
    )
    if zone == "west-arxan":
        ax.plot(*ARXAN, marker="s", ms=6, mfc="white", mec="black")
    print(zone, sid, round(A, 1), round(dmax, 2))
h = [
    Line2D([], [], color="magenta", lw=1.4, label=T(f"{F}.scar_edge")),
    Line2D([], [], label=T(f"{F}.border_osm"), **line(lang, f"{F}.osm")),
    Line2D([], [], color="cyan", lw=1.4, ls=":", label=T(f"{F}.box")),
]
fig.legend(handles=h, loc="outside lower center", ncol=len(h), fontsize=9, frameon=False)
fig.suptitle(T(f"{F}.title", letter=letter, zone=T(f"{F}.zone_{zone}")), fontsize=12)
save(fig, lang.out(f"{F}-{zone}"))
