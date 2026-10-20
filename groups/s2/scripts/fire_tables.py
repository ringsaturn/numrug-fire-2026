"""Active-fire L2 granules -> detection tables for the fire box 46.4–47.6°N, 118.8–120.2°E.

- data/s2/viirs_l2/*.nc  -> data/s2/derived/viirs_box.csv (t = granule start UTC; side A = Mongolian side of the
  OSM line closed to 117.5°E; dkm = distance to the line in UTM 50N). When CMR lists two production versions of
  one granule, the newest is kept.
- data/s2/modis_l2/*.hdf -> data/s2/derived/modis_l2_box.csv (day = solar zenith < 85°)."""

import csv
import datetime as dt
import glob
import os

import netCDF4
from pyhdf.SD import SD, SDC
from pyproj import Transformer
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import linemerge, unary_union
from shapely.prepared import prep

from common import D, osm

S, N, W, E = 46.4, 47.6, 118.8, 120.2
SAT = {"SUOMI-NPP": "N", "NPP": "N", "JPSS-1": "N20", "NOAA-20": "N20", "JPSS-2": "N21", "NOAA-21": "N21"}
SRC = {"N": "SUOMI_VIIRS_C2", "N20": "J1_VIIRS_C2", "N21": "J2_VIIRS_C2"}
CONF = {7: "l", 8: "n", 9: "h"}

os.makedirs(D("derived"), exist_ok=True)
T = Transformer.from_crs(4326, 32650, always_xy=True).transform
L = linemerge(unary_union([LineString(p) for p in osm() if len(p) > 1]))
if L.geom_type != "LineString":
    L = max(L.geoms, key=lambda g: g.length)
c = list(L.coords)
A = prep(Polygon(c + [(117.5, c[-1][1]), (117.5, c[0][1])]))
Lm = LineString([T(*q) for q in c])

latest = {}
for f in sorted(glob.glob(str(D("viirs_l2", "*.nc")))):
    latest[".".join(os.path.basename(f).split(".")[:3])] = f  # sorted: the later production stamp wins
rows, empty = [], 0
for f in sorted(latest.values()):
    d = netCDF4.Dataset(f)
    t = d.PGE_StartTime[:16]
    sat = SAT[d.PlatformShortName]
    if "FP_latitude" not in d.variables or len(d["FP_latitude"]) == 0:
        empty += 1
        continue
    lat, lon, frp, conf, day = (d[v][:] for v in ["FP_latitude", "FP_longitude", "FP_power", "FP_confidence", "FP_day"])
    for y, x, p, k, dn in zip(lat, lon, frp, conf, day):
        y, x = float(y), float(x)
        if S < y < N and W < x < E:
            rows.append(
                dict(
                    t=t,
                    src=SRC[sat],
                    sat=sat,
                    dn="D" if dn else "N",
                    lat=round(y, 5),
                    lon=round(x, 5),
                    frp=round(float(p), 2),
                    conf=CONF.get(int(k), str(k)),
                    nrt=0,
                    side="A" if A.contains(Point(x, y)) else "B",
                    dkm=round(Lm.distance(Point(*T(x, y))) / 1000, 2),
                )
            )
rows.sort(key=lambda r: (r["t"], r["sat"]))
with open(D("derived", "viirs_box.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, rows[0].keys())
    w.writeheader()
    w.writerows(rows)
print(len(rows), "VIIRS detections in the box;", empty, "granules without fire pixels")

rows = []
for f in sorted(glob.glob(str(D("modis_l2", "*.hdf")))):
    a = os.path.basename(f).split(".")
    t0 = dt.datetime.strptime(a[1][1:] + a[2], "%Y%j%H%M")
    s = SD(f, SDC.READ)
    v = {k: s.select(k)[:] for k in ["FP_latitude", "FP_longitude", "FP_power", "FP_SolZenAng"]}
    for y, x, p, z in zip(v["FP_latitude"], v["FP_longitude"], v["FP_power"], v["FP_SolZenAng"]):
        y, x = float(y), float(x)
        if S < y < N and W < x < E:
            rows.append(
                dict(
                    t=t0.strftime("%Y-%m-%d %H:%M"),
                    src="MODIS_C6_1_L2",
                    sat="T" if a[0] == "MOD14" else "A",
                    dn="D" if z < 85 else "N",
                    lat=f"{y:.5f}",
                    lon=f"{x:.5f}",
                    frp=f"{float(p):.2f}",
                )
            )
with open(D("derived", "modis_l2_box.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, rows[0].keys(), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
print(len(rows), "MODIS L2 detections in the box")
