"""gibs-wide-20261012: the five 10-12 true-colour GIBS daily mosaics over 44–50°N, 114–124°E (3 x 2, legend in the sixth cell)."""

import numpy as np
from matplotlib.lines import Line2D
from PIL import Image

from common import (
    BLOG_RC,
    TC,
    W_IN,
    init,
    line,
    local,
    map_axes,
    mark_arxan,
    ne_border,
    osm_border,
    plot_lines,
    save,
    tile,
    utc,
)

lang = init(__file__, BLOG_RC)
import matplotlib.pyplot as plt  # noqa: E402

T = lang.T
DAY = "2026-10-12"
SCENES = [
    ("MODIS_Terra", "Terra MODIS", "01:32"),
    ("VIIRS_NOAA20", "NOAA-20 VIIRS", "03:47"),
    ("VIIRS_NOAA21", "NOAA-21 VIIRS", "04:32"),
    ("VIIRS_SNPP", "S-NPP VIIRS", "05:10"),
    ("MODIS_Aqua", "Aqua MODIS", "06:35"),
]
ext = (114, 124, 44, 50)
asp = 1 / np.cos(np.radians(47))
OSM, NE = osm_border(), ne_border()

fig, axs = plt.subplots(
    3, 2, figsize=(W_IN, 8.8), gridspec_kw=dict(hspace=0.30, wspace=0.06, left=0.09, right=0.99, top=0.965, bottom=0.04)
)
for k, (sat, name, t) in enumerate(SCENES):
    ax = axs.flat[k]
    ax.imshow(Image.open(tile("wide", DAY, sat, TC)), extent=ext, aspect=asp)
    plot_lines(ax, OSM, **line(lang, "gibs-wide.osm"))
    plot_lines(ax, NE, **line(lang, "gibs-wide.ne"))
    mark_arxan(ax, T("gibs-wide.arxan"))
    map_axes(ax, ext, left=k % 2 == 0, bottom=k >= 3, xt=[116, 119, 122], yt=[45, 47, 49])
    tu = utc(DAY, t)
    ax.set_title(T("gibs-wide.panel", sat=name, local=lang.hm(local(tu)), utc=lang.hm(tu)))
lg = axs.flat[5]
lg.axis("off")
lg.legend(
    handles=[
        Line2D([], [], label=T("gibs-wide.border_osm"), **line(lang, "gibs-wide.osm", lw=1.4)),
        Line2D([], [], label=T("gibs-wide.border_ne"), **line(lang, "gibs-wide.ne", lw=1)),
        Line2D([], [], marker="s", ls="none", mfc="white", mec="black", label=T("gibs-wide.arxan")),
    ],
    loc="center",
    frameon=False,
    fontsize=10,
    title=T("gibs-wide.legend_title", md=lang.md(tu), ymd=lang.ymd(tu)),
    title_fontsize=10,
)
save(fig, lang.out("gibs-wide-20261012-v2"))
