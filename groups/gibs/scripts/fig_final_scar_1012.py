"""final-scar-20261012: burned area on the five 10-12 GIBS false-colour scenes (2 x 3, summary in the sixth cell).

Contours and areas from scar/scar_masks.npz and scar/scar_areas.json (derive_scar.py).
"""

import json

import numpy as np
from matplotlib.lines import Line2D

from common import (
    BLOG_RC,
    NE_STYLE,
    OSM_STYLE,
    W_IN,
    ZoomGrid,
    data,
    fc,
    init,
    local,
    map_axes,
    mark_arxan,
    ne_border,
    osm_border,
    plot_lines,
    rgb,
    save,
    tile,
    utc,
)

lang = init(__file__, BLOG_RC)
import matplotlib.pyplot as plt  # noqa: E402

T = lang.T
DAY = "2026-10-12"
SCENES = [
    ("20261012-terra", "MODIS_Terra", "Terra MODIS 7-2-1", "01:32"),
    ("20261012-noaa20", "VIIRS_NOAA20", "NOAA-20 VIIRS", "03:47"),
    ("20261012-noaa21", "VIIRS_NOAA21", "NOAA-21 VIIRS", "04:32"),
    ("20261012-snpp", "VIIRS_SNPP", "S-NPP VIIRS", "05:10"),
    ("20261012-aqua", "MODIS_Aqua", "Aqua MODIS 7-2-1", "06:35"),
]
g = ZoomGrid()
asp = 1 / np.cos(np.radians(47))
J = json.load(open(data("scar", "scar_areas.json")))
M = np.load(data("scar", "scar_masks.npz"))
OSM, NE = osm_border(), ne_border()

fig, axs = plt.subplots(
    2,
    3,
    figsize=(W_IN, 5.9),
    gridspec_kw=dict(
        hspace=T("final-scar-20261012.hspace"),
        wspace=0.06,
        left=0.085,
        right=0.99,
        top=T("final-scar-20261012.top"),
        bottom=0.05,
    ),
)
for k, (sid, sat, name, t) in enumerate(SCENES):
    ax = axs.flat[k]
    ax.imshow(rgb(tile("zoom", DAY, sat, fc(sat))), extent=g.ext, aspect=asp)
    ax.contour(g.lon, g.lat, M[f"{sid}_main"].astype(float), levels=[0.5], colors="magenta", linewidths=1.0)
    plot_lines(ax, OSM, lw=1.2, **OSM_STYLE)
    plot_lines(ax, NE, lw=0.8, **NE_STYLE)
    mark_arxan(ax, T("final-scar-20261012.arxan"), left=True)
    map_axes(ax, g.ext, left=k % 3 == 0, bottom=k >= 2, xt=[119, 119.5, 120], yt=[46.6, 47.0, 47.4])
    r = J[sid]
    ax.set_title(
        T(
            "final-scar-20261012.panel",
            sat=name,
            local=lang.hm(local(utc(DAY, t))),
            area=lang.num(r["area_main"]),
            outside=lang.num(r["china"]),
        ),
        fontsize=T("final-scar-20261012.title_size"),
    )
sm = J["summary_20261012"]
lg = axs.flat[5]
lg.axis("off")
lg.legend(
    handles=[
        Line2D([], [], color="magenta", lw=1.4, label=T("final-scar-20261012.scar")),
        Line2D([], [], lw=1.4, label=T("final-scar-20261012.border_osm"), **OSM_STYLE),
        Line2D([], [], lw=1, label=T("final-scar-20261012.border_ne"), **NE_STYLE),
    ],
    loc="center",
    frameon=False,
    fontsize=9.5,
    title_fontsize=10,
    title=T(
        "final-scar-20261012.summary", min=lang.num(sm["min"]), max=lang.num(sm["max"]), median=lang.num(sm["median"])
    ),
)
save(fig, lang.out("final-scar-20261012-v3"))
