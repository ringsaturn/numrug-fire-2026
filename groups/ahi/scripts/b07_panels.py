"""Eight panels of Himawari-9 B07 (3.9 um) brightness temperature with the hotspot outline.

usage: b07_panels.py key|evening
  key      ahi-b07-1008-1012-v3: key frames 10-08 to 10-12, Natural Earth border
  evening  ahi-b07-1012-evening-v2: 10-12 afternoon to night, OSM border
Reads data/ahi/ahi_b07_b14_crop.npz and ahi_hotmask.npz.
"""

import sys

import numpy as np
import pandas as pd

from common import CROP, MASK, border_lines, border_lines_osm, decorate, lang, plt

lang.init(__file__)
which = sys.argv[1]
SETS = {
    "key": (
        "ahi-b07-1008-1012-v3",
        border_lines,
        [
            "20261008_0440",
            "20261008_1700",
            "20261009_0400",
            "20261010_0500",
            "20261010_1010",
            "20261010_1200",
            "20261011_0500",
            "20261012_0440",
        ],
    ),
    "evening": (
        "ahi-b07-1012-evening-v2",
        border_lines_osm,
        [
            "20261012_0440",
            "20261012_0530",
            "20261012_0630",
            "20261012_0710",
            "20261012_0830",
            "20261012_0920",
            "20261012_1030",
            "20261012_1140",
        ],
    ),
}
name, borders, sel = SETS[which]
z = np.load(CROP)
m = np.load(MASK)["mask"]
tags = list(z["tags"])
lon, lat = z["lon"], z["lat"]
L = borders()
fs = lang.T("b07.font_size")
fig, axs = plt.subplots(4, 2, figsize=(7.2, 13.2), sharex=True, sharey=True, layout="constrained")
for ax, tg in zip(axs.flat, sel):
    i = tags.index(tg)
    b7 = z["b07"][i]
    t = pd.to_datetime(tg, format="%Y%m%d_%H%M") + pd.Timedelta(hours=8)
    pm = ax.pcolormesh(lon, lat, b7, cmap="inferno", vmin=270, vmax=360, shading="nearest", rasterized=True)
    ax.contour(lon, lat, m[i].astype(float), levels=[0.5], colors="cyan", linewidths=0.8)
    decorate(ax, L, (118.4, 120.6), (46.3, 47.85), color="w")
    ax.set_title(
        lang.T("b07.panel_title", time=lang.mdhm(t), label=lang.T(f"b07.{which}.{tg}")),
        fontsize=lang.T("b07.panel_title_size"),
    )
    ax.text(
        0.98,
        0.03,
        lang.T("b07.stats", n=int(m[i].sum()), bt=f"{np.nanmax(b7):.0f}"),
        transform=ax.transAxes,
        ha="right",
        fontsize=fs,
        color="w",
        bbox=dict(fc="k", alpha=0.5, ec="none"),
    )
    ax.set_xticks([118.5, 119.5, 120.5])
    ax.set_yticks([46.5, 47.0, 47.5])
    ax.tick_params(labelsize=fs)
    print(tg, int(m[i].sum()), round(float(np.nanmax(b7)), 1))
cb = fig.colorbar(pm, ax=axs, orientation="horizontal", shrink=0.8, pad=0.01, aspect=40, extend="both")
cb.set_label(lang.T("b07.cbar"), fontsize=fs)
cb.ax.tick_params(labelsize=fs)
fig.suptitle(lang.T(f"b07.{which}.title"), fontsize=12)
fig.savefig(lang.out(name), dpi=200)
