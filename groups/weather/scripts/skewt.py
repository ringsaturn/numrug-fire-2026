"""skewt-20261013-2000-v2: the 2026-10-13 12Z ascents at Hailar, Xilinhot and Tongliao on skew-T
diagrams, 2×2 with the fourth cell holding the legend and each station's derived values.

Input: data/weather/xue-case/soundings.json (the archived xue sounding issue of 10-13 14Z;
xue_case.py). The diagram is case_plots.skewt from the xue repo at a larger type size.
"""

import json
import math
from datetime import timedelta

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from figkit import lang  # noqa: E402

lang.init(__file__)
import xue_case as C  # noqa: E402
from common import data  # noqa: E402

NAME = "skewt-20261013-2000-v2"
STATIONS = ["50527", "54102", "54135"]
TIME = "2026-10-13T12:00:00Z"
YLAB = [1000, 850, 700, 500, 400, 300, 250, 200, 150, 100]  # 925 left out of the labels only (crowded at 9 pt)
TICKS = [1000, 925, 850, 700, 500, 400, 300, 250, 200, 150, 100]


def T(key, **kw):
    return lang.T(f"{NAME}.{key}", **kw)


def skewt(ax, asc, title, skew=35.0):
    p, z, tt, td, wd, ws = C.profile(asc)
    X = lambda temp, pp: temp + skew * (np.log(1000) - np.log(pp))  # noqa: E731
    for T0 in range(-100, 60, 10):
        ax.plot([X(T0, 1000), X(T0, 100)], [np.log(1000), np.log(100)], color="0.85", lw=0.5, zorder=1)
    for th in range(250, 460, 20):
        pp = np.linspace(1000, 100, 50)
        ax.plot(X(th * (pp / 1000) ** 0.2857 - 273.15, pp), np.log(pp), color="#e8c9a0", lw=0.5, zorder=1)
    y = np.log(p)
    ax.plot(X(tt, p), y, color="#c0392b", lw=1.6, zorder=5, label=T("t"))
    ax.plot(X(td, p), y, color="#2e8b57", lw=1.6, zorder=5, label=T("td"))
    ax.set_yticks(np.log(YLAB))
    ax.set_yticklabels(YLAB, fontsize=9)
    ax.set_ylim(np.log(1050), np.log(100))
    ax.set_xlim(-40, 45)
    ax.set_xticks(range(-40, 50, 20))
    ax.set_xticklabels(range(-40, 50, 20), fontsize=9)
    sel = [i for i in range(len(p)) if not np.isnan(wd[i]) and not np.isnan(ws[i]) and (p[i] in TICKS or i % 6 == 0)]
    for i in sel:
        ang = math.radians(wd[i])
        sp = ws[i] * 1.944
        ax.barbs(
            [41],
            [y[i]],
            [-sp * math.sin(ang)],
            [-sp * math.cos(ang)],
            length=5,
            linewidth=0.7,
            color="0.2",
            zorder=6,
            clip_on=False,
        )
    ax.set_title(title, fontsize=10.5, pad=12)  # clear of the top barbs, which are drawn with clip_on=False


def value(v, unit=""):
    if v is None:
        return "—"
    return f"{lang.num(v)}{unit}" if isinstance(v, int) else f"{v}{unit}"


snd = json.loads(data("xue-case", "soundings.json").read_text())
fig, axs = plt.subplots(2, 2, figsize=(7.2, 7.4))
rows = []
for ax, w in zip(axs.flat, STATIONS):
    s = snd[w]
    a = C.ascent_at(s, TIME)
    name = T(f"station.{w}")
    skewt(ax, a, T("panel", name=name, wmo=w, lat=s["lat"], lon=s["lon"]))
    d = a.get("derived", {})
    rows.append(
        T(
            "values",
            name=name,
            pw=value(d.get("pw"), " mm"),
            fl=value(d.get("freezingLevel"), " m"),
            lr=value(d.get("lapse850_500"), " K/km"),
            tp=value(d.get("tropopause"), " m"),
        )
    )
for ax in axs[:, 0]:
    ax.set_ylabel("hPa", fontsize=9)
for ax in (axs[1, 0], axs[1, 1], axs[0, 1]):
    ax.set_xlabel(T("xlabel"), fontsize=9)
k = axs[1, 1]
k.axis("off")
h, l = axs[0, 0].get_legend_handles_labels()
k.legend(h, l, loc="upper left", fontsize=10, frameon=False, bbox_to_anchor=(0.0, 1.0))
k.text(0.0, 0.66, T("barbs"), fontsize=9.5, transform=k.transAxes)
k.text(0.0, 0.56, "\n".join(rows), fontsize=9.5, va="top", transform=k.transAxes, linespacing=1.5)
t = C.parse_time(TIME)
lt = t + timedelta(hours=8)
fig.suptitle(T("title", date=lang.ymd(lt), hm=lang.hm(lt), utc=lang.hm(t), utc_h=t.hour), fontsize=12)
fig.tight_layout()
fig.savefig(lang.out(NAME), dpi=200)
