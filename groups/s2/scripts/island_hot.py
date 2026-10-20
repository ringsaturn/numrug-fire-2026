"""Saturated SWIR pixels on the 10-15 Sentinel-2C ZI window (B12 > 0.40 and B11 > 0.35, outside cloud),
split by side of the OSM border -> data/s2/derived/zone_i_hot.json. Expected: 164 on the Mongolian side, 0 on the
Chinese side; the first 40 pixels (row-major) are kept for drawing."""

import json

import numpy as np

from common import D, cloudmask, ext_of, load, mongolia_mask

B8 = ("red", "green", "blue", "nir", "nir08", "swir16", "swir22", "scl")
e, dx, dy = ext_of("ZI", "2026-10-15")
X = load("2026-10-15", "ZI", B8)
cl = cloudmask(X)
inM, la, lo = mongolia_mask(e, dx, dy, cl.shape)
hot = (X["swir22"] > 4000) & (X["swir16"] > 3500) & ~cl
ys, xs = np.where(hot)
res = dict(
    hot_mn=int((hot & inM).sum()),
    hot_cn=int((hot & ~inM).sum()),
    hot_px=[dict(lat=round(float(la[y]), 4), lon=round(float(lo[x]), 4)) for y, x in zip(ys, xs)][:40],
)
D("derived").mkdir(parents=True, exist_ok=True)
json.dump(res, open(D("derived", "zone_i_hot.json"), "w"), indent=1)
print("saturated pixels: Mongolian side", res["hot_mn"], "Chinese side", res["hot_cn"])
