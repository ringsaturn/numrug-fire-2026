"""GEFS-Aerosols at the cities and over the fire, from data/weather/gefs/<run>/fFFF.grib2.

Writes data/weather/gefs-points/points.csv (run, lead, valid_utc, point, aod, aod_pom, aod_bc,
pm25, col_bc, col_pom; bilinear at each city) and fire_box.csv (column POM and BC summed over
the fire box, in tonnes, which shows the run in which this fire enters the model's emissions).
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import rasterio

from common import data

POINTS = {  # city means of the monitoring sites (aq_cities.py)
    "Hailar": (119.74, 49.19),
    "Baicheng": (122.83, 45.59),
    "Qiqihar": (123.89, 47.30),
    "Tongliao": (122.27, 43.64),
    "Songyuan": (124.80, 45.15),
    "Xilinhot": (116.09, 43.93),
    "Ulanhot": (122.06, 46.07),
}
FIRE_BOX = (118.8, 46.4, 120.2, 47.6)
BANDS = ["aod", "aod_pom", "aod_bc", "pm25", "col_bc", "col_pom"]


def bilinear(arr, t, lon, lat):
    col = (lon - t.c) / t.a - 0.5
    row = (lat - t.f) / t.e - 0.5
    c0, r0 = int(np.floor(col)), int(np.floor(row))
    dc, dr = col - c0, row - r0
    return (
        arr[:, r0, c0] * (1 - dc) * (1 - dr)
        + arr[:, r0, c0 + 1] * dc * (1 - dr)
        + arr[:, r0 + 1, c0] * (1 - dc) * dr
        + arr[:, r0 + 1, c0 + 1] * dc * dr
    )


def box_sum(arr, t, box, band):
    w, s, e, n = box
    c0, c1 = int((w - t.c) / t.a), int((e - t.c) / t.a)
    r0, r1 = int((n - t.f) / t.e), int((s - t.f) / t.e)
    cell_area = (0.25 * 111.2e3) ** 2 * np.cos(np.radians((s + n) / 2))
    return float(arr[band, r0:r1, c0:c1].sum() * cell_area)  # kg


rows, firerows = [], []
for run_dir in sorted(data("gefs").iterdir()):
    run = datetime.strptime(run_dir.name, "%Y%m%d%H")
    for f in sorted(run_dir.glob("f*.grib2")):
        lead = int(f.stem[1:])
        with rasterio.open(f) as ds:
            arr = ds.read().astype("float64")
            t = ds.transform
        valid = run + timedelta(hours=lead)
        for name, (lon, lat) in POINTS.items():
            v = bilinear(arr, t, lon, lat)
            rows.append(
                {
                    "run": run_dir.name,
                    "lead": lead,
                    "valid_utc": valid,
                    "point": name,
                    **{b: v[i] for i, b in enumerate(BANDS)},
                }
            )
        firerows.append(
            {
                "run": run_dir.name,
                "lead": lead,
                "valid_utc": valid,
                "fire_col_pom_t": box_sum(arr, t, FIRE_BOX, 5) / 1e3,
                "fire_col_bc_t": box_sum(arr, t, FIRE_BOX, 4) / 1e3,
            }
        )
out = data("gefs-points")
out.mkdir(parents=True, exist_ok=True)
pd.DataFrame(rows).to_csv(out / "points.csv", index=False, float_format="%.5g")
fire = pd.DataFrame(firerows)
fire.to_csv(out / "fire_box.csv", index=False, float_format="%.5g")
print(fire[fire["lead"] == 0].to_string(index=False))
