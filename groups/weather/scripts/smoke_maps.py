"""smoke-pm25-maps: GEFS-Aerosols surface PM2.5 (shading) with observed city PM2.5 (dots, same
colour scale) and the fire (red star).

Rows are valid times, columns runs; the 10-08 00Z run predates this fire, so it is the run
without it. Inputs: data/weather/gefs/<run>/fFFF.grib2 (band 4), data/weather/aq/city_hourly.csv,
data/weather/base/ (Natural Earth lines).

    smoke_maps.py [VALID:RUN,RUN,... ...]    # VALID and RUN as YYYYmmddHH UTC
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402

from figkit import lang  # noqa: E402

lang.init(__file__)
from common import data  # noqa: E402

NAME = "smoke-pm25-maps"
ROWS = ["2026101100:2026100800,2026101012,2026101100", "2026101212:2026100800,2026101100,2026101200"]
NO_FIRE_RUN = "2026100800"
EXTENT = (114.0, 127.0, 43.0, 50.5)
LEVELS = [0, 5, 10, 15, 25, 35, 50, 75, 115, 150, 250, 400]
CMAP = ListedColormap(plt.get_cmap("YlOrBr")(np.linspace(0.05, 1, len(LEVELS) - 1)))
NORM = BoundaryNorm(LEVELS, CMAP.N)
CITIES = {
    "Hailar": (119.74, 49.19),
    "Baicheng": (122.83, 45.59),
    "Qiqihar": (123.89, 47.30),
    "Tongliao": (122.27, 43.64),
    "Songyuan": (124.80, 45.15),
    "Xilinhot": (116.09, 43.93),
    "Ulanhot": (122.06, 46.07),
}
FIRE = (119.45, 47.05)


def label_place(key):
    """Each label sits next to its own dot and never crosses the panel frame: up-right by default;
    Baicheng and Tongliao to the left, Songyuan below and Qiqihar above (east edge, close together)."""
    if key in ("Baicheng", "Tongliao"):
        return (-10, 0), "right", "center"
    if key == "Songyuan":
        return (lang.T(f"{NAME}.songyuan_dx"), -9), "center", "top"
    if key == "Qiqihar":
        return (0, 9), "center", "bottom"
    return (7, 5), "left", "bottom"


def lines(path):
    out = []
    for feat in json.loads(Path(path).read_text())["features"]:
        g = feat["geometry"]
        parts = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
        for p in parts:
            a = np.asarray(p)
            if (
                (a[:, 0] > EXTENT[0] - 5)
                & (a[:, 0] < EXTENT[1] + 5)
                & (a[:, 1] > EXTENT[2] - 5)
                & (a[:, 1] < EXTENT[3] + 5)
            ).any():
                out.append(a)
    return out


ADM0 = lines(data("base", "ne_50m_admin_0_boundary_lines_land.geojson"))
ADM1 = lines(data("base", "ne_50m_admin_1_states_provinces_lines.geojson"))
OBS = pd.read_csv(data("aq", "city_hourly.csv"), parse_dates=["time_utc"])


def field(run, valid):
    lead = int((valid - datetime.strptime(run, "%Y%m%d%H")).total_seconds() // 3600)
    with rasterio.open(data("gefs", run, f"f{lead:03d}.grib2")) as ds:
        a = ds.read(4)
        t = ds.transform
    lon = t.c + t.a * (np.arange(a.shape[1]) + 0.5)
    lat = t.f + t.e * (np.arange(a.shape[0]) + 0.5)
    return lon, lat, a, lead


def panel(ax, run, valid):
    lon, lat, a, lead = field(run, valid)
    sel_c = (lon > EXTENT[0] - 1) & (lon < EXTENT[1] + 1)
    sel_r = (lat > EXTENT[2] - 1) & (lat < EXTENT[3] + 1)
    ax.pcolormesh(lon[sel_c], lat[sel_r], a[np.ix_(sel_r, sel_c)], cmap=CMAP, norm=NORM, shading="nearest")
    for seg in ADM1:
        ax.plot(seg[:, 0], seg[:, 1], color="0.55", lw=0.5)
    for seg in ADM0:
        ax.plot(seg[:, 0], seg[:, 1], color="0.15", lw=1.0)
    ax.plot(*FIRE, marker="*", ms=16, mfc="red", mec="k", mew=0.8, zorder=5)
    obs = OBS[OBS["time_utc"] == valid].set_index("city")["pm25"]
    for key, (x, y) in CITIES.items():
        v = obs.get(key, np.nan)
        if np.isfinite(v):
            ax.scatter([x], [y], c=[v], cmap=CMAP, norm=NORM, s=130, edgecolors="k", linewidths=1.2, zorder=6)
            off, ha, va = label_place(key)
            ax.annotate(
                lang.T(f"{NAME}.city_value", city=lang.T(f"{NAME}.city.{key}"), v=v),
                (x, y),
                xytext=off,
                textcoords="offset points",
                fontsize=9,
                zorder=7,
                ha=ha,
                va=va,
                path_effects=[pe.withStroke(linewidth=3, foreground="white")],
            ).set_in_layout(False)  # long names must not shrink the panels
        else:
            ax.plot(x, y, "o", mfc="none", mec="0.3", ms=6, zorder=6)
    ax.set_xlim(EXTENT[:2])
    ax.set_ylim(EXTENT[2:])
    ax.set_aspect(1 / np.cos(np.radians(47)))
    r = datetime.strptime(run, "%Y%m%d%H")
    tag = lang.T(f"{NAME}.without_fire" if run == NO_FIRE_RUN else f"{NAME}.with_fire")
    ax.set_title(lang.T(f"{NAME}.panel", md=lang.md(r), h=r.hour, lead=lead, tag=tag), fontsize=9)
    ax.tick_params(labelsize=9)


def main():
    specs = [a.split(":") for a in (sys.argv[1:] or ROWS)]
    rows = [(datetime.strptime(v, "%Y%m%d%H"), r.split(",")) for v, r in specs]
    ncol = max(len(r) for _, r in rows)
    fig, axes = plt.subplots(
        len(rows), ncol, figsize=(9.6, 3.0 * len(rows) + 0.5), constrained_layout=True, squeeze=False
    )
    fig.get_layout_engine().set(wspace=0.07)
    for (valid, runs), row in zip(rows, axes):
        for k, (ax, run) in enumerate(zip(row, runs)):
            panel(ax, run, valid)
            ax.set_zorder(10 - k)  # left panels on top, so a long city label can run into the gap
        row[0].set_ylabel(lang.T(f"{NAME}.row", t=lang.mdhm(valid + timedelta(hours=8))), fontsize=10)
    fig.suptitle(lang.T(f"{NAME}.title"), fontsize=lang.T(f"{NAME}.title_size"))
    sm = plt.cm.ScalarMappable(cmap=CMAP, norm=NORM)
    fig.colorbar(sm, ax=axes.ravel().tolist(), shrink=0.6, ticks=LEVELS, label="PM2.5 µg/m³")
    fig.savefig(lang.out(NAME), dpi=150)


if __name__ == "__main__":
    main()
