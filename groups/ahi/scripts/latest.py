"""Map of the AHI hotspot pixels in the last hours of an update: square size = number of
detections, colour = time of the last detection.

usage: latest.py r2|r3|r5 <figure name>
r2 and r3 show the last 3 hours of the update; r5 the whole new period after 10-13 05:10Z.
Reads data/ahi/ahi_hotmask.npz.
"""

import sys

import matplotlib.dates as mdates
import numpy as np
import pandas as pd

from common import ARXAN, MASK, border_lines_osm, date_formatter, decorate, fix_size, lang, plt, round_sel

lang.init(__file__)
rnd, name = sys.argv[1:3]
out = lang.out(name)
z = np.load(MASK)
s = round_sel(z["tags"], rnd)
M = z["mask"][s]
lon, lat = z["lon"], z["lat"]
TT = pd.to_datetime([str(t) for t in z["tags"][s]], format="%Y%m%d_%H%M")
t1 = TT.max()
t0 = pd.Timestamp("2026-10-13 05:10") if rnd == "r5" else t1 - pd.Timedelta(hours=3)
sel = np.nonzero((TT > t0) & (TT <= t1))[0]
last = np.full(lon.shape, np.nan)
cnt = np.zeros(lon.shape, int)
for i in sel:
    last[M[i]] = mdates.date2num(TT[i] + pd.Timedelta(hours=8))
    cnt += M[i]
ev = cnt > 0
fig, ax = plt.subplots(figsize=(11, 8.2), layout="constrained")
ax.fill_between([118, 121], 46, 48, color="#f4f1ea")
o = np.argsort(last[ev])
sc = ax.scatter(
    lon[ev][o],
    lat[ev][o],
    c=last[ev][o],
    s=20 + 12 * cnt[ev][o],
    marker="s",
    cmap="plasma",
    edgecolor="k",
    lw=0.3,
    vmin=mdates.date2num(t0 + pd.Timedelta(hours=8)),
    vmax=mdates.date2num(t1 + pd.Timedelta(hours=8)),
)
decorate(ax, border_lines_osm(), (118.8, 120.3), (46.5, 47.6), color="k")
th = np.linspace(0, 2 * np.pi, 200)
r = 15
ax.plot(
    ARXAN[0] + r / 111.2 / np.cos(np.radians(ARXAN[1])) * np.cos(th),
    ARXAN[1] + r / 111.2 * np.sin(th),
    ":",
    color="#555",
    lw=1,
)
ax.text(ARXAN[0] - 0.02, ARXAN[1] - 0.17, "15 km", fontsize=8, color="#555", ha="center")
ax.text(119.0, 47.5, lang.T("map.mongolia"), fontsize=13, color="#555")
ax.text(120.05, 46.65, lang.T("map.china"), fontsize=13, color="#555")
cb = fig.colorbar(sc, ax=ax, shrink=0.8)
if rnd == "r5":
    cb.ax.yaxis.set_major_locator(mdates.HourLocator(interval=1))
else:
    cb.ax.yaxis.set_major_locator(mdates.MinuteLocator(byminute=[0, 30]))
cb.ax.yaxis.set_major_formatter(date_formatter(lang.hm))
ta = t0 + pd.Timedelta(minutes=10) + pd.Timedelta(hours=8)
tb = t1 + pd.Timedelta(hours=8)
cb.set_label(lang.T("latest.cbar", md=lang.md(tb)))
ax.set_title(
    lang.T("latest.title", lead=lang.T(f"latest.lead_{rnd}"), start=lang.mdhm(ta), end=lang.hm(tb), n=len(sel)),
    fontsize=12,
)
ax.set_xlabel(lang.T("map.lon"))
ax.set_ylabel(lang.T("map.lat"))
fig.text(0.01, -0.02, lang.T("latest.footer"), fontsize=8, color="#555")
fig.savefig(out, dpi=150, bbox_inches="tight")
fix_size(out, 1653, 1280)
print(len(sel), "frames", int(ev.sum()), "pixels")
