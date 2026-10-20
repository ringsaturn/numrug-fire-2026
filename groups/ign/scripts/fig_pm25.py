"""pm25-hailar-baicheng-20261007-1014-v2: hourly city PM2.5 / PM10 / CO at Hulunbuir (Hailar) and Baicheng, 10-07..10-14,
with the peak windows whose back trajectories cross the fire area.

Input: data/ign/aq_hourly_long.csv (extract_aq.py). The series ends at 10-14 15:00 UTC+8, the last hour the mirror had
when the figure was first published. A catalog may set `mirror_as_published = true` to also drop the hours the mirror
lacked then (snapshot/pm25_published_missing.json), as the published Chinese figure shows.
"""

import datetime as dt
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import pandas as pd

from common import SNAPSHOT, data
from figkit import lang

lang.init(__file__)
K = "pm25-hailar-baicheng-20261007-1014-v2."
d = pd.read_csv(data("aq_hourly_long.csv"))
d = d[d.level == "city"]
d["t"] = pd.to_datetime(d.date_bjt.astype(str)) + pd.to_timedelta(d.hour_bjt, unit="h")
d = d[d.t <= pd.Timestamp("2026-10-14 15:00")]
if lang.T(K + "mirror_as_published"):
    for city, ts in json.load(open(SNAPSHOT / "pm25_published_missing.json")).items():
        d = d[~((d["where"] == city) & d.t.isin(pd.to_datetime(ts)))]
# (city column in the source, catalog key, peak window UTC+8, catalog fields of the satellite note)
C = [
    (
        "呼伦贝尔",
        "hailar",
        ("2026-10-11 07:00", "2026-10-11 11:00"),
        dict(t=lang.mdhm(dt.datetime(2026, 10, 11, 11, 52))),
    ),
    (
        "白城",
        "baicheng",
        ("2026-10-12 16:00", "2026-10-12 23:00"),
        dict(
            date=lang.md(dt.datetime(2026, 10, 12)),
            t1=lang.hm(dt.datetime(2026, 10, 12, 11, 33)),
            t2=lang.hm(dt.datetime(2026, 10, 12, 13, 12)),
        ),
    ),
]
fig, ax = plt.subplots(2, 1, figsize=(12, 7.5), sharex=True)
for a, (city, key, (t0, t1), kw) in zip(ax, C):
    q = d[d["where"] == city].pivot_table(index="t", columns="type", values="value")
    a.plot(q.index, q["PM2.5"], "-", c="#d62728", lw=1.6, label="PM2.5 µg/m³")
    a.plot(q.index, q["PM10"], "-", c="#ff9896", lw=1, label="PM10 µg/m³")
    b = a.twinx()
    b.plot(q.index, q["CO"], "-", c="#1f77b4", lw=1, label="CO mg/m³")
    b.set_ylabel("CO mg/m³", color="#1f77b4")
    a.axvspan(pd.Timestamp(t0), pd.Timestamp(t1), color="orange", alpha=0.25, label=lang.T(K + "peak"))
    a.set_title(lang.T(K + key, **kw), fontsize=10)
    a.set_ylabel("µg/m³")
    a.grid(alpha=0.3)
    a.legend(loc="upper left", fontsize=8)
    a.axvline(pd.Timestamp("2026-10-08 11:45"), c="k", ls=":", lw=1)
    a.text(
        pd.Timestamp("2026-10-08 12:30"),
        a.get_ylim()[1] * 0.92,
        lang.T(K + "ignition"),
        fontsize=8,
        path_effects=[pe.withStroke(linewidth=2.5, foreground="w")],
    )
if lang.T(K + "xlabel"):
    ax[1].set_xlabel(lang.T("common.local_time_axis"))
ax[1].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: lang.md(mdates.num2date(x))))
fig.suptitle(lang.T(K + "title"), fontsize=11)
fig.tight_layout()
fig.savefig(lang.out("pm25-hailar-baicheng-20261007-1014-v2"), dpi=140)
