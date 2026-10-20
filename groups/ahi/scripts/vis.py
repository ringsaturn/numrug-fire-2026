"""Himawari-9 visible map: B03 0.64 um red band (0.5 km) above a B03/B02/B01 true-colour
composite (1 km), with the AHI hotspot outline of the same frame.

usage: vis.py r1|r2|r3|r5 <UTC tag> <figure name>
The update decides the border (r1 Natural Earth, later OSM), whether the true-colour
panel carries the outline (r2 on), and which segments are read: r1/r2 were drawn with
segment 2 only, so the top-right corner is empty as published.
"""

import glob
import sys
import warnings

import numpy as np
import pandas as pd
from satpy import Scene

from common import MASK, RAW, border_lines, border_lines_osm, decorate, fix_size, lang, plt

warnings.filterwarnings("ignore")
lang.init(__file__)
rnd, tag, name = sys.argv[1:4]
out = lang.out(name)
L = border_lines() if rnd == "r1" else border_lines_osm()
z = np.load(MASK)
mtags = list(z["tags"])
XL, YL = (118.0, 123.5), (46.0, 47.95)


def load(tag):
    fs = sorted(glob.glob(f"{RAW}/HS_H09_{tag}_B0[1-4]_*" + ("S0210*" if rnd in ("r1", "r2") else "")))
    s = Scene(reader="ahi_hsd", filenames=fs)
    s.load(["B01", "B02", "B03", "B04"])
    out = {}
    for b, f in [("B03", 4), ("B01", 2), ("B02", 2), ("B04", 2)]:
        r0, r1, c0, c1 = 540 * f, 640 * f, 1925 * f, 2175 * f
        lon, lat = s[b].attrs["area"].get_lonlats()
        out[b] = (s[b].values[r0:r1, c0:c1] / 100.0, lon[r0:r1, c0:c1], lat[r0:r1, c0:c1])
    return out


def stretch(x, lo=0.0, hi=1.0):
    x = np.clip((x - lo) / (hi - lo), 0, 1)
    return x ** (1 / 2.2)


d = load(tag)
t = pd.to_datetime(tag, format="%Y%m%d_%H%M")
tl = t + pd.Timedelta(hours=8)
hm = z["mask"][mtags.index(tag)]
fig, axs = plt.subplots(2, 1, figsize=(13, 10.5), layout="constrained")
v, lon, lat = d["B03"]
ax = axs[0]
ax.pcolormesh(lon, lat, stretch(v, 0.0, 0.6), cmap="gray", vmin=0, vmax=1, shading="nearest", rasterized=True)
ax.contour(z["lon"], z["lat"], hm.astype(float), levels=[0.5], colors="r", linewidths=0.8)
decorate(ax, L, XL, YL, color="yellow")
# a frame without detections draws no outline, so the key says so instead of naming one
ax.set_title(lang.T("vis.b03") + lang.T("vis.outline" if hm.any() else "vis.no_hotspots"), fontsize=11)
r = d["B03"][0].reshape(d["B03"][0].shape[0] // 2, 2, -1, 2).mean((1, 3))
b1, lon1, lat1 = d["B01"]
g = 0.85 * d["B02"][0] + 0.15 * d["B04"][0]
rgb = np.dstack([stretch(c - np.nanpercentile(c, 0.5), 0, hi) for c, hi in ((r, 0.45), (g, 0.45), (b1, 0.42))])
ax = axs[1]
qm = ax.pcolormesh(lon1, lat1, np.zeros(r.shape), shading="nearest", rasterized=True)
qm.set_array(None)
qm.set_facecolor(rgb.reshape(-1, 3))
if rnd != "r1":
    ax.contour(z["lon"], z["lat"], hm.astype(float), levels=[0.5], colors="r", linewidths=0.8)
decorate(ax, L, XL, YL, color="yellow")
ax.set_title(lang.T("vis.truecolour"), fontsize=11)
for ax in axs:
    ax.set_xticks(np.arange(118, 123.6, 0.5))
    ax.tick_params(labelsize=8)
when = lang.T("vis.time", ymd=lang.ymd(tl), hm=lang.hm(tl), md=lang.md(tl), ymd_utc=lang.ymd(t), hm_utc=lang.hm(t))
# without a hotspot there is no fire smoke to point at (10-13 06Z is all cumulus)
fig.suptitle(lang.T("vis.title_smoke" if hm.any() else "vis.title_plain", time=when), fontsize=13)
fig.text(
    0.01,
    -0.03,
    lang.T("vis.footer", border=lang.T("vis.border_ne" if rnd == "r1" else "vis.border_osm")),
    fontsize=8,
    color="#555",
)
fig.savefig(out, dpi=130, bbox_inches="tight")
plt.close(fig)
fix_size(out, 1448, 1429)
print(tag, out)
