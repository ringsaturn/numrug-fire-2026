"""Trajectory wind field: ECMWF IFS 0.25° hourly winds from the Open-Meteo historical-forecast API on a 0.5° grid,
43–51°N × 114–126°E, 10 m / 925 / 850 / 700 hPa, 2026-10-09..10-12 UTC, m/s -> data/ign/traj/wind_ecmwf_hist.json
(lat, lon, data = one Open-Meteo response per grid point, lat-major). Skipped if the file exists."""

import json
import time

import numpy as np
import requests

from common import data

OUT = data("traj", "wind_ecmwf_hist.json")
if OUT.exists():
    print(f"{OUT.name} present")
    raise SystemExit(0)
OUT.parent.mkdir(parents=True, exist_ok=True)
la = np.arange(43, 51.01, 0.5)
lo = np.arange(114, 126.01, 0.5)
V = ",".join(f"wind_speed_{p},wind_direction_{p}" for p in ("10m", "925hPa", "850hPa", "700hPa"))
rows = []
for y in la:
    for k in range(5):
        try:
            r = requests.get(
                "https://historical-forecast-api.open-meteo.com/v1/forecast",
                headers={"User-Agent": "numrug-fire-2026/1.0"},
                timeout=120,
                params=dict(
                    latitude=",".join(f"{y:.2f}" for _ in lo),
                    longitude=",".join(f"{x:.2f}" for x in lo),
                    hourly=V,
                    models="ecmwf_ifs025",
                    wind_speed_unit="ms",
                    timezone="GMT",
                    start_date="2026-10-09",
                    end_date="2026-10-12",
                ),
            )
            r.raise_for_status()
            rows += r.json()
            break
        except Exception as e:
            print(y, e)
            time.sleep(20 * (k + 1))
    else:
        raise SystemExit("Open-Meteo request failed")
    print(y, len(rows))
json.dump(dict(lat=la.tolist(), lon=lo.tolist(), data=rows), open(OUT, "w"))
