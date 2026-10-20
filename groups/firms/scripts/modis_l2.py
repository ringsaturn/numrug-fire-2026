"""MOD14 / MYD14 C6.1 standard granules (LP DAAC) -> data/firms/modis_l2.csv for 10-07 12Z to 10-11 03Z.
The FIRMS MODIS NRT records of those days are no longer served; the standard product is their reprocessed
equivalent (identical on the one overlapping pass, Terra 10-11 00:50Z: 74 detections, 3571.69 MW)."""

import csv
import datetime as dt
import glob
import os

from pyhdf.SD import SD, SDC

from common import D, RAW, WIDE_BOX

S, N, W, E = WIDE_BOX
rows = []
for f in sorted(glob.glob(str(RAW / "modis_l2" / "*.hdf"))):
    a = os.path.basename(f).split(".")
    t = dt.datetime.strptime(a[1][1:] + a[2], "%Y%j%H%M")
    s = SD(f, SDC.READ)
    if "FP_latitude" not in s.datasets():
        continue
    v = {k: s.select(k)[:] for k in ["FP_latitude", "FP_longitude", "FP_power", "FP_confidence"]}
    if v["FP_latitude"] is None or len(v["FP_latitude"]) == 0:
        continue
    for y, x, p, c in zip(v["FP_latitude"], v["FP_longitude"], v["FP_power"], v["FP_confidence"]):
        y, x = float(y), float(x)
        if S < y < N and W < x < E:
            rows.append(
                dict(
                    latitude=round(y, 4),
                    longitude=round(x, 4),
                    frp=round(float(p), 2),
                    conf=int(c),
                    t=t.strftime("%Y-%m-%d %H:%M"),
                    src="MODIS",
                    sat="T" if a[0] == "MOD14" else "A",
                    granule=os.path.basename(f),
                )
            )
with open(D / "modis_l2.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, rows[0].keys())
    w.writeheader()
    w.writerows(rows)
print(len(rows), "MODIS detections")
