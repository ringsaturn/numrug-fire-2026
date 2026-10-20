"""FIRMS-style tables of the r2 and r3 reports -> data/firms/main_{r2,r3}.csv (detections in 46.3-47.9°N,
118.3-120.6°E with side, distance to the border and to Arxan) and passes_{r2,r3}.csv (30-min bins, >= 3 detections).

Sources: VIIRS L2 (viirs_l2.csv), MODIS standard before 10-11 00:30Z (modis_l2.csv), FIRMS MODIS NRT after.
Each table holds what that report's FIRMS download held:
  r2 (10-12 11:56Z): detections up to 10-12 06:35Z;
  r3 (10-13 05:26Z): up to 10-13 00:35Z, NOAA-20 only up to 10-12 05:27Z (the NOAA-20 7-day download failed)."""

import numpy as np
import pandas as pd
from shapely.geometry import Point

from common import ARXAN, D, TABLE_BOX, in_box, modis_nrt, mongolia, viirs

MNG, Lm, T = mongolia("mapbbox")
cols = ["latitude", "longitude", "frp", "t", "src"]
m1 = pd.read_csv(D / "modis_l2.csv", parse_dates=["t"])
m1 = m1[m1.t < "2026-10-11 00:30"]
m2 = modis_nrt()
m2["src"] = "MODIS"
b = pd.concat([viirs()[cols], m1[cols], m2[cols]])


def build(tag, cut, j1cut=None):
    q = b[b.t <= cut]
    if j1cut is not None:
        q = q[(q.src != "J1") | (q.t <= j1cut)]
    d = in_box(q, TABLE_BOX, strict=True).copy()
    d["cty"] = ["MNG" if MNG.contains(Point(x, y)) else "CHN" for x, y in zip(d.longitude, d.latitude)]
    d["dkm"] = [Lm.distance(Point(*T(x, y))) / 1000 for x, y in zip(d.longitude, d.latitude)]
    ax = T(*ARXAN)
    d["darx"] = [np.hypot(*(np.subtract(T(x, y), ax))) / 1000 for x, y in zip(d.longitude, d.latitude)]
    d["pass"] = d.t.dt.floor("30min")
    d = d.sort_values("t")
    d.to_csv(D / f"main_{tag}.csv", index=False)
    rows = []
    for (p, s), g in d.groupby(["pass", "src"]):
        if len(g) >= 3:
            rows.append(
                dict(
                    t=p,
                    src=s,
                    n=len(g),
                    frp=g.frp.sum(),
                    cn=(g.cty == "CHN").sum(),
                    E=g.longitude.max(),
                    W=g.longitude.min(),
                )
            )
    pd.DataFrame(rows).to_csv(D / f"passes_{tag}.csv", index=False)
    bj = d[d.src != "MODIS"].t + pd.Timedelta(hours=8)
    print(
        tag,
        len(d),
        "detections, newest",
        d.t.max(),
        "| VIIRS per UTC+8 day",
        bj.dt.strftime("%m-%d").value_counts().sort_index().to_dict(),
    )


build("r2", "2026-10-12 06:35")
build("r3", "2026-10-13 00:35", j1cut="2026-10-12 05:27")
