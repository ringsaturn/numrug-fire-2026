"""Hotspot detection on every Himawari-9 frame of data/ahi/ahi_b07_b14_crop.npz.

Absolute test (BT7 > 320 K day / 310 K night with BT7-BT14 margin) or contextual test
(BT7-BT14 > 4 sigma above the 21x21 clear-sky background and > 10 K, BT7 > 3 sigma), with a
BT14 cloud screen, inside the box 46.3-47.8 N, 118.4-120.4 E. Day = solar zenith < 85 deg.
Writes data/ahi/ahi_hotmask.npz (per-frame masks) and ahi_hotspots_10min.csv (per-frame stats).
"""

import warnings

import numpy as np
import pandas as pd
from pyorbital.astronomy import sun_zenith_angle
from scipy.ndimage import uniform_filter

from common import BOX, CROP, HOTSPOTS, MASK

warnings.filterwarnings("ignore")
z = np.load(CROP)
tags, b7a, b14a, lon, lat = z["tags"], z["b07"], z["b14"], z["lon"], z["lat"]
box = (lat >= BOX["lat"][0]) & (lat <= BOX["lat"][1]) & (lon >= BOX["lon"][0]) & (lon <= BOX["lon"][1])
# pixel area (km2) from the lon/lat spacing
dy = np.abs(np.gradient(lat, axis=0)) * 111.2
dx = np.abs(np.gradient(lon, axis=1)) * 111.2 * np.cos(np.radians(lat))
area = dx * dy
W = 21


def lstat(x, valid):
    """Mean, standard deviation and count of x over the valid pixels of each W x W window."""
    n = uniform_filter(valid.astype("f8"), W, mode="nearest") * W * W
    s = uniform_filter(np.where(valid, x, 0.0), W, mode="nearest") * W * W
    s2 = uniform_filter(np.where(valid, x * x, 0.0), W, mode="nearest") * W * W
    m = s / np.maximum(n, 1)
    sd = np.sqrt(np.maximum(s2 / np.maximum(n, 1) - m * m, 0))
    return m, sd, n


rows, masks = [], []
for i, tag in enumerate(tags):
    t = pd.to_datetime(str(tag), format="%Y%m%d_%H%M") + pd.Timedelta(
        minutes=1
    )  # segment 2 is scanned about 1 min after the slot start
    b7 = b7a[i].astype("f8")
    b14 = b14a[i].astype("f8")
    d = b7 - b14
    sza = float(sun_zenith_angle(t.to_pydatetime(), 119.3, 47.0))
    day = sza < 85
    absT = 320.0 if day else 310.0
    cand = (b7 > (310 if day else 285)) & (d > (8 if day else 6)) & (b14 > (275 if day else 255))
    clear = (b14 > 265) & np.isfinite(b7) & np.isfinite(b14)
    bg = clear & ~cand
    md, sdd, n = lstat(d, bg)
    m7, sd7, _ = lstat(b7, bg)
    m14, _, _ = lstat(b14, bg)
    sdd = np.maximum(sdd, 1.5 if day else 1.0)
    sd7 = np.maximum(sd7, 1.5 if day else 1.0)
    ctx = cand & (d > md + 4 * sdd) & (d > 10) & (b7 > m7 + 3 * sd7) & (n >= 20) & (b14 > m14 - (4 if day else 8))
    f = (((b7 > absT) & (d > (15 if day else 10)) & (b14 > (275 if day else 255))) | ctx) & box
    nfire = int(f.sum())
    r = dict(
        time_utc=t.floor("min") - pd.Timedelta(minutes=1),
        sza=round(sza, 1),
        day=int(day),
        n_hot=nfire,
        hot_area_km2=round(float(area[f].sum()), 1),
        bt7_max=round(float(np.nanmax(np.where(box, b7, np.nan))), 2),
        n_sat=int(((b7 >= 399) & box).sum()),
        dT_excess_sum=round(float((d - md)[f].sum()), 1) if nfire else 0.0,
    )
    if nfire:
        w = (d - md)[f]
        r.update(
            lat_c=round(float(lat[f].mean()), 4),
            lon_c=round(float(lon[f].mean()), 4),
            lat_wc=round(float((lat[f] * w).sum() / w.sum()), 4),
            lon_wc=round(float((lon[f] * w).sum() / w.sum()), 4),
            lat_min=round(float(lat[f].min()), 3),
            lat_max=round(float(lat[f].max()), 3),
            lon_min=round(float(lon[f].min()), 3),
            lon_max=round(float(lon[f].max()), 3),
        )
    rows.append(r)
    masks.append(f)
df = pd.DataFrame(rows)
df.insert(1, "time_bjt", df.time_utc + pd.Timedelta(hours=8))
df.to_csv(HOTSPOTS, index=False)
np.savez_compressed(MASK, tags=tags, mask=np.stack(masks), lon=lon, lat=lat)
print(len(df), "frames,", int(df.n_hot.sum()), "hotspot pixel detections")
