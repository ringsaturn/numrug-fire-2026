"""smoke-transport-s5p-20261011-1012: TROPOMI CO total column and UV aerosol index (qa >= 0.5) on 10-11 and 10-12,
2×2 (rows CO / UV AI), with the back trajectories arriving at Hailar (10-11 09:00) and Baicheng (10-12 19:00 UTC+8).

Inputs: data/ign/s5p/*.nc (GES DISC, orbits 46602/46603 and 46616/46617), data/ign/traj/back_traj.json (traj.py).
"""

import datetime as dt
import glob
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import netCDF4
import numpy as np

from common import IGN_LAT, IGN_LON, border, data
from figkit import lang

lang.init(__file__)
K = "smoke-transport-s5p-20261011-1012-v2."
plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "figure.titlesize": 12})
BX = (114, 126, 43, 51)
B = border()
PLACES = {
    "ignition": (IGN_LON, IGN_LAT),
    "hailar": (119.75, 49.22),
    "arxan": (119.944, 47.177),
    "ulanhot": (122.05, 46.08),
    "baicheng": (122.83, 45.62),
}
OFF = {"arxan": (0.2, 0.15), "hailar": (0.2, 0.15), "ulanhot": (0.2, 0.15), "baicheng": (0.2, -0.45)}
TR = json.load(open(data("traj", "back_traj.json")))


def load(day, prod, var, qa):
    out = []
    for f in sorted(glob.glob(str(data("s5p", f"S5P_OFFL_L2__{prod}_{day}*.nc")))):
        g = netCDF4.Dataset(f)["PRODUCT"]
        la = g["latitude"][0]
        lo = g["longitude"][0]
        m = (la > BX[2] - 1) & (la < BX[3] + 1) & (lo > BX[0] - 1) & (lo < BX[1] + 1)
        if not m.any():
            continue
        r, c = np.where(m)
        s = (slice(r.min(), r.max() + 1), slice(c.min(), c.max() + 1))
        v = np.ma.filled(g[var][0][s].astype(float), np.nan)
        v[g["qa_value"][0][s] < qa] = np.nan
        # overpass time = time of the scanline nearest the ignition point, so CO and AI of one orbit give the same minute
        dd = np.hypot(la - IGN_LAT, (lo - IGN_LON) * np.cos(np.radians(IGN_LAT)))
        ii = np.unravel_index(np.argmin(dd), dd.shape)[0]
        out.append((la[s], lo[s], v, dt.datetime.strptime(str(g["time_utc"][0][ii])[:16], "%Y-%m-%dT%H:%M")))
    return out


ROWS = [
    ("CO____", "carbonmonoxide_total_column", 0.028, 0.045, "YlOrRd", "co"),
    ("AER_AI", "aerosol_index_354_388", -1, 2, "RdPu", "ai"),
]
COLS = [
    (
        "20261011",
        [
            ("hailar 10-11T09 10m", "darkgreen", "10 m"),
            ("hailar 10-11T09 925hPa", "lime", "925 hPa"),
            ("hailar 10-11T09 850hPa", "b", "850 hPa"),
            ("hailar 10-11T09 700hPa", "c", "700 hPa"),
        ],
        "arrive_hailar",
        dt.datetime(2026, 10, 11, 9),
    ),
    (
        "20261012",
        [
            ("baicheng 10-12T19 925hPa", "lime", "925 hPa"),
            ("baicheng 10-12T19 850hPa", "b", "850 hPa"),
            ("baicheng 10-12T19 700hPa", "c", "700 hPa"),
        ],
        "arrive_baicheng",
        dt.datetime(2026, 10, 12, 19),
    ),
]
fig, ax = plt.subplots(2, 2, figsize=(7.2, 7.6))
halo = [pe.withStroke(linewidth=2.5, foreground="w")]
ign_dx, ign_ha = float(lang.T(K + "ignition_dx")), lang.T(K + "ignition_ha")
meshes = []
for i, (prod, var, vmin, vmax, cm, key) in enumerate(ROWS):
    for j, (day, trs, arrive, t_arr) in enumerate(COLS):
        a = ax[i, j]
        ts = []
        for la, lo, v, t in load(day, prod, var, 0.5):
            mesh = a.pcolormesh(lo, la, v, vmin=vmin, vmax=vmax, cmap=cm, shading="auto", rasterized=True)
            ts.append(t)
        for p in B:
            x, y = zip(*p)
            a.plot(x, y, "k--", lw=0.8)
        hs = []
        for tk, c, l in trs:
            pth = np.array([q[1:] for q in TR[tk]["path"]])
            hs += a.plot(pth[:, 1], pth[:, 0], "-", c=c, lw=1.6, label=l)
        for n, (x, y) in PLACES.items():
            a.plot(x, y, "k^" if n == "ignition" else "ko", ms=5)
            dx, dy, ha = (ign_dx, -0.45, ign_ha) if n == "ignition" else (*OFF[n], "left")
            a.text(x + dx, y + dy, lang.T(K + "place." + n), fontsize=9.5, path_effects=halo, ha=ha)
        a.set_xlim(BX[0], BX[1])
        a.set_ylim(BX[2], BX[3])
        a.set_aspect(1 / np.cos(np.radians(47)))
        a.set_xticks([116, 120, 124])
        a.set_yticks([44, 47, 50])
        a.set_xticklabels([f"{v}°E" for v in (116, 120, 124)] if i == 1 else [])
        a.set_yticklabels([f"{v}°N" for v in (44, 47, 50)] if j == 0 else [])
        times = lang.T(K + "time_sep").join(lang.hm(t + dt.timedelta(hours=8)) for t in sorted(set(ts)))
        a.set_title(
            lang.T(K + "panel", date=lang.md(t_arr), product=lang.T(K + key), times=times),
            fontsize=float(lang.T(K + "panel_size")),
        )
        if i == 1:
            a.legend(
                handles=hs,
                title=lang.T(
                    K + "legend", arrival=lang.T(K + arrive, date=lang.md(t_arr), H=t_arr.hour, M=t_arr.minute)
                ),
                fontsize=8.5,
                title_fontsize=8.5,
                loc="upper center",
                bbox_to_anchor=(0.5, -0.14),
                ncol=2,
                frameon=False,
            )
    meshes.append((mesh, lang.T(K + key + "_unit")))
fig.suptitle(lang.T(K + "title"), y=0.985)
fig.subplots_adjust(left=0.08, right=0.85, top=0.92, bottom=0.14, wspace=0.05, hspace=0.18)
fig.canvas.draw()
for i, (mesh, lab) in enumerate(meshes):
    pos = ax[i, 1].get_position()
    cb = fig.colorbar(mesh, cax=fig.add_axes([pos.x1 + 0.015, pos.y0, 0.022, pos.height]))
    cb.set_label(lab)
fig.savefig(lang.out("smoke-transport-s5p-20261011-1012-v2"), dpi=200)
