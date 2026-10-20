"""FIRMS detections of 10-12 in the fire box (46.3–47.9°N, 118.3–120.6°E), each classed by side of the OSM border.

Reads the LANCE daily archive files (raw/firms/*_NRT_2026285.txt) and writes firms/firms_20261012.csv with
the archive columns plus src (SUOMI/J1/J2/MODIS), t (UTC) and cty (MNG on the Mongolian side, else CHN).
"""

import glob
import os

import pandas as pd
from shapely.geometry import Point, Polygon
from shapely.prepared import prep

from common import data, main_line, mongolia_polygon, osm_border

MNG = prep(Polygon(mongolia_polygon(main_line(osm_border()))))
frames = []
for f in sorted(glob.glob(str(data("raw", "firms", "*_NRT_2026285.txt")))):
    q = pd.read_csv(f)
    q["src"] = os.path.basename(f).split("_")[0]
    frames.append(q)
d = pd.concat(frames)
d = d[(d.latitude > 46.3) & (d.latitude < 47.9) & (d.longitude > 118.3) & (d.longitude < 120.6)].copy()
d["t"] = pd.to_datetime(
    d.acq_date + " " + d.acq_time.astype(str).str.replace(":", "").str.zfill(4), format="%Y-%m-%d %H%M"
)
d["cty"] = ["MNG" if MNG.contains(Point(x, y)) else "CHN" for x, y in zip(d.longitude, d.latitude)]
d = d.sort_values("t", kind="stable")
data("firms").mkdir(parents=True, exist_ok=True)
d.to_csv(data("firms", "firms_20261012.csv"), index=False)
g = d.groupby([d.t.dt.strftime("%H:%M"), "src"]).agg(
    n=("frp", "size"), frp=("frp", "sum"), chn=("cty", lambda s: (s == "CHN").sum())
)
print(g[g.n >= 3].round(1).to_string())
