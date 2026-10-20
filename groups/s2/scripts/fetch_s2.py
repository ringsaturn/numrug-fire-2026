"""Sentinel-2 L2A windows from the Element84 Earth Search COGs -> data/s2/s2/<date>_<window>_<band>.npy.

Each window is read through a WarpedVRT onto a regular EPSG:4326 grid; tiles of the same day are mosaicked in
order of increasing no-data share. The 40 m overview grid "A" reads the COG overviews (20 m bands at level 0,
10 m bands at level 1). Existing files are kept, so a partial run resumes.

    python fetch_s2.py              # every window the figures read (about 1 GB)
    python fetch_s2.py 2026-10-10 SE # one window
"""

import concurrent.futures as cf
import json
import math
import os
import sys

import numpy as np
import rasterio
from pystac_client import Client
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT

from common import BOX, D

os.environ.update(
    GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
    CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
    GDAL_HTTP_MULTIRANGE="YES",
    GDAL_HTTP_MERGE_CONSECUTIVE_RANGES="YES",
    VSI_CACHE="TRUE",
    GDAL_HTTP_MAX_RETRY="6",
    GDAL_HTTP_RETRY_DELAY="3",
    GDAL_HTTP_USERAGENT="numrug-fire-2026/1.0",
)
STAC = "https://earth-search.aws.element84.com/v1"
COL = "sentinel-2-l2a"  # BOA offset already removed (earthsearch:boa_offset_applied)
NATIVE = {"blue": 10, "green": 10, "red": 10, "nir": 10, "nir08": 20, "swir16": 20, "swir22": 20, "scl": 20}
B6 = ["red", "green", "blue", "nir08", "swir22", "scl"]
B8 = ["red", "green", "blue", "nir", "nir08", "swir16", "swir22", "scl"]
# (date, window, target resolution in m, bands)
JOBS = (
    [(d, "A", 40, B6) for d in ("2026-10-05", "2026-10-08", "2026-10-10")]
    + [
        ("2026-10-10", "SE", 10, B6),
        ("2026-10-10", "NW", 10, B6),
        ("2026-10-05", "SPA", 20, B6),
        ("2026-10-10", "SPA", 10, B6),
        ("2026-10-08", "IGN", 10, B6),
    ]
    + [(d, "ZA", 10, B8) for d in ("2026-10-05", "2026-10-08", "2026-10-10", "2026-10-13")]
    + [(d, "ZB", 10, B8) for d in ("2026-10-05", "2026-10-13")]
    + [("2026-10-15", "ZI", 10, B8)]
)
# The 40 m overview keeps the published grid: fixed degree steps rather than metres.
A_GRID = (118.6, 120.1, 46.5, 47.6, 0.00052, 0.00036)


def grid(g, res):
    if g == "A":
        l0, l1, b0, b1, dx, dy = A_GRID
    else:
        l0, l1, b0, b1 = BOX[g]
        dx = res / (111320 * math.cos(math.radians((b0 + b1) / 2)))
        dy = res / 110950
    return from_origin(l0, b1, dx, dy), int(round((l1 - l0) / dx)), int(round((b1 - b0) / dy))


def fetch_one(href, asset, g, res):
    tr, w, h = grid(g, res)
    f = max(1, res // NATIVE[asset])
    kw = {"overview_level": {2: 0, 4: 1}[f]} if f >= 2 else {}
    rs = Resampling.nearest if asset == "scl" else Resampling.bilinear
    with (
        rasterio.open("/vsicurl/" + href, **kw) as src,
        WarpedVRT(src, crs="EPSG:4326", transform=tr, width=w, height=h, resampling=rs, src_nodata=0, nodata=0) as v,
    ):
        return v.read(1)


def run(date, g, res, assets):
    todo = [a for a in assets if not D("s2", f"{date}_{g}_{a}.npy").exists()]
    if not todo:
        return
    bbox = [118.6, 46.5, 120.1, 47.6]
    items = list(Client.open(STAC).search(collections=[COL], bbox=bbox, datetime=date).items())
    items.sort(key=lambda i: i.properties.get("s2:nodata_pixel_percentage", 0))
    meta = D("s2", f"{date}_{g}_meta.json")
    if not meta.exists():
        json.dump(
            {
                "date": date,
                "collection": COL,
                "items": [(i.id, i.datetime.isoformat(), i.properties.get("eo:cloud_cover")) for i in items],
            },
            open(meta, "w"),
        )
    tr, w, h = grid(g, res)
    for a in todo:
        with cf.ThreadPoolExecutor(4) as ex:
            arrs = list(ex.map(lambda it: fetch_one(it.assets[a].href, a, g, res), items))
        out = np.zeros((h, w), arrs[0].dtype)
        for arr in arrs:
            m = (out == 0) & (arr != 0)
            out[m] = arr[m]
        np.save(D("s2", f"{date}_{g}_{a}.npy"), out)
        print(date, g, a, out.shape, round(float((out > 0).mean()), 4), flush=True)


if __name__ == "__main__":
    os.makedirs(D("s2"), exist_ok=True)
    sel = sys.argv[1:3]
    for d, g, res, bands in JOBS:
        if not sel or (d, g) == tuple(sel):
            run(d, g, res, bands)
