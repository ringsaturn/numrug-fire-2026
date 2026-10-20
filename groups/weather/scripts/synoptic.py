# Adapted from github.com/ringsaturn/xue, .agents/skills/synoptic-analysis/scripts/case_plots.py
# (MIT OR Apache-2.0, © 2026 Han Xiao): setmap, barbs, fig_upper, fig_surface and fig_meteogram,
# with the text moved into the catalogs and this case's layout fixes applied in place.
"""upper-20261013-2000, surface-20261013-2000 and meteogram-20261013-2000 from data/weather/xue-case/.

- upper: 500 hPa height and the 250 hPa jet, ECMWF 10-13 00Z and GFS 10-13 06Z, at 10-13 and 10-17 20:00 UTC+8.
- surface: sea-level pressure, 10 m wind and rain rate, same runs and times.
- meteogram: sea-level pressure, wind and gust, rain rate and accumulation at the fire from
  ECMWF, GFS, IFS HRES and AIFS.

    synoptic.py upper|surface|meteogram
"""

import json
import math
import sys
from datetime import timedelta, timezone

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402
from PIL import Image  # noqa: E402

from figkit import lang  # noqa: E402

lang.init(__file__)
plt.rcParams["figure.dpi"] = 130
import xue_case as C  # noqa: E402
from common import data, date_ticks  # noqa: E402

TZ_H = 8
TZ = timezone(timedelta(hours=TZ_H))
SPAN = ("2026-10-13T12Z", "2026-10-21T00Z")  # meteogram x limits
RAIN_LEVELS = [0.5, 1, 2, 5, 10, 20, 40, 80]
RAIN_COLORS = ["#d9f0ff", "#a6d8ff", "#66b3ff", "#2a80ff", "#ffe066", "#ff9d1a", "#e0261c", "#8e0d8e"]
MODEL_COLORS = {"gfs": "#c0392b", "ecmwf": "#1f5fbf", "ifshres": "#2e8b57", "aifs": "#8e0d8e"}
MODEL_NAMES = {"gfs": "GFS", "ecmwf": "ECMWF IFS", "ifshres": "IFS HRES", "aifs": "AIFS"}
# The maps are saved with a tight bounding box, then padded with white to the published size,
# so every language comes out at the same pixel size.
PAD = {"upper": (1106, 970), "surface": (1124, 1043)}
NAMES = {"upper": "upper-20261013-2000", "surface": "surface-20261013-2000", "meteogram": "meteogram-20261013-2000"}

CASE = data("xue-case")
META = json.loads((CASE / "meta.json").read_text())


def T(key, **kw):
    return lang.T(f"synoptic.{key}", **kw)


def local(t):
    return T("local", t=lang.mdhm(C.parse_time(t).astimezone(TZ)))


def run_label(src):
    run = META["runs"][src].split(".")[1]
    return f"{MODEL_NAMES[src]} {run[:8]}/{run[8:10]}Z"


def load_coast():
    lines = []
    for feat in json.loads(data("base", "ne_50m_coastline.geojson").read_text())["features"]:
        geom = feat["geometry"]
        for ln in geom["coordinates"] if geom["type"] == "MultiLineString" else [geom["coordinates"]]:
            lines.append(np.asarray(ln))
    return lines


def setmap(ax, box, coast, title, marks):
    s, n, w, e = box
    for a in coast:
        if a[:, 0].max() < w - 5 or a[:, 0].min() > e + 5 or a[:, 1].max() < s - 5 or a[:, 1].min() > n + 5:
            continue
        ax.plot(a[:, 0], a[:, 1], color="0.25", lw=0.6, zorder=5)
    ax.set_xlim(w, e)
    ax.set_ylim(s, n)
    ax.set_aspect(1 / math.cos(math.radians((s + n) / 2)))
    step = 5 if e - w <= 40 else 10
    ax.set_xticks(np.arange(math.ceil(w / step) * step, e + 0.1, step))
    ax.set_yticks(np.arange(math.ceil(s / step) * step, n + 0.1, step))
    ax.set_xticklabels([f"{int(x)}°E" for x in ax.get_xticks()], fontsize=7)
    ax.set_yticklabels([f"{int(y)}°N" for y in ax.get_yticks()], fontsize=7)
    ax.grid(True, lw=0.3, color="0.7", alpha=0.6)
    for lat, lon in marks:
        ax.plot(lon, lat, marker="*", ms=11, color="gold", mec="k", mew=0.8, zorder=12)
    ax.set_title(title, fontsize=9)


def barbs(ax, lon, lat, u, v, st, **kw):
    ax.barbs(
        lon[::st],
        lat[::st],
        u[::st, ::st] * 1.944,
        v[::st, ::st] * 1.944,
        length=kw.pop("length", 4.2),
        linewidth=kw.pop("linewidth", 0.4),
        color=kw.pop("color", "0.3"),
        zorder=6,
        **kw,
    )


def pad(path, size):
    im = Image.open(path).convert("RGB")
    W, H = size
    if im.width > W or im.height > H:
        raise SystemExit(f"{path}: {im.width}x{im.height} is larger than the published {W}x{H}; shorten the text")
    out = Image.new("RGB", (W, H), "white")
    out.paste(im, ((W - im.width) // 2, (H - im.height) // 2))
    out.save(path)


def fields():
    f = np.load(CASE / "fields.npz")
    return lambda src, b, v, t: (f[f"{src}:{b}:{v}:{t}"], f[f"{src}:{b}:lat"], f[f"{src}:{b}:lon"])


def map_title(src, t):
    return f"{run_label(src)}\n{T('valid', t=local(t))}"


def fig_upper(out):
    fld, coast, box, times, marks = fields(), load_coast(), META["box"], META["times"], [tuple(META["point"])]
    srcs = META["sources"]
    fig, axs = plt.subplots(len(srcs), len(times), figsize=(5.5 * len(times), 4.1 * len(srcs)), squeeze=False)
    for i, src in enumerate(srcs):
        for j, t in enumerate(times):
            ax = axs[i, j]
            z, lat, lon = fld(src, "hgt500", "hgt500", t)
            u, _, _ = fld(src, "wind250", "ugrd250", t)
            v, _, _ = fld(src, "wind250", "vgrd250", t)
            setmap(ax, box, coast, map_title(src, t), marks)
            cf = ax.contourf(
                lon,
                lat,
                np.hypot(u, v),
                levels=[30, 40, 50, 60, 70, 80],
                cmap="Purples",
                alpha=0.75,
                extend="max",
                zorder=1,
            )
            cs = ax.contour(lon, lat, z, levels=np.arange(4800, 6040, 40), colors="k", linewidths=0.6, zorder=6)
            ax.clabel(cs, fmt="%d", fontsize=6)
            ax.contour(lon, lat, z, levels=[5880], colors="#c0392b", linewidths=1.6, zorder=7)
            barbs(ax, lon, lat, u, v, max(1, len(lon) // 20))
    fig.colorbar(cf, ax=axs, shrink=0.6, label=T("jet"), pad=0.02)
    fig.suptitle(lang.T("upper-20261013-2000.title"), fontsize=10)
    fig.savefig(out, bbox_inches="tight")
    pad(out, PAD["upper"])


def fig_surface(out):
    fld, coast, box, times, marks = fields(), load_coast(), META["box"], META["times"], [tuple(META["point"])]
    cm = ListedColormap(RAIN_COLORS)
    norm = BoundaryNorm(RAIN_LEVELS, cm.N)
    srcs = META["sources"]
    s_, n, w, e = box
    fig, axs = plt.subplots(len(srcs), len(times), figsize=(5.5 * len(times), 4.5 * len(srcs)), squeeze=False)
    for i, src in enumerate(srcs):
        for j, t in enumerate(times):
            ax = axs[i, j]
            p, lat, lon = fld(src, "prmsl", "prmsl", t)
            u, _, _ = fld(src, "wind10m", "ugrd10m", t)
            v, _, _ = fld(src, "wind10m", "vgrd10m", t)
            setmap(ax, box, coast, map_title(src, t), marks)
            r, _, _ = fld(src, "prate", "prate", t)
            cf = ax.contourf(lon, lat, r, levels=RAIN_LEVELS, cmap=cm, norm=norm, extend="max", zorder=1)
            cs = ax.contour(lon, lat, p, levels=np.arange(900, 1060, 4), colors="k", linewidths=0.6, zorder=6)
            ax.clabel(cs, fmt="%d", fontsize=6)
            barbs(ax, lon, lat, u, v, max(1, len(lon) // 22), color="0.2")
            # The low centre: "L" and its value, kept inside the frame, the value a little below the
            # L and under it, each with a white halo.
            ii, kk = np.unravel_index(np.nanargmin(p), p.shape)
            x = min(max(lon[kk], w + 0.9), e - 0.9)
            for txt, y, kw in (
                ("L", lat[ii], dict(fontsize=13, fontweight="bold", va="center", zorder=13, lw=2.5)),
                (f"{p[ii, kk]:.0f}", lat[ii] - (n - s_) / 20 - 0.35, dict(fontsize=7, zorder=12, lw=1.5)),
            ):
                lw = kw.pop("lw")
                ax.text(
                    x,
                    min(max(y, s_ + 0.6), n - 0.6),
                    txt,
                    color="#c0392b",
                    ha="center",
                    **kw,
                    path_effects=[pe.withStroke(linewidth=lw, foreground="white")],
                )
            # 10 m wind >= 17.2 m/s, thick and haloed: it only occurs in small patches at the map edge.
            c17 = ax.contour(
                lon, lat, np.hypot(u, v), levels=[17.2], colors="#c0392b", linewidths=1.0, linestyles="--", zorder=7
            )
            c17.set_linewidth(2.4)
            c17.set_path_effects([pe.Stroke(linewidth=4.0, foreground="white"), pe.Normal()])
    fig.colorbar(cf, ax=axs, shrink=0.6, label=T("rain"), pad=0.02)
    fig.suptitle(lang.T("surface-20261013-2000.title"), fontsize=10)
    fig.savefig(out, bbox_inches="tight")
    pad(out, PAD["surface"])


def fig_meteogram(out):
    K = "meteogram-20261013-2000"
    pt = np.load(CASE / "point.npz")
    lat, lon = META["point"]
    fig, axs = plt.subplots(4, 1, figsize=(10, 10.5), sharex=True)
    for src in META["point_sources"]:
        fr = C.point_frame(pt, src, TZ_H)
        col = MODEL_COLORS[src]
        lab = run_label(src)
        t = fr["t"]
        axs[0].plot(t, fr["p"], color=col, lw=1.4, label=lab)
        axs[1].plot(t, fr["ws"], color=col, lw=1.4, label=lab + lang.T(f"{K}.w10"))
        axs[1].plot(t, fr["gust"], color=col, lw=1.0, ls="--", label=lab + lang.T(f"{K}.gust"))
        axs[2].plot(t, fr["rate"], color=col, lw=1.4, label=lab, drawstyle="steps-post")
        axs[3].plot(t, C.accumulate(t, fr["rate"]), color=col, lw=1.4, label=lab)
    for ax, key in zip(axs, ("mslp", "wind", "rate", "accum")):
        ax.set_ylabel(lang.T(f"{K}.{key}"))
    box = dict(fc="white", ec="none", alpha=0.8, pad=1)
    axs[1].axhline(17.2, color="0.4", lw=0.6, ls=":")
    axs[1].text(
        0.995,
        17.6,
        lang.T(f"{K}.gale"),
        fontsize=7,
        color="0.3",
        ha="right",
        bbox=box,
        transform=axs[1].get_yaxis_transform(),
    )
    axs[1].axhline(10.8, color="0.6", lw=0.6, ls=":")
    axs[1].text(
        0.995,
        11.2,
        lang.T(f"{K}.strong"),
        fontsize=7,
        color="0.4",
        ha="right",
        bbox=box,
        transform=axs[1].get_yaxis_transform(),
    )
    for ax in axs:
        ax.grid(True, lw=0.3, alpha=0.6)
        if ax is axs[1]:
            # no legend entry for a series that has no data (AIFS has no gust)
            h, labels = ax.get_legend_handles_labels()
            keep = [(hh, ll) for hh, ll in zip(h, labels) if np.isfinite(np.asarray(hh.get_ydata(), dtype=float)).any()]
            ax.legend([k[0] for k in keep], [k[1] for k in keep], fontsize=7, loc="upper left", ncol=2)
        else:
            ax.legend(fontsize=7, loc="upper left")
    axs[0].set_title(lang.T(f"{K}.title", name=lang.T(f"{K}.point_name"), lat=lat, lon=lon), fontsize=9)
    axs[3].xaxis.set_major_formatter(date_ticks(f"{K}.tick", tz=TZ))
    axs[3].xaxis.set_major_locator(mdates.DayLocator(tz=TZ))
    # Two layout passes, as the published figure was made: the first, with case_plots' slanted
    # tick labels, free y labels and automatic wind limits, sets the margins; the second fits the
    # final labels into them.
    plt.setp(axs[3].get_xticklabels(), rotation=45, ha="right", fontsize=7)
    axs[3].set_xlim(*(C.parse_time(x).astimezone(TZ) for x in SPAN))
    fig.tight_layout()
    axs[1].set_ylim(top=31)  # headroom: the wind legend sits above the curves
    plt.setp(axs[3].get_xticklabels(), rotation=0, ha="center")
    for ax in axs:
        ax.yaxis.set_label_coords(-0.06, 0.5)  # one column for all y labels, so a two-line label stays in its panel
    axs[3].set_xlabel(lang.T("common.local_time_axis"), fontsize=8)
    fig.tight_layout()
    fig.savefig(out)


if __name__ == "__main__":
    which = sys.argv[1]
    {"upper": fig_upper, "surface": fig_surface, "meteogram": fig_meteogram}[which](lang.out(NAMES[which]))
