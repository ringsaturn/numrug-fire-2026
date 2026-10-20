"""VIIRS 375 m active-fire detections (standard L2 VNP14IMG / VJ114IMG / VJ214IMG v002) of the three 2026-10-08 passes
in the fire box -> data/ign/viirs_af_1008.csv (FIRMS-style columns; acq_time is the granule start time)."""

import csv
import glob

import netCDF4

from common import data

S, N, W, E = 46.4, 47.6, 118.8, 120.2
SAT = {"SUOMI-NPP": "NPP", "NPP": "NPP", "JPSS-1": "N20", "NOAA-20": "N20", "JPSS-2": "N21", "NOAA-21": "N21"}
CONF = {7: "l", 8: "n", 9: "h"}
COLS = [
    "satellite",
    "acq_date",
    "acq_time",
    "latitude",
    "longitude",
    "bright_ti4",
    "bright_ti5",
    "frp",
    "confidence",
    "daynight",
    "granule",
]
rows = []
for f in sorted(glob.glob(str(data("viirs_af", "V*14IMG.A2026281.*.nc")))):
    g = netCDF4.Dataset(f)
    t = g.PGE_StartTime
    v = {k: g[k][:] for k in ["FP_latitude", "FP_longitude", "FP_T4", "FP_T5", "FP_power", "FP_confidence", "FP_day"]}
    for i in range(len(v["FP_latitude"])):
        y, x = float(v["FP_latitude"][i]), float(v["FP_longitude"][i])
        if not (S < y < N and W < x < E):
            continue
        rows.append(
            dict(
                satellite=SAT[g.PlatformShortName],
                acq_date=t[:10],
                acq_time=t[11:13] + t[14:16],
                latitude=f"{y:.5f}",
                longitude=f"{x:.5f}",
                bright_ti4=f"{float(v['FP_T4'][i]):.2f}",
                bright_ti5=f"{float(v['FP_T5'][i]):.2f}",
                frp=f"{float(v['FP_power'][i]):.2f}",
                confidence=CONF[int(v["FP_confidence"][i])],
                daynight="D" if v["FP_day"][i] else "N",
                granule=f.rsplit("/", 1)[-1],
            )
        )
with open(data("viirs_af_1008.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, COLS)
    w.writeheader()
    w.writerows(rows)
for s in ("N21", "NPP", "N20"):
    q = [r for r in rows if r["satellite"] == s]
    print(s, len(q), "detections", round(sum(float(r["frp"]) for r in q), 2), "MW")
