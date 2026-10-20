"""GK-2A AMI around the ignition point, 2026-10-08 ~11:40–12:20 UTC+8.

    fig_gk2a.py ir    ignition-gk2a-20261008-ir: 3.8 µm brightness temperature, five scans + legend cell (3×2),
                      each panel tagged with the ignition-pixel excess over background from gk2a_ign_series.json
    fig_gk2a.py vis   ignition-gk2a-20261008-vis: 0.64 µm albedo, four scans (2×2)

Inputs: data/ign/gk2a/*.nc (NOAA open-data bucket), data/ign/gk2a_ign_series.json (gk2a_series.py).
"""

import datetime as dt
import json
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import netCDF4
import numpy as np

from common import border, data, gk2a_bt, gk2a_lc, geos_lc
from figkit import lang

lang.init(__file__)
plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "figure.titlesize": 12})
EPOCH = dt.datetime(2000, 1, 1, 12)
LOCAL = dt.timedelta(hours=8)
B = border()


def draw_border(d, c0, l0, a, col):
    for p in B:
        lo, la = np.array(p).T
        c, l = geos_lc(la, lo, d.sub_longitude, d.cfac, d.lfac, d.coff, d.loff)
        a.plot(c - c0, l - l0, "--", c=col, lw=1)


def scan_time(d, li):
    """Scan time of line li, interpolated within the full-disk scan, UTC+8, truncated to the minute."""
    s = d.observation_start_time + li / d.number_of_lines * (d.observation_end_time - d.observation_start_time)
    return (EPOCH + dt.timedelta(seconds=float(s)) + LOCAL).replace(second=0, microsecond=0)


def ir():
    K = "ignition-gk2a-20261008-ir."
    ser = {r["nominal_utc"].replace(":", ""): r for r in json.load(open(data("gk2a_ign_series.json")))}
    fig, ax = plt.subplots(2, 3, figsize=(7.2, 5.9))
    ax = ax.ravel()
    for k, t in enumerate(["0340", "0350", "0400", "0410", "0420"]):
        d = netCDF4.Dataset(data("gk2a", f"gk2a_ami_le1b_sw038_fd020ge_20261008{t}.nc"))
        d.set_auto_mask(False)
        c, l = gk2a_lc(d)
        ci, li = int(round(c)), int(round(l))
        H, W2 = 15, 21
        b = gk2a_bt(d, d["image_pixel_values"][li - H : li + H, ci - W2 : ci + W2].astype(float))
        a = ax[k]
        im = a.imshow(b, cmap="inferno", vmin=290, vmax=335, aspect=1.45)
        draw_border(d, ci - W2, li - H, a, "w")
        a.plot(c - (ci - W2), l - (li - H), marker="*", ms=11, mfc="none", mec="cyan", mew=1.4)
        a.set_xlim(0, 2 * W2)
        a.set_ylim(2 * H, 0)
        a.set_xticks([])
        a.set_yticks([])
        s = ser[t]
        ts = dt.datetime.strptime("20261008 " + s["scan_utc_est"], "%Y%m%d %H:%M:%S").replace(second=0) + LOCAL
        a.set_title(lang.T(K + "panel", time=lang.hm(ts)))
        a.text(
            0.04,
            0.05,
            f"{s['dT38']:+.1f} K",
            transform=a.transAxes,
            color="w",
            fontsize=11,
            fontweight=lang.T(K + "excess_weight"),
            bbox=dict(fc="k", alpha=0.55, lw=0, pad=2),
        )
    LG = ax[5]
    LG.axis("off")
    cb = fig.colorbar(im, ax=LG, orientation="horizontal", fraction=0.5, aspect=12, location="top", pad=0)
    cb.set_label(lang.T(K + "colorbar"))
    LG.plot([], [], marker="*", ls="", ms=11, mfc="none", mec="cyan", mew=1.4, label=lang.T(K + "ignition"))
    LG.plot([], [], "w--", label=lang.T(K + "border"))
    LG.set_facecolor("none")
    LG.legend(loc="center", frameon=True, facecolor="#444", labelcolor="w", fontsize=9)
    LG.text(0.5, 0.1, lang.T(K + "note"), ha="center", va="center", transform=LG.transAxes, fontsize=9)
    fig.suptitle(lang.T(K + "title"), y=0.99)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.88, bottom=0.02, wspace=0.06, hspace=0.22)
    fig.savefig(lang.out("ignition-gk2a-20261008-ir"), dpi=200)


def vis():
    K = "ignition-gk2a-20261008-vis."
    fig, ax = plt.subplots(2, 2, figsize=(7.2, 7.3))
    ax = ax.ravel()
    for k, t in enumerate(["0340", "0350", "0400", "0410"]):
        d = netCDF4.Dataset(data("gk2a", f"gk2a_ami_le1b_vi006_fd005ge_20261008{t}.nc"))
        d.set_auto_mask(False)
        c, l = gk2a_lc(d)
        ci, li = int(round(c)), int(round(l))
        H = 60
        W2 = int(H * 1.4)
        dn = d["image_pixel_values"][li - H : li + H, ci - W2 : ci + W2].astype(float)
        alb = (dn * d.DN_to_Radiance_Gain + d.DN_to_Radiance_Offset) * d.Radiance_to_Albedo_c
        a = ax[k]
        a.imshow(alb, cmap="gray", vmin=0.08, vmax=0.20, aspect=1.45)
        draw_border(d, ci - W2, li - H, a, "y")
        a.plot(c - (ci - W2), l - (li - H), marker="*", ms=12, mfc="none", mec="cyan", mew=1.5)
        a.set_xlim(0, 2 * W2)
        a.set_ylim(2 * H, 0)
        a.set_xticks([])
        a.set_yticks([])
        a.set_title(lang.T(K + "panel", time=lang.hm(scan_time(d, li))))
    fig.suptitle(lang.T(K + "title"), y=0.99)
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    fig.savefig(lang.out("ignition-gk2a-20261008-vis"), dpi=200)


{"ir": ir, "vis": vis}[sys.argv[1]]()
