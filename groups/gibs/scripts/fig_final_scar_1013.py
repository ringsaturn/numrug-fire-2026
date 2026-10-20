"""final-scar-20261013: main patch vs all patches >= 5 km² on the two clearest 10-12 VIIRS scenes and on 10-13 Terra
(green < 75 and the green < 110 sensitivity run), 2 x 2, with the FY-4C hotspots ① and ③.

Contours and areas from scar/scar_masks.npz and scar/scar_areas.json (derive_scar.py).
"""

import json

import numpy as np
from matplotlib.lines import Line2D

from common import (
    BLOG_RC,
    W_IN,
    ZoomGrid,
    data,
    fc,
    init,
    line,
    local,
    map_axes,
    mark_arxan,
    osm_border,
    plot_lines,
    rgb,
    save,
    stroke,
    tile,
    utc,
)

lang = init(__file__, BLOG_RC)
import matplotlib.pyplot as plt  # noqa: E402

T = lang.T
F = "final-scar-20261013"
# (scene id in scar_areas.json, day, satellite, sensor name, overpass UTC, heading key)
PANELS = [
    ("20261012-noaa21", "2026-10-12", "VIIRS_NOAA21", "NOAA-21 VIIRS", "04:32", "head"),
    ("20261012-snpp", "2026-10-12", "VIIRS_SNPP", "S-NPP VIIRS", "05:10", "head"),
    ("20261013-terra", "2026-10-13", "MODIS_Terra", "Terra MODIS", "00:35", "head_g75"),
    ("20261013-terra-g110", "2026-10-13", "MODIS_Terra", "Terra MODIS", "00:35", "head_g110"),
]
FY4C = {"①": (119.84, 46.80), "③": (119.50, 47.32)}  # hotspots reported by the China Meteorological Administration
g = ZoomGrid()
asp = 1 / np.cos(np.radians(47))
J = json.load(open(data("scar", "scar_areas.json")))
M = np.load(data("scar", "scar_masks.npz"))
OSM = osm_border()

fig, axs = plt.subplots(
    2,
    2,
    figsize=(W_IN, 8.6),
    gridspec_kw=dict(hspace=T(f"{F}.hspace"), wspace=0.05, left=0.09, right=0.99, top=T(f"{F}.top"), bottom=0.12),
)
for k, (sid, day, sat, name, t, head) in enumerate(PANELS):
    ax = axs.flat[k]
    r = J[sid]
    tl = local(utc(day, t))
    ax.imshow(rgb(tile("zoom", day, sat, fc(sat))), extent=g.ext, aspect=asp)
    ax.contour(g.lon, g.lat, M[f"{sid}_all"].astype(float), [0.5], colors="cyan", linewidths=0.9)
    ax.contour(g.lon, g.lat, M[f"{sid}_main"].astype(float), [0.5], colors="magenta", linewidths=1.2)
    plot_lines(ax, OSM, **line(lang, f"{F}.osm"))
    for d in r["detached"]:
        if d["km2"] >= 5:
            ax.annotate(
                lang.num(d["km2"]),
                (d["lon"], d["lat"]),
                color="cyan",
                fontsize=9,
                ha="center",
                path_effects=stroke(),
                zorder=6,
            )
    for c, (x, y) in FY4C.items():
        ax.plot(x, y, marker="o", ms=10, mfc="none", mec="white", mew=1.6)
        ax.annotate(
            c, (x, y), xytext=(7, 4), textcoords="offset points", color="white", fontsize=10, path_effects=stroke()
        )
    mark_arxan(ax, T(f"{F}.arxan"), left=True)
    map_axes(ax, g.ext, left=k % 2 == 0, bottom=k >= 2, xt=[119, 119.5, 120], yt=[46.6, 47.0, 47.4])
    heading = T(f"{F}.{head}", md=lang.md(tl), sat=name, local=lang.hm(tl))
    ax.set_title(
        T(
            f"{F}.panel",
            head=heading,
            main=lang.num(r["area_main"]),
            all=lang.num(r["area_allcomp"]),
            outside=lang.num(r["china"]),
        )
    )
fig.legend(
    handles=[
        Line2D([], [], color="magenta", lw=1.4, label=T(f"{F}.main")),
        Line2D([], [], color="cyan", lw=1.2, label=T(f"{F}.all")),
        Line2D([], [], label=T(f"{F}.border_osm"), **line(lang, f"{F}.osm")),
        Line2D([], [], marker="o", ls="none", mfc="none", mec="black", label=T(f"{F}.fy4c")),
    ],
    loc="lower center",
    ncol=2,
    frameon=False,
    fontsize=9,
    bbox_to_anchor=(0.54, 0.0),
)
save(fig, lang.out(F + "-v2"))
