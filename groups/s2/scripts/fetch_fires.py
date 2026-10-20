"""Active-fire L2 granules from NASA Earthdata (needs an Earthdata login in ~/.netrc).

- VIIRS 375 m (VNP14IMG, VJ114IMG, VJ214IMG v002, LP DAAC) over the fire box 46.4–47.6°N, 118.8–120.2°E,
  10-08 00Z – 10-11 06Z, listed from CMR -> data/s2/viirs_l2/ (42 granules, about 85 MB).
- MODIS 1 km (MOD14 / MYD14 C6.1): the three granules of 10-10 11Z – 10-11 00:50Z with detections in the box
  -> data/s2/modis_l2/. The 10-11 00:54Z Terra pass comes from the FIRMS snapshot instead.
Existing files are kept."""

import json
import os
import subprocess
import urllib.request

from common import D

CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"
VIIRS = ["VNP14IMG", "VJ114IMG", "VJ214IMG"]
TEMPORAL = "2026-10-08T00:00:00Z,2026-10-11T06:00:00Z"
MODIS = [
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD14.061/MOD14.A2026283.1120.061.2026283151814/MOD14.A2026283.1120.061.2026283151814.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD14.061/MOD14.A2026283.1255.061.2026283213250/MOD14.A2026283.1255.061.2026283213250.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MYD14.061/MYD14.A2026283.2025.061.2026285222329/MYD14.A2026283.2025.061.2026285222329.hdf",
]


def viirs_urls():
    urls = []
    for p in VIIRS:
        q = f"{CMR}?short_name={p}&version=002&bounding_box=118.8,46.4,120.2,47.6&temporal={TEMPORAL}&page_size=200"
        for e in json.load(urllib.request.urlopen(q))["feed"]["entry"]:
            urls += [
                l["href"] for l in e["links"] if l["href"].endswith(".nc") and l["href"].startswith("https://data.")
            ][:1]
    return sorted(set(urls))


def get(urls, sub):
    os.makedirs(D(sub), exist_ok=True)
    jar = D(sub, ".cookies")
    for u in urls:
        f = D(sub, os.path.basename(u))
        if f.exists() and f.stat().st_size:
            continue
        part = f.with_name(f.name + ".part")
        rc = subprocess.call(
            ["curl", "-sfn", "-L", "-c", str(jar), "-b", str(jar), "-A", "numrug-fire-2026/1.0", "-o", str(part), u]
        )
        if rc:
            print("failed", rc, u)
            continue
        part.rename(f)
        print(f.name)


u = viirs_urls()
D("viirs_l2").mkdir(parents=True, exist_ok=True)
D("viirs_l2", "urls.txt").write_text("\n".join(u) + "\n")
print(len(u), "VIIRS granules")
get(u, "viirs_l2")
get(MODIS, "modis_l2")
