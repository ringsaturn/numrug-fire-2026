"""firms-timeseries-20261013: per-overpass total FRP, fire-pixel count and east/west edge longitude of the
detections in 46.3-47.9°N, 118.3-120.6°E, 10-08 to 10-13 morning (r3 overpass table)."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from common import BJ, D
from figkit import lang

lang.init(__file__)
C = "firms-timeseries-20261013."
NAMES = {"SUOMI": "S-NPP VIIRS", "J1": "NOAA-20 VIIRS", "J2": "NOAA-21 VIIRS", "MODIS": "Terra/Aqua MODIS"}
COLS = {"SUOMI": "#1b9e77", "J1": "#d95f02", "J2": "#7570b3", "MODIS": "#e7298a"}

p = pd.read_csv(D / "passes_r3.csv", parse_dates=["t"])
p["bj"] = p.t + BJ
fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(11, 8.5), sharex=True)
for s, q in p.groupby("src"):
    a1.plot(q.bj, q.frp / 1000, "o", color=COLS[s], label=NAMES[s])
    a2.plot(q.bj, q.n, "o", color=COLS[s])
    a3.plot(q.bj, q.E, "^", color=COLS[s])
    a3.plot(q.bj, q.W, "v", color=COLS[s], mfc="none")
a1.set_ylabel(lang.T(C + "frp"))
a1.legend(fontsize=8, ncol=4, title=lang.T(C + "legend_title"), title_fontsize=8)
a2.set_ylabel(lang.T(C + "pixels"))
a2.set_yscale("log")
a3.axhline(119.93, color="k", ls=":")
a3.annotate(
    lang.T(C + "border_east"),
    (p.bj.min(), 119.93),
    xytext=(0, -5),
    textcoords="offset points",
    va="top",
    fontsize=8,
    bbox=dict(fc="white", ec="none", alpha=0.85, pad=1),
)
a3.set_ylabel(lang.T(C + "edges"))
for a in (a1, a2, a3):
    a.grid(alpha=0.3)
a3.xaxis.set_major_formatter(mdates.DateFormatter(lang.T(C + "tick_fmt")))
a3.set_xlabel(lang.T("common.local_time_axis"))
a1.set_title(lang.T(C + "title"))
fig.tight_layout()
fig.savefig(lang.out("firms-timeseries-20261013"), dpi=150)
