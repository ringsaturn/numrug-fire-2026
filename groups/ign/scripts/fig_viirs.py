"""ignition-viirs-20261008: the first three VIIRS passes after ignition (NOAA-21 04:06, S-NPP 04:42, NOAA-20 05:00 UTC):
colour composite of the wider area, false colour and I4 (3.74 µm) of the fire box, active-fire detections and I4 statistics.

Inputs: data/ign/viirs_<pass>.npz (viirs_crop.py), data/ign/viirs_af_1008.csv (viirs_af.py).
"""

import datetime as dt

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.transforms import Bbox

from common import IGN_LAT, IGN_LON, border, data
from figkit import lang

lang.init(__file__)
K = "ignition-viirs-20261008."
B = border()
F = pd.read_csv(data("viirs_af_1008.csv"), dtype={"acq_time": str})
IGN = (IGN_LON, IGN_LAT)
ZB = (119.22, 119.62, 46.75, 47.02)
ASPECT = 1 / np.cos(np.radians(47))
# pass, satellite, nominal overpass time over the fire (UTC), active-fire granule start (hhmm)
P = [
    ("N21_0406", "NOAA-21", dt.datetime(2026, 10, 8, 4, 8), "N21", "0406"),
    ("NPP_0442", "S-NPP", dt.datetime(2026, 10, 8, 4, 44), "NPP", "0442"),
    ("N20_0500", "NOAA-20", dt.datetime(2026, 10, 8, 5, 4), "N20", "0500"),
]


def stretch(a, lo, hi, g=0.8):
    return np.clip((a - lo) / (hi - lo), 0, 1) ** g


fig, ax = plt.subplots(3, 3, figsize=(15, 14.5))
for i, (tag, sat, t, src, gran) in enumerate(P):
    z = np.load(data(f"viirs_{tag}.npz"))
    lat, lon = z["lat"], z["lon"]
    ext = (lon[0], lon[-1], lat[-1], lat[0])
    if "M05" in z:
        rgb = np.dstack([stretch(z["M05"], 0.02, 0.16), stretch(z["M04"], 0.03, 0.16), stretch(z["M03"], 0.04, 0.17)])
        lab = lang.T(K + "true_colour")
    else:
        g = stretch(z["I01"], 0.02, 0.17)
        rgb = np.dstack([g, g, g])
        lab = lang.T(K + "i1")
    fc = np.dstack([stretch(z["I03"], 0.03, 0.35), stretch(z["I02"], 0.03, 0.25), stretch(z["I01"], 0.02, 0.17)])
    q = F[(F.satellite == src) & (F.acq_date == "2026-10-08") & (F.acq_time == gran)]
    I4 = z["I04"]
    LA, LO = np.meshgrid(lat, lon, indexing="ij")
    near = np.hypot((LO - IGN[0]) * np.cos(np.radians(47)), LA - IGN[1]) < 0.12
    bg = np.nanmedian(I4[near & (I4 < 320)])
    hot = near & (I4 > bg + 15)
    j, k = np.unravel_index(np.nanargmax(np.where(near, I4, np.nan)), I4.shape)
    st = dict(
        n=len(q),
        frp=round(float(q.frp.sum()), 1),
        i4max=round(float(I4[j, k]), 1),
        i4bg=round(float(bg), 1),
        hot=int(hot.sum()),
        vza=round(float(z["vza"][j, k]), 1),
    )
    print(sat, st)
    head = dict(sat=sat, local=lang.hm(t + dt.timedelta(hours=8)), utc=lang.hm(t))
    for c, (img, title) in enumerate([(rgb, lab), (fc, lang.T(K + "false_colour")), (None, lang.T(K + "i4"))]):
        a = ax[i, c]
        if img is None:
            im = a.imshow(I4, extent=ext, cmap="inferno", vmin=285, vmax=345, aspect=ASPECT)
        else:
            a.imshow(img, extent=ext, aspect=ASPECT)
        for p in B:
            x, y = zip(*p)
            a.plot(x, y, "--", c="w" if c == 2 else "yellow", lw=1)
        a.plot(*IGN, marker="*", ms=10 if c == 0 else 13, mfc="none", mec="cyan", mew=1.5)
        if c > 0:
            a.set_xlim(ZB[0], ZB[1])
            a.set_ylim(ZB[2], ZB[3])
            if c == 2:
                a.scatter(q.longitude, q.latitude, s=40, facecolor="none", edgecolor="cyan", lw=1.2)
        else:
            a.set_xlim(118.7, 120.3)
            a.set_ylim(46.3, 47.4)
            a.add_patch(plt.Rectangle((ZB[0], ZB[2]), ZB[1] - ZB[0], ZB[3] - ZB[2], fill=False, ec="w", lw=1))
            a.text(119.944, 47.177, lang.T(K + "arxan"), c="w", fontsize=float(lang.T(K + "arxan_size")))
        a.set_title(lang.T(K + "panel", product=title, **head), fontsize=9)
        a.tick_params(labelsize=7)
    ax[i, 2].text(
        0.02,
        0.02,
        lang.T(K + "stats", **st),
        transform=ax[i, 2].transAxes,
        color="w",
        fontsize=8.5,
        va="bottom",
        bbox=dict(fc="k", alpha=0.5),
    )
fig.colorbar(im, ax=ax[:, 2], shrink=0.5, label=lang.T(K + "colorbar"))
fig.suptitle(lang.T(K + "title", date=lang.ymd(P[0][2]), lat=IGN_LAT, lon=IGN_LON), fontsize=11)
# tight bbox, widened or narrowed about its centre to the published 1606×1691 px, so every language has the same size
bb = fig.get_tightbbox(fig.canvas.get_renderer()).padded(0.1)
cx, cy = (bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2
w, h = 1606 / 130, 1691 / 130
fig.savefig(
    lang.out("ignition-viirs-20261008"), dpi=130, bbox_inches=Bbox([[cx - w / 2, cy - h / 2], [cx + w / 2, cy + h / 2]])
)
