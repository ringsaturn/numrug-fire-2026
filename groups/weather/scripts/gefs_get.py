"""Fetch GEFS-Aerosols (GEFSv12 chemistry, control member, 0.25°, 3-hourly) records by .idx byte range.

Each data/weather/gefs/<run>/fFFF.grib2 holds six records, in this band order:
total AOD 550 nm, POM AOD 550, BC AOD 550, surface PM2.5 (µg/m³), column BC, column POM (kg/m²).
Runs: 10-08 00Z to +120 h (before this fire entered the model), and every 12 h from
10-08 12Z to 10-13 00Z to +48 h. About 900 MB in all.

    gefs_get.py [RUN MAXF ...]     # default: every run above
"""

import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from common import USER_AGENT, data

BASE = "https://noaa-gefs-pds.s3.amazonaws.com"
RUNS = [("2026100800", 120)] + [
    (r, 48)
    for r in (
        "2026100812",
        "2026100900",
        "2026100912",
        "2026101000",
        "2026101012",
        "2026101100",
        "2026101112",
        "2026101200",
        "2026101212",
        "2026101300",
    )
]
WANT = [
    ("AOTK", "aerosol=Total aerosol:", "aerosol_wavelength >=5.45e-07"),
    ("AOTK", "aerosol=Particulate organic matter dry:", "aerosol_wavelength >=5.45e-07"),
    ("AOTK", "aerosol=Black carbon dry:", "aerosol_wavelength >=5.45e-07"),
    ("PMTF", "aerosol=Total aerosol:", "surface"),
    ("COLMD", "aerosol=Black carbon dry:", ""),
    ("COLMD", "aerosol=Particulate organic matter dry:", ""),
]
OUT = data("gefs")


def get(url, rng=None):
    headers = {"User-Agent": USER_AGENT}
    if rng:
        headers["Range"] = f"bytes={rng[0]}-{rng[1]}"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
                return r.read()
        except Exception:
            if attempt == 3:
                raise
            time.sleep(5 * (attempt + 1))


def one(run, f):
    d, h = run[:8], run[8:]
    dest = OUT / run / f"f{f:03d}.grib2"
    if dest.exists() and dest.stat().st_size > 0:
        return
    url = f"{BASE}/gefs.{d}/{h}/chem/pgrb2ap25/gefs.chem.t{h}z.a2d_0p25.f{f:03d}.grib2"
    lines = get(url + ".idx").decode().strip().splitlines()
    starts = [int(line.split(":")[1]) for line in lines]
    parts = []
    for var, aer, extra in WANT:
        hit = [
            i for i, line in enumerate(lines) if f":{var}:" in line and aer.lower() in line.lower() and extra in line
        ]
        if var == "COLMD":
            hit = hit[:1]
        if len(hit) != 1:
            raise SystemExit(f"{run} f{f}: {var} {aer} matched {len(hit)}")
        i = hit[0]
        end = starts[i + 1] - 1 if i + 1 < len(starts) else ""
        parts.append(get(url, (starts[i], end)))
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    tmp.write_bytes(b"".join(parts))
    tmp.rename(dest)


if __name__ == "__main__":
    args = sys.argv[1:]
    runs = [(args[i], int(args[i + 1])) for i in range(0, len(args), 2)] if args else RUNS
    for run, maxf in runs:
        with ThreadPoolExecutor(3) as pool:
            list(pool.map(lambda f: one(run, f), range(0, maxf + 1, 3)))
        print(run, "files:", len(list((OUT / run).glob("*.grib2"))), file=sys.stderr)
