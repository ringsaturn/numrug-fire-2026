"""Landsat 9 C2 L2 scene LC09_L2SP_122027_20261008_02_T1 (Microsoft Planetary Computer), ignition box
46.78–46.97°N, 119.28–119.52°E on a 30 m EPSG:4326 grid -> data/s2/landsat/IGN_<band>.npy (about 7 MB)."""

import math
import os

import numpy as np
import planetary_computer as pc
import rasterio
from pystac_client import Client
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT

from common import BOX, D

os.environ.update(
    GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_USERAGENT="numrug-fire-2026/1.0"
)
ITEM = "LC09_L2SP_122027_20261008_02_T1"
BANDS = ["red", "green", "blue", "nir08", "swir16", "swir22", "lwir11", "qa_pixel"]
l0, l1, b0, b1 = BOX["IGN"]
res = 30
dx = res / (111320 * math.cos(math.radians((b0 + b1) / 2)))
dy = res / 110950
w = int(round((l1 - l0) / dx))
h = int(round((b1 - b0) / dy))
tr = from_origin(l0, b1, dx, dy)
os.makedirs(D("landsat"), exist_ok=True)
todo = [a for a in BANDS if not D("landsat", f"IGN_{a}.npy").exists()]
if todo:
    c = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)
    it = next(c.search(collections=["landsat-c2-l2"], ids=[ITEM]).items())
    print(it.datetime, it.properties.get("eo:cloud_cover"))
    for a in todo:
        rs = Resampling.nearest if a == "qa_pixel" else Resampling.bilinear
        with (
            rasterio.open(it.assets[a].href) as src,
            WarpedVRT(src, crs="EPSG:4326", transform=tr, width=w, height=h, resampling=rs) as v,
        ):
            np.save(D("landsat", f"IGN_{a}.npy"), v.read(1))
            print(a)
