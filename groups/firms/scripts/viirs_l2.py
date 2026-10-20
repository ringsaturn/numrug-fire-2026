"""VIIRS 375 m active-fire L2 granules (VNP14IMG / VJ114IMG / VJ214IMG v002, LANCE NRT where the standard product
was not out yet) -> data/firms/viirs_l2.csv, one row per fire pixel in 44-50.5°N, 110-124°E.

CMR can list two production versions of one granule: the newest per (product, start time) is kept, and an NRT
granule is used only where no standard granule exists. t is the granule start (UTC), which FIRMS calls acq_time."""

import csv
import datetime as dt
import glob
import os

import netCDF4

from common import D, RAW, SRC, WIDE_BOX

latest = {}
for f in sorted(glob.glob(str(RAW / "l2" / "*.nc"))):
    k = ".".join(os.path.basename(f).replace("_NRT", "").split(".")[:3])
    if "_NRT" in f and k in latest and "_NRT" not in latest[k]:
        continue
    if "_NRT" not in f or k not in latest:
        latest[k] = f
S, N, W, E = WIDE_BOX
rows = []
for f in sorted(latest.values()):
    d = netCDF4.Dataset(f)
    if "FP_latitude" not in d.variables or len(d["FP_latitude"]) == 0:
        continue
    a = os.path.basename(f).split(".")
    t = dt.datetime.strptime(a[1][1:] + a[2], "%Y%j%H%M")
    src = SRC[d.PlatformShortName]
    for y, x, p, dn in zip(*(d[v][:] for v in ["FP_latitude", "FP_longitude", "FP_power", "FP_day"])):
        y, x = float(y), float(x)
        if S < y < N and W < x < E:
            rows.append(
                dict(
                    latitude=round(y, 5),
                    longitude=round(x, 5),
                    frp=round(float(p), 2),
                    t=t.strftime("%Y-%m-%d %H:%M"),
                    src=src,
                    daynight="D" if dn else "N",
                    version="NRT" if "_NRT" in f else "STD",
                    granule=os.path.basename(f),
                )
            )
with open(D / "viirs_l2.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, rows[0].keys())
    w.writeheader()
    w.writerows(rows)
print(len(rows), "VIIRS detections from", len(latest), "granules")
