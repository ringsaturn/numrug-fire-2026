"""NASA GIBS WMS images: the 10-16 NOAA-21 false colour behind the end of the animation, and the 10-12 NOAA-21
and 10-14 NOAA-20 false colour the burn-scar masks are cut from. Files already present are kept."""

import time

import requests

from common import GIBS

URL = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
M11 = "_CorrectedReflectance_BandsM11-I2-I1"
BOX = {"anim": ((118.8, 46.4, 120.2, 47.6), (1400, 1600)), "zoom": ((118.8, 46.5, 120.1, 47.5), (1300, 1460))}
JOBS = [
    ("anim", "2026-10-16", "VIIRS_NOAA21" + M11),
    ("zoom", "2026-10-12", "VIIRS_NOAA21" + M11),
    ("zoom", "2026-10-14", "VIIRS_NOAA20" + M11),
]

GIBS.mkdir(parents=True, exist_ok=True)
for box, day, layer in JOBS:
    f = GIBS / f"{box}_{day}_{layer}.png"
    if f.exists():
        print(f.name, "present")
        continue
    bb, (w, h) = BOX[box]
    for k in range(6):
        try:
            r = requests.get(
                URL,
                params=dict(
                    SERVICE="WMS",
                    VERSION="1.1.1",
                    REQUEST="GetMap",
                    LAYERS=layer,
                    SRS="EPSG:4326",
                    BBOX=",".join(map(str, bb)),
                    WIDTH=w,
                    HEIGHT=h,
                    FORMAT="image/png",
                    TRANSPARENT="TRUE",
                    TIME=day,
                ),
                timeout=180,
            )
        except requests.RequestException:
            time.sleep(10 * (k + 1))
            continue
        if r.status_code == 503:
            time.sleep(15 * (k + 1))
            continue
        r.raise_for_status()
        if not r.headers.get("content-type", "").startswith("image"):
            raise SystemExit(f"{f.name}: {r.text[:200]}")
        f.write_bytes(r.content)
        print(f.name, len(r.content))
        break
    else:
        raise SystemExit(f"{f.name}: no response")
