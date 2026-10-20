"""models-daily-20261013-2000: daily forecasts of four models at the fire (47.0°N 119.5°E), days
in Beijing time: minimum RH, maximum gust, wind direction at 14:00 and precipitation.

Solid: the runs of this report (10-13 06Z, served 10-13 14:14Z); dotted / crosses: the previous
report (served 10-13 05:34Z). Inputs: data/weather/om/models_20261013T1414Z.json and
models_20261013T0534Z.json (om_runs.py).
"""

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from figkit import lang  # noqa: E402

lang.init(__file__, figure="models-daily-20261013-2000")
from common import data, date_ticks  # noqa: E402

NAME = "models-daily-20261013-2000"
MODELS = {
    "ecmwf_ifs025": ("ECMWF", "#1f77b4"),
    "gfs_seamless": ("GFS", "#d62728"),
    "cma_grapes_global": ("CMA-GRAPES", "#2ca02c"),
    "icon_seamless": ("ICON", "#9467bd"),
}


def daily(name):
    h = pd.DataFrame(json.loads(data("om", f"{name}.json").read_text())[0]["hourly"])
    h["bj"] = pd.to_datetime(h.time) + pd.Timedelta(hours=8)
    h = h[(h.bj >= "2026-10-13") & (h.bj < "2026-10-22")]
    h["day"] = h.bj.dt.normalize()
    g = h.groupby("day")
    out = {}
    for m in MODELS:
        out[m] = pd.DataFrame(
            {
                "rh": g[f"relative_humidity_2m_{m}"].min(),
                "gust": g[f"wind_gusts_10m_{m}"].max(),
                "pr": g[f"precipitation_{m}"].sum(min_count=1),
            }
        )
        out[m]["dir"] = h[h.bj.dt.hour == 14].set_index("day")[f"wind_direction_10m_{m}"]
    return out


new, old = daily("models_20261013T1414Z"), daily("models_20261013T0534Z")
fig, ax = plt.subplots(4, 1, figsize=(11, 10), sharex=True)
for i, m in enumerate(MODELS):
    n, c = MODELS[m]
    a, o = new[m], old[m]
    off = pd.Timedelta(hours=-6 + 4 * i)
    ax[0].plot(a.index, a.rh, "-o", color=c, label=lang.T(f"{NAME}.this_report", model=n))
    ax[0].plot(o.index, o.rh, ":", color=c, alpha=0.6)
    ax[1].plot(a.index, a.gust, "-o", color=c)
    ax[1].plot(o.index, o.gust, ":", color=c, alpha=0.6)
    ax[2].plot(a.index + off, a.dir, "o", color=c, ms=7)
    ax[2].plot(o.index + off, o.dir, "x", color=c, alpha=0.6)
    ax[3].bar(a.index + off, a.pr, width=0.16, color=c)
ax[0].axhline(30, color="r", ls=":")
ax[0].set_ylabel(lang.T(f"{NAME}.rh"))
ax[0].legend(ncol=4, fontsize=8, title=lang.T(f"{NAME}.legend_title"), title_fontsize=8, loc="upper left")
ax[0].set_ylim(top=97)  # headroom so the legend sits above the curves (max 78 %)
ax[1].set_ylabel(lang.T(f"{NAME}.gust"))
ax[1].set_yticks(range(6, 19, 2))
ax[2].set_ylabel(lang.T(f"{NAME}.dir"))
ax[2].set_yticks([0, 90, 180, 270, 360])
ax[2].set_yticklabels([lang.T(f"{NAME}.compass.{k}") for k in ("n", "e", "s", "w", "n")])
ax[3].set_ylabel(lang.T(f"{NAME}.precip"))
for a in ax:
    a.grid(alpha=0.3)
ax[3].set_xlabel(lang.T("common.local_time_axis"))
ax[3].xaxis.set_major_formatter(date_ticks(f"{NAME}.tick"))
ax[0].set_title(lang.T(f"{NAME}.title"))
fig.tight_layout()
fig.savefig(lang.out(NAME), dpi=150)
