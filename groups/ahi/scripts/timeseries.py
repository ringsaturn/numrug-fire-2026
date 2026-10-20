"""ahi-hotspots-20261013-2200: three-panel time series over the box 46.3-47.8 N, 118.4-120.4 E,
10-07 18:00Z to 10-13 14:00Z: AHI hotspot pixel count, sum of the BT7-BT14 excess and the
maximum BT7 every 10 min, with VIIRS detections and FRP per overpass on the right axes.
Reads data/ahi/ahi_hotspots_10min.csv and viirs_box.csv.
"""

import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from matplotlib.ticker import StrMethodFormatter

from common import BOX, HOTSPOTS, VIIRS_BOX, date_formatter, lang, plt

lang.init(__file__)
d = pd.read_csv(HOTSPOTS, parse_dates=["time_utc", "time_bjt"])
f = pd.read_csv(VIIRS_BOX, parse_dates=["t"])
f = f[f.latitude.between(*BOX["lat"]) & f.longitude.between(*BOX["lon"])]
f["pass"] = f.t.dt.floor("20min")
g = f.groupby(["pass", "src"]).agg(n=("frp", "size"), frp=("frp", "sum"), t=("t", "min")).reset_index()
g["bjt"] = g.t + pd.Timedelta(hours=8)
g = g[g.t >= "2026-10-07 18:00"]
COLS = {"SUOMI": "#1f77b4", "J1": "#2ca02c", "J2": "#9467bd"}
NAMES = {"SUOMI": "S-NPP", "J1": "NOAA-20", "J2": "NOAA-21"}
fs = lang.T("timeseries.legend_size")

fig, ax = plt.subplots(3, 1, figsize=(14, 9.5), sharex=True, gridspec_kw=dict(height_ratios=[1.3, 1, 1]))


def shade(a):
    """Grey bands over the night frames (solar zenith >= 85 deg)."""
    nd = d.day.values
    t = d.time_bjt.values
    i = 0
    while i < len(nd):
        if nd[i] == 0:
            j = i
            while j < len(nd) and nd[j] == 0:
                j += 1
            a.axvspan(t[i], t[min(j, len(nd) - 1)], color="#d0d4e4", alpha=0.45, lw=0)
            i = j
        else:
            i += 1


for a in ax:
    shade(a)
    a.grid(alpha=0.3)

a = ax[0]
a.plot(d.time_bjt, d.n_hot, color="#c0392b", lw=1.3, label=lang.T("timeseries.ahi_pixels"))
a.set_ylabel(lang.T("timeseries.ahi_pixels_axis"))
a2 = a.twinx()
for s, c in COLS.items():
    q = g[g.src == s]
    a2.scatter(
        q.bjt,
        q.n,
        s=36,
        marker="D",
        color=c,
        edgecolor="k",
        lw=0.4,
        zorder=5,
        label=lang.T("timeseries.viirs_count", sat=NAMES[s]),
    )
a2.set_ylabel(lang.T("timeseries.viirs_count_axis"))
h1, l1 = a.get_legend_handles_labels()
h2, l2 = a2.get_legend_handles_labels()
a.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=fs, framealpha=0.9)
a.set_title(lang.T("timeseries.title"), fontsize=12)

a = ax[1]
a.plot(d.time_bjt, d.dT_excess_sum, color="#e67e22", lw=1.2, label=lang.T("timeseries.dt_excess"))
a.set_ylabel(lang.T("timeseries.dt_excess_axis"))
a2 = a.twinx()
for s, c in COLS.items():
    q = g[g.src == s]
    a2.scatter(
        q.bjt,
        q.frp,
        s=30,
        marker="o",
        color=c,
        edgecolor="k",
        lw=0.4,
        zorder=5,
        label=lang.T("timeseries.viirs_frp", sat=NAMES[s]),
    )
a2.set_ylabel(lang.T("timeseries.viirs_frp_axis"))
h1, l1 = a.get_legend_handles_labels()
h2, l2 = a2.get_legend_handles_labels()
a.legend(h1 + h2, l1 + l2, loc="upper right", fontsize=fs, framealpha=0.9)

a = ax[2]
a.plot(d.time_bjt, d.bt7_max, color="#8e44ad", lw=1.1, label=lang.T("timeseries.bt7_max"))
sat = d[d.n_sat > 0]
a.scatter(sat.time_bjt, np.full(len(sat), 402), marker="v", s=14, color="k", label=lang.T("timeseries.saturated"))
a.set_ylabel(lang.T("timeseries.bt7_max_axis"))
a.set_ylim(260, 435)
a.legend(
    loc="upper left", ncol=2, fontsize=fs, framealpha=0.9
)  # one row above the 402 K saturation marks, covering no data
a.xaxis.set_major_locator(mdates.HourLocator(byhour=[0, 12]))
a.xaxis.set_minor_locator(mdates.HourLocator(byhour=range(0, 24, 3)))
a.xaxis.set_major_formatter(date_formatter(lambda t: lang.md(t) + "\n" + lang.hm(t)))
a.set_xlabel(lang.T("common.local_time_axis"))
a.set_xlim(d.time_bjt.min(), d.time_bjt.max())
for x in fig.axes:
    x.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
fig.text(0.01, 0.005, lang.T("timeseries.footer"), fontsize=7.5, color="#555")
fig.tight_layout(rect=(0, 0.03, 1, 1))  # room for the two-line footer
fig.savefig(lang.out("ahi-hotspots-20261013-2200"), dpi=150)
