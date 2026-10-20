"""gibs-daily: GIBS daily mosaics 10-07..10-12, true colour (top row) and false colour (bottom row), three days per figure.

fig_gibs_daily.py a    -> gibs-daily-1007-1009-v2
fig_gibs_daily.py b    -> gibs-daily-1010-1012-v3
"""

import sys

import numpy as np
from PIL import Image

from common import (
    BLOG_RC,
    TC,
    W_IN,
    fc,
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
# day, (true-colour satellite, name, approx. overpass UTC), (false-colour satellite, name, approx. overpass UTC)
DAYS = [
    ("2026-10-07", ("VIIRS_NOAA20", "NOAA-20 VIIRS", "04:00"), ("VIIRS_NOAA20", "NOAA-20 VIIRS", "04:00")),
    ("2026-10-08", ("VIIRS_SNPP", "S-NPP VIIRS", "04:45"), ("VIIRS_SNPP", "S-NPP VIIRS", "04:45")),
    ("2026-10-09", ("MODIS_Terra", "Terra MODIS", "01:15"), ("VIIRS_NOAA20", "NOAA-20 VIIRS", "04:45")),
    ("2026-10-10", ("MODIS_Aqua", "Aqua MODIS", "05:00"), ("VIIRS_NOAA20", "NOAA-20 VIIRS", "04:25")),
    ("2026-10-11", ("MODIS_Aqua", "Aqua MODIS", "05:40"), ("VIIRS_SNPP", "S-NPP VIIRS", "03:50")),
    ("2026-10-12", ("MODIS_Terra", "Terra MODIS", "01:32"), ("MODIS_Terra", "Terra MODIS 7-2-1", "01:32")),
]
PARTS = {"a": (DAYS[:3], "gibs-daily-1007-1009-v2"), "b": (DAYS[3:], "gibs-daily-1010-1012-v3")}
ext = (118, 121, 46, 48)
asp = 1 / np.cos(np.radians(47))
OSM, NE = osm_border(), ne_border()

days, name = PARTS[sys.argv[1]]
fig, axs = plt.subplots(
    2, 3, figsize=(W_IN, 5.3), gridspec_kw=dict(hspace=0.26, wspace=0.06, left=0.16, right=0.99, top=0.92, bottom=0.06)
)
for j, (d, tcol, fcol) in enumerate(days):
    for i, ((sat, sname, t), bands) in enumerate([(tcol, TC), (fcol, fc(fcol[0]))]):
        ax = axs[i, j]
        ax.imshow(Image.open(tile("loc", d, sat, bands)), extent=ext, aspect=asp)
        plot_lines(ax, OSM, **line(lang, "gibs-daily.osm"))
        plot_lines(ax, NE, **line(lang, "gibs-daily.ne"))
        mark_arxan(ax, T("gibs-daily.arxan"))
        map_axes(ax, ext, left=j == 0, bottom=i == 1, xt=[118.5, 119.5, 120.5], yt=[46.5, 47, 47.5])
        tl = local(utc(d, t))
        ax.set_title(T("gibs-daily.panel", md=lang.md(tl), sat=sname, local=lang.hm(tl)))
axs[0, 0].set_ylabel(T("gibs-daily.true_colour"), fontsize=10, labelpad=6)
axs[1, 0].set_ylabel(T("gibs-daily.false_colour"), fontsize=10, labelpad=6)
save(fig, lang.out(name))
