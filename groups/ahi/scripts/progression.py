"""ahi-front-progression: first AHI detection time of every 2 km pixel (pixels detected in
at least 2 frames) over update 1 (10-07 18:00Z to 10-12 04:40Z), with the 12-hour
hotspot-weighted centroid track. Reads data/ahi/ahi_hotmask.npz and ahi_hotspots_10min.csv.
"""

import matplotlib.dates as mdates
import matplotlib.patheffects as pe
import numpy as np
import pandas as pd

from common import HOTSPOTS, MASK, border_lines, date_formatter, decorate, fix_size, lang, plt, round_sel

lang.init(__file__)
out = lang.out("ahi-front-progression")
z = np.load(MASK)
sel = round_sel(z["tags"], "r1")
M = z["mask"][sel]
lon, lat = z["lon"], z["lat"]
TT = pd.to_datetime([str(t) for t in z["tags"][sel]], format="%Y%m%d_%H%M")
cnt = M.sum(0)
first = np.full(lon.shape, np.nan)
tn = mdates.date2num(TT + pd.Timedelta(hours=8))
for i in range(len(TT)):
    first[M[i] & np.isnan(first)] = tn[i]
ever = cnt >= 2  # detected in >= 2 frames: drops isolated noise
print("pixels detected in >= 2 frames:", int(ever.sum()))

d = pd.read_csv(HOTSPOTS, parse_dates=["time_utc"])
d = d[d.time_utc <= TT.max()]
dd = d[d.n_hot >= 3].copy()
dd["w"] = dd.n_hot
dd["wlat"] = dd.lat_c * dd.w
dd["wlon"] = dd.lon_c * dd.w
# 12 h windows 00:00-12:00 / 12:00-24:00 UTC+8 (= 16:00Z / 04:00Z), plotted at the window midpoint
g = dd.set_index("time_utc")[["wlat", "wlon", "w"]].resample("12h", offset="4h").sum()
g = g[g.w > 0]
h = pd.DataFrame(dict(lat_c=g.wlat / g.w, lon_c=g.wlon / g.w, n_hot=g.w))
h.index = h.index + pd.Timedelta(hours=6)

fig, ax = plt.subplots(figsize=(11, 8.2), layout="constrained")
ax.fill_between([118, 121], 46, 48, color="#f4f1ea")
o = np.argsort(-first[ever])
# colour scale from 10-08 12:00 UTC+8; computed as in the published script, whose rounding (4e-12 d below
# 12:00) decides which colour bin the frame times that fall exactly on a bin edge land in
vmin = tn.min() + mdates.date2num(pd.Timestamp("2026-10-08 12:00")) - tn.min()
sc = ax.scatter(
    lon[ever][o],
    lat[ever][o],
    c=first[ever][o],
    cmap="turbo",
    s=46,
    marker="s",
    edgecolor="none",
    vmin=vmin,
    vmax=tn.max(),
)
ax.plot(h.lon_c, h.lat_c, "-", color="k", lw=1.6, alpha=0.85)
ax.scatter(h.lon_c, h.lat_c, c="w", edgecolor="k", s=30, zorder=5)
# 10-09 06:00: the segments to 10-10 18:00 (up-right) and from 10-08 18:00 (lower right) leave only the left side free;
# 10-11 18:00: the segment from 10-10 18:00 arrives from the upper left, so that label goes below-left
OFFSET = {pd.Timestamp("2026-10-09 06:00"): (-5, 2, "right"), pd.Timestamp("2026-10-11 18:00"): (-5, -10, "right")}
for t, r in h.iterrows():
    tb = t + pd.Timedelta(hours=8)
    # a centroid with another one just to its right gets its label on the left
    left = ((h.lon_c - r.lon_c).between(0.01, 0.2) & ((h.lat_c - r.lat_c).abs() < 0.03)).any()
    dx, dy, ha = OFFSET.get(tb, (-5, 2, "right") if left else (4, 3, "left"))
    ax.annotate(
        lang.T("progression.track_label", mdhm=lang.mdhm(tb), d=tb.day, H=tb.hour, M=tb.minute),
        (r.lon_c, r.lat_c),
        fontsize=7.5,
        xytext=(dx, dy),
        textcoords="offset points",
        ha=ha,
        zorder=7,
        path_effects=[pe.withStroke(linewidth=2.5, foreground="white")],
    )
decorate(ax, border_lines(), (118.6, 120.2), (46.5, 47.6), color="k")
ax.text(119.0, 47.5, lang.T("map.mongolia"), fontsize=13, color="#555")
ax.text(119.95, 46.6, lang.T("map.china"), fontsize=13, color="#555")
cb = fig.colorbar(sc, ax=ax, shrink=0.8)
cb.ax.yaxis.set_major_locator(mdates.HourLocator(byhour=[0, 12]))
cb.ax.yaxis.set_major_formatter(date_formatter(lang.mdhm))
cb.set_label(lang.T("progression.cbar"))
ax.set_title(lang.T("progression.title"), fontsize=12)
ax.set_xlabel(lang.T("map.lon"))
ax.set_ylabel(lang.T("map.lat"))
fig.text(0.01, -0.02, lang.T("progression.footer"), fontsize=8, color="#555")
fig.savefig(out, dpi=150, bbox_inches="tight")
fix_size(out, 1653, 1280)
print(h.round(3).to_string())
