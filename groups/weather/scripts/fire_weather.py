"""fire-weather-20261013: hourly temperature, dew point, precipitation, relative humidity and
10 m wind / gust at the fire (47.0°N 119.4°E), 10-08..10-21 Beijing time.

Input: data/weather/om/fire_weather_20261013T0528Z.json, the Open-Meteo forecast-API series as
served at 10-13 05:28Z (om_runs.py). The magenta line is the report time: before it the series
is the stitched model past, after it the forecast.
"""

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from figkit import lang  # noqa: E402

lang.init(__file__, figure="fire-weather-20261013")
from common import data, date_ticks  # noqa: E402

NAME = "fire-weather-20261013"
REPORT_TIME = pd.Timestamp("2026-10-13 13:45")  # Beijing time

h = json.loads(data("om", "fire_weather_20261013T0528Z.json").read_text())[0]
w = pd.DataFrame(h["hourly"])
w["bj"] = pd.to_datetime(w.time) + pd.Timedelta(hours=8)
w = w[(w.bj >= "2026-10-08") & (w.bj < "2026-10-22")]

fig, (b1, b2, b3) = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
b1.plot(w.bj, w.temperature_2m, "r-", label=lang.T(f"{NAME}.t2m"))
b1.plot(w.bj, w.dew_point_2m, "g-", label=lang.T(f"{NAME}.td"))
b1.legend(fontsize=8)
b1.set_ylabel("°C")
b1b = b1.twinx()
b1b.bar(w.bj, w.precipitation, width=0.04, color="b", alpha=0.5)
b1b.set_ylabel(lang.T(f"{NAME}.precip"), color="b")
b2.plot(w.bj, w.relative_humidity_2m, "k-")
b2.axhline(30, color="r", ls=":")
b2.set_ylabel(lang.T(f"{NAME}.rh"))
b3.plot(w.bj, w.wind_speed_10m, "k-", label=lang.T(f"{NAME}.wind"))
b3.plot(w.bj, w.wind_gusts_10m, "0.6", label=lang.T(f"{NAME}.gust"))
b3.set_ylabel("m/s")
b3.legend(fontsize=8, loc="lower left", ncol=2, framealpha=0.9)
q = w.iloc[::3]
u = -q.wind_speed_10m * np.sin(np.radians(q.wind_direction_10m))
v = -q.wind_speed_10m * np.cos(np.radians(q.wind_direction_10m))
b3.quiver(q.bj, np.full(len(q), 17), u, v, scale=120, width=0.002)
b3.set_ylim(-4.5, 20)  # room below 0 for the legend, clear of the curves and the arrows
b3.set_yticks(range(0, 21, 5))
for a in (b1, b2, b3):
    a.grid(alpha=0.3)
    a.axvline(REPORT_TIME, color="m", lw=1)
b3.xaxis.set_major_formatter(date_ticks(f"{NAME}.tick"))
b3.set_xlabel(lang.T(f"{NAME}.xlabel"))
b1.set_title(lang.T(f"{NAME}.title"), fontsize=11)
fig.tight_layout()
fig.savefig(lang.out(NAME), dpi=150)
