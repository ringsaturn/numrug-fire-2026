"""VIIRS 375 m fire pixels in the detection box from the L2 granules in data/ahi/viirs_l2/.

granules/viirs_l2.txt pins one production version per overpass (VNP14IMG / VJ114IMG /
VJ214IMG v002). Points in 46.3-47.8 N, 118.4-120.4 E with a granule start before
2026-10-12 00:00Z (the last VIIRS overpass in the published time series is 10-11 18:00Z)
go to data/ahi/viirs_box.csv: t (granule start, UTC), src, latitude, longitude, frp (MW).
"""

import csv
import os

import netCDF4

from common import BOX, GROUP_DIR, VIIRS_BOX, VIIRS_L2

SAT = {"SUOMI-NPP": "SUOMI", "NPP": "SUOMI", "JPSS-1": "J1", "NOAA-20": "J1", "JPSS-2": "J2", "NOAA-21": "J2"}
rows = []
for url in open(GROUP_DIR / "granules" / "viirs_l2.txt").read().split():
    d = netCDF4.Dataset(VIIRS_L2 / os.path.basename(url))
    t = d.PGE_StartTime[:16]
    if t >= "2026-10-12 00:00" or "FP_latitude" not in d.variables or len(d["FP_latitude"]) == 0:
        continue
    for y, x, p in zip(d["FP_latitude"][:], d["FP_longitude"][:], d["FP_power"][:]):
        y, x = float(y), float(x)
        if BOX["lat"][0] <= y <= BOX["lat"][1] and BOX["lon"][0] <= x <= BOX["lon"][1]:
            rows.append(
                dict(
                    t=t,
                    src=SAT[d.PlatformShortName],
                    latitude=round(y, 5),
                    longitude=round(x, 5),
                    frp=round(float(p), 2),
                )
            )
rows.sort(key=lambda r: (r["t"], r["src"]))
with open(VIIRS_BOX, "w", newline="") as fh:
    w = csv.DictWriter(fh, rows[0].keys())
    w.writeheader()
    w.writerows(rows)
print(len(rows), "points", rows[0]["t"], rows[-1]["t"])
