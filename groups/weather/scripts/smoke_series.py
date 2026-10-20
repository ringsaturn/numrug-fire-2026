"""smoke-pm25-series: Hailar and Baicheng, observed PM2.5 (black) and CO (blue, right axis) against
GEFS-Aerosols surface PM2.5 from the run without this fire (dashed) and four runs with it.

Inputs: data/weather/aq/city_hourly.csv, data/weather/gefs-points/points.csv (bilinear at the city).
Beijing time (UTC+8) on the axis.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from figkit import lang  # noqa: E402

lang.init(__file__)
from common import data, date_ticks  # noqa: E402

NAME = "smoke-pm25-series"
H8 = pd.Timedelta(hours=8)
NO_FIRE_RUN = "2026100800"
PANELS = [
    ("Hailar", "2026-10-10 08:00", "2026-10-11 20:00", ["2026100912", "2026101000", "2026101012", "2026101100"]),
    ("Baicheng", "2026-10-12 00:00", "2026-10-13 12:00", ["2026101100", "2026101112", "2026101200", "2026101212"]),
]
COLORS = ["#fdae6b", "#f16913", "#d94801", "#7f2704"]


def run_label(key, run):
    t = pd.Timestamp(f"{run[:8]}T{run[8:]}")
    return lang.T(f"{NAME}.{key}", md=lang.md(t), h=t.hour)


obs = pd.read_csv(data("aq", "city_hourly.csv"), parse_dates=["time_bjt"])
pts = pd.read_csv(data("gefs-points", "points.csv"), parse_dates=["valid_utc"], dtype={"run": str})
pts["time_bjt"] = pts["valid_utc"] + H8

fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.6), constrained_layout=True)
for ax, (key, t0, t1, runs) in zip(axes, PANELS):
    t0, t1 = pd.Timestamp(t0), pd.Timestamp(t1)
    o = obs[(obs["city"] == key) & obs["time_bjt"].between(t0, t1)]
    p = pts[(pts["point"] == key) & pts["time_bjt"].between(t0, t1)]
    off = p[p["run"] == NO_FIRE_RUN]
    ax.plot(off["time_bjt"], off["pm25"], color="0.4", ls="--", lw=1.4, label=run_label("no_fire", NO_FIRE_RUN))
    for run, c in zip(runs, COLORS):
        r = p[p["run"] == run]
        ax.plot(r["time_bjt"], r["pm25"], color=c, lw=1.6, marker="o", ms=3, label=run_label("with_fire", run))
    ax.plot(o["time_bjt"], o["pm25"], color="k", lw=2.2, label=lang.T(f"{NAME}.observed"))
    ax.set_title(lang.T(f"{NAME}.panel", city=lang.T(f"{NAME}.city.{key}")), fontsize=10)
    ax.set_xlim(t0, t1)
    ax.xaxis.set_major_formatter(date_ticks(f"{NAME}.tick"))
    ax.xaxis.set_major_locator(mdates.HourLocator(byhour=[0, 6, 12, 18]))
    ax.tick_params(labelsize=9)
    ax.set_xlabel(lang.T("common.local_time_axis"), fontsize=9)
    ax.grid(alpha=0.3)
    top = max(p["pm25"].max(), o["pm25"].max())
    ax.set_ylim(0, top * 1.75)  # headroom: the legend sits above every curve
    tw = ax.twinx()
    tw.plot(o["time_bjt"], o["co"], color="tab:blue", lw=1.0, alpha=0.8)
    tw.set_ylabel(lang.T(f"{NAME}.co"), fontsize=9, color="tab:blue")
    tw.tick_params(labelsize=9, colors="tab:blue")
    tw.set_ylim(0, max(1.3, o["co"].max() * 1.15) * 1.6)  # the CO peak stays below the legend
    ax.legend(
        fontsize=lang.T(f"{NAME}.legend_size"),
        loc="upper left",
        framealpha=0.85,
        ncol=2,
        columnspacing=1.0,
        handlelength=1.6,
    )
fig.suptitle(lang.T(f"{NAME}.title"), fontsize=10)
fig.savefig(lang.out(NAME), dpi=150)
