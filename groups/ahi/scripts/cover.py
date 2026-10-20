"""cover: Himawari-9 true colour over the fire at 2026-10-12 06:00Z, B03-sharpened to 0.5 km,
regridded to a 1920 x 1080 lon/lat frame, no axes. Reads data/ahi/raw/ (B01-B04)."""

import glob
import warnings

import matplotlib.patheffects as pe
import numpy as np
import pandas as pd
from satpy import Scene
from scipy.interpolate import griddata

from common import RAW, lang, plt

warnings.filterwarnings("ignore")
lang.init(__file__)
tag = "20261012_0600"
s = Scene(reader="ahi_hsd", filenames=sorted(glob.glob(f"{RAW}/HS_H09_{tag}_B0[1-4]_*")))
s.load(["B01", "B02", "B03", "B04"])


def crop(b, f):
    r0, r1, c0, c1 = 470 * f, 700 * f, 1870 * f, 2200 * f
    lon, lat = s[b].attrs["area"].get_lonlats()
    return s[b].values[r0:r1, c0:c1] / 100.0, lon[r0:r1, c0:c1], lat[r0:r1, c0:c1]


r5, lon5, lat5 = crop("B03", 4)
b1 = crop("B01", 2)[0]
g2 = crop("B02", 2)[0]
n4 = crop("B04", 2)[0]
r1 = r5.reshape(r5.shape[0] // 2, 2, -1, 2).mean((1, 3))


def up(x):
    return np.repeat(np.repeat(x, 2, 0), 2, 1)


ratio = np.clip(r5 / np.maximum(up(r1), 1e-3), 0.6, 1.6)  # 0.5 km detail of B03 carried onto the 1 km bands
g = 0.85 * g2 + 0.15 * n4


def st(x, hi):
    x = np.clip((x - np.nanpercentile(x, 0.5)) / hi, 0, 1)
    return x ** (1 / 2.2)


rgb = np.nan_to_num(np.clip(np.dstack([st(r5, 0.45), st(up(g) * ratio, 0.45), st(up(b1) * ratio, 0.42)]), 0, 1))
XL = (116.8, 124.8)
kx = np.cos(np.radians(46.6))
hh = (XL[1] - XL[0]) * kx * 9 / 16 / 2
YL = (46.6 - hh, 46.6 + hh)
gx, gy = np.meshgrid(np.linspace(XL[0], XL[1], 1920), np.linspace(YL[1], YL[0], 1080))
ok = np.isfinite(lon5) & np.isfinite(lat5)
grid = np.dstack([griddata((lon5[ok], lat5[ok]), rgb[..., i][ok], (gx, gy), method="linear") for i in range(3)])
grid = np.clip(np.nan_to_num(grid), 0, 1)
fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.imshow(grid, extent=(XL[0], XL[1], YL[0], YL[1]), origin="upper", interpolation="lanczos", aspect=1 / kx)
ax.set_xlim(*XL)
ax.set_ylim(*YL)
ax.set_aspect(1 / kx)
ax.axis("off")
tl = pd.Timestamp(tag[:8] + tag[9:]) + pd.Timedelta(hours=8)
ax.text(
    0.995,
    0.01,
    lang.T("cover.stamp", mdhm=lang.mdhm(tl), ymd=lang.ymd(tl), hm=lang.hm(tl)),
    transform=ax.transAxes,
    ha="right",
    va="bottom",
    fontsize=10,
    color="white",
    alpha=0.9,
    path_effects=[pe.withStroke(linewidth=2, foreground="black")],
)
fig.savefig(lang.out("cover"), dpi=100)
