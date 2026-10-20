"""dNBR rasters for the zoom figures and the numbers quoted with them.

- ZA 10-05 -> 10-10: cloud = SCL 8/9/10 or blue > 0.15 (no dilation)       -> derived/ZA_dnbr_1005_1010.npy
- ZA, ZB 10-05 -> 10-13: cloud and cloud shadow, common.cloudmask()        -> derived/{ZA,ZB}_dnbr_1005_1013.npy
- burned area on the Chinese side (dNBR > 0.27, opened twice, patches >= 0.05 km²) -> derived/zones_check.json
Expected: ZA 10-10 22.55 km² (largest patch 12.04), Chinese-side cloud 27.8 %; 10-13 ZA cloud 55.7 %, ZB 77.3 %;
ZA new since 10-10 0.14 km²."""

import json

import numpy as np
from scipy import ndimage

from common import D, cloudmask, ext_of, load, mongolia_mask, nbr

B8 = ("red", "green", "blue", "nir", "nir08", "swir16", "swir22", "scl")
D("derived").mkdir(parents=True, exist_ok=True)
res = {}

e, dx, dy = ext_of("ZA", "2026-10-05")
D5 = load("2026-10-05", "ZA", B8)
D10 = load("2026-10-10", "ZA", B8)
cloud = np.isin(D10["scl"], [8, 9, 10]) | (D10["blue"] > 1500)
dn = np.where(cloud, np.nan, nbr(D5) - nbr(D10))
np.save(D("derived", "ZA_dnbr_1005_1010.npy"), dn.astype("f4"))
inM, la, lo = mongolia_mask(e, dx, dy, dn.shape)
pxa = (dx * 111.32 * np.cos(np.radians(la)) * dy * 110.95)[:, None] * np.ones((1, dn.shape[1]))
burn = ndimage.binary_opening((dn > 0.27) & ~inM, iterations=2)
lab, n = ndimage.label(burn)
sz = ndimage.sum(burn, lab, range(1, n + 1)) * pxa.mean()
big = np.isin(lab, 1 + np.where(sz >= 0.05)[0])
res["zonea_cn_km2"] = round(float((big * pxa).sum()), 2)
res["zonea_cloud_cn"] = round(float(cloud[~inM].mean()), 3)
res["zonea_largest_km2"] = round(float(sz.max()), 2)

for g in ["ZA", "ZB"]:
    e, dx, dy = ext_of(g, "2026-10-05")
    D5 = load("2026-10-05", g, B8)
    D13 = load("2026-10-13", g, B8)
    cl = cloudmask(D13)
    dn = np.where(cl, np.nan, nbr(D5) - nbr(D13))
    np.save(D("derived", f"{g}_dnbr_1005_1013.npy"), dn.astype("f4"))
    inM, la, lo = mongolia_mask(e, dx, dy, dn.shape)
    pa = dx * 111.32 * np.cos(np.radians(e[2])) * dy * 110.95
    burn = ndimage.binary_opening((dn > 0.27) & ~inM, iterations=2)
    lab, n = ndimage.label(burn)
    sz = ndimage.sum(burn, lab, range(1, n + 1)) * pa
    res[g + "_1013"] = dict(cloud_cn=round(float(cl[~inM].mean()), 3), cn_km2=round(float(sz[sz >= 0.05].sum()), 2))

e, dx, dy = ext_of("ZA", "2026-10-05")
d10 = np.load(D("derived", "ZA_dnbr_1005_1010.npy"))
d13 = np.load(D("derived", "ZA_dnbr_1005_1013.npy"))
inM, la, lo = mongolia_mask(e, dx, dy, d13.shape)
pa = dx * 111.32 * np.cos(np.radians(e[2])) * dy * 110.95
ok = np.isfinite(d10) & np.isfinite(d13) & ~inM
new = ndimage.binary_opening(ok & (d13 > 0.27) & ~(d10 > 0.27), iterations=2)
res["ZA_new_since_1010_km2"] = round(float(new.sum() * pa), 2)
print(json.dumps(res, indent=1))
json.dump(res, open(D("derived", "zones_check.json"), "w"), indent=1)
