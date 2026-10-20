"""Fetch the NASA GIBS Corrected Reflectance tiles every gibs figure reads (WMS GetMap, EPSG:4326).

The tiles come from the explicitly versioned NRT layers (MODIS_*_v6.1_NRT, VIIRS_SNPP_*_v2_NRT,
VIIRS_NOAA2x_*_v2.1_NRT) on the /wms/epsg4326/all/ endpoint. This is what the "best" endpoint served
in October 2026; it now serves the science-quality MODIS imagery for these days, which moves the
MODIS burn-scar areas by up to 20 km². Existing files are kept, so a rerun only fills gaps.
"""

import os
import sys
import time
import concurrent.futures as cf

import requests

from common import BOXES, FC_VIIRS, TC, data, fc, tile

URL = "https://gibs.earthdata.nasa.gov/wms/epsg4326/all/wms.cgi"
UA = {"User-Agent": "numrug-fire-2026/1.0"}
SATS = ["MODIS_Terra", "MODIS_Aqua", "VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21"]


def nrt(sat: str, bands: str) -> str:
    v = "_v6.1_NRT" if sat.startswith("MODIS") else "_v2_NRT" if sat == "VIIRS_SNPP" else "_v2.1_NRT"
    return f"{sat}_CorrectedReflectance_{bands}{v}"


def jobs():
    J = []
    # daily overview 10-07..10-12: (true-colour satellite, false-colour satellite) per day
    for d, a, b in [
        ("2026-10-07", "VIIRS_NOAA20", "VIIRS_NOAA20"),
        ("2026-10-08", "VIIRS_SNPP", "VIIRS_SNPP"),
        ("2026-10-09", "MODIS_Terra", "VIIRS_NOAA20"),
        ("2026-10-10", "MODIS_Aqua", "VIIRS_NOAA20"),
        ("2026-10-11", "MODIS_Aqua", "VIIRS_SNPP"),
        ("2026-10-12", "MODIS_Terra", "MODIS_Terra"),
    ]:
        J += [("loc", d, a, TC), ("loc", d, b, fc(b))]
    # 10-12: wide true colour, zoom true and false colour, all five satellites
    J += [("wide", "2026-10-12", s, TC) for s in SATS]
    J += [("zoom", "2026-10-12", s, b) for s in SATS for b in (fc(s), TC)]
    # 10-13: the three scenes that are not blank (S-NPP and NOAA-21 tiles are empty for this day)
    J += [("zoom", "2026-10-13", s, fc(s)) for s in ("MODIS_Terra", "VIIRS_NOAA20", "MODIS_Aqua")]
    # 10-14, 10-15: VIIRS false colour
    J += [("zoom", d, s, FC_VIIRS) for d in ("2026-10-14", "2026-10-15") for s in SATS[2:]]
    # the separate scar south of the main one (south-scar figure and its area check)
    J += [("south", "2026-10-14", "VIIRS_NOAA20", FC_VIIRS), ("south", "2026-10-16", "VIIRS_NOAA21", FC_VIIRS)]
    J += [("anim", "2026-10-16", s, FC_VIIRS) for s in ("VIIRS_NOAA21", "VIIRS_SNPP")]
    return J


def get(job):
    box, day, sat, bands = job
    fn = tile(box, day, sat, bands)
    if fn.exists():
        return fn, "kept"
    bb, (w, h), fmt = BOXES[box]
    params = dict(
        SERVICE="WMS",
        VERSION="1.1.1",
        REQUEST="GetMap",
        LAYERS=nrt(sat, bands),
        SRS="EPSG:4326",
        BBOX=",".join(map(str, bb)),
        WIDTH=w,
        HEIGHT=h,
        FORMAT="image/" + fmt,
        TRANSPARENT="TRUE" if fmt == "png" else "FALSE",
        TIME=day,
    )
    for k in range(6):
        try:
            r = requests.get(URL, params=params, headers=UA, timeout=180)
        except requests.RequestException:
            time.sleep(10 * (k + 1))
            continue
        if r.status_code == 503:
            time.sleep(15 * (k + 1))
            continue
        if r.headers.get("content-type", "").startswith("image"):
            tmp = fn.with_suffix(".part")
            tmp.write_bytes(r.content)
            os.replace(tmp, fn)
            return fn, len(r.content)
        return fn, "ERROR " + r.text[:200]
    return fn, "ERROR retries exhausted"


def main():
    data("raw", "gibs").mkdir(parents=True, exist_ok=True)
    bad = 0
    with cf.ThreadPoolExecutor(4) as ex:
        for fn, s in ex.map(get, jobs()):
            print(fn.name, s, flush=True)
            bad += str(s).startswith("ERROR")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
