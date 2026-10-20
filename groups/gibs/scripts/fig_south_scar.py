"""south-scar-20261016: the separate scar south of the main fire, before (10-14 NOAA-20, clear) and after (10-16 NOAA-21)
on GIBS VIIRS false colour, with the three MODIS detections of 10-15 (Aqua 06:52Z, Terra 11:19Z x2) circled.

Border from border/border_osm_south.json (Overpass); the area of the scar is in scar/south_scar_20261016.json.
"""

import numpy as np
from PIL import Image

from common import BOXES, FC_VIIRS, init, line, local, osm_border_south, tile, utc

lang = init(__file__)
import matplotlib.pyplot as plt  # noqa: E402

T = lang.T
F = "south-scar-20261016"
W0, S0, E0, N0 = BOXES["south"][0]
PANELS = [("2026-10-14", "VIIRS_NOAA20", "NOAA-20", "before"), ("2026-10-16", "VIIRS_NOAA21", "NOAA-21", "after")]
MODIS_10_15 = [(46.49929, 119.51719), (46.4723, 119.58435), (46.459, 119.59129)]  # FIRMS MODIS C6.1, lat, lon
border = osm_border_south()

fig, axs = plt.subplots(1, 2, figsize=(12, 4.2), dpi=150)
for ax, (day, sat, name, key) in zip(axs, PANELS):
    im = Image.open(tile("south", day, sat, FC_VIIRS)).convert("RGB")
    ax.imshow(im, extent=(W0, E0, S0, N0), aspect=1 / np.cos(np.radians(46.5)))
    for p in border:
        a = np.array(p)
        if len(a) > 1:
            ax.plot(a[:, 0], a[:, 1], **line(lang, f"{F}.osm"))
    for y, x in MODIS_10_15:
        ax.plot(x, y, "o", mfc="none", mec="cyan", ms=10, mew=1.5)
    ax.set_xlim(W0, E0)
    ax.set_ylim(S0, N0)
    ax.set_title(T(f"{F}.{key}", md=lang.md(local(utc(day, "12:00"))), sat=name), fontsize=11)
    ax.tick_params(labelsize=8)
axs[0].text(119.35, 46.70, T(f"{F}.mongolia"), color="w", fontsize=10)
axs[0].text(119.75, 46.34, T(f"{F}.china"), color="w", fontsize=10)
fig.tight_layout()
fig.savefig(lang.out(F))
print(lang.out(F))
