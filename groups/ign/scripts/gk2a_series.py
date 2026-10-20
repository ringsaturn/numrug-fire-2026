"""GK-2A AMI 3.8 / 10.5 µm at the Arxan ignition pixel, 2026-10-08 03:40–04:20 UTC: brightness temperature,
excess over the surrounding background and the line-interpolated scan time -> data/ign/gk2a_ign_series.json."""

import datetime as dt
import glob
import json

import netCDF4
import numpy as np

from common import data, gk2a_bt, gk2a_lc

EPOCH = dt.datetime(2000, 1, 1, 12)
out = []
for f in sorted(glob.glob(str(data("gk2a", "*sw038_fd020ge_*.nc")))):
    t = f[-15:-3]
    row = dict(nominal_utc=f"{t[8:10]}:{t[10:12]}")
    for ch in ("sw038", "ir105"):
        d = netCDF4.Dataset(f.replace("sw038", ch))
        d.set_auto_mask(False)
        c, l = gk2a_lc(d)
        ci, li = int(round(c)), int(round(l))
        img = d["image_pixel_values"]
        win = img[li - 12 : li + 13, ci - 12 : ci + 13].astype(float)
        win = np.where(win >= 2**14 - 2, np.nan, win)
        # 5×5 core around the point; background = median of the 25×25 window outside the central 9×9
        b = gk2a_bt(d, win)
        cen = b[10:15, 10:15]
        ring = b.copy()
        ring[8:17, 8:17] = np.nan
        row[ch] = dict(
            max=round(float(np.nanmax(cen)), 2),
            bg=round(float(np.nanmedian(ring)), 2),
            sd=round(float(np.nanstd(ring)), 2),
        )
        if ch == "sw038":
            j, i = np.unravel_index(np.nanargmax(cen), cen.shape)
            row["hot_px_line_col"] = [li - 2 + int(j), ci - 2 + int(i)]
            frac = li / d.number_of_lines
            t0, t1 = d.observation_start_time, d.observation_end_time
            row["scan_utc_est"] = (EPOCH + dt.timedelta(seconds=float(t0 + frac * (t1 - t0)))).strftime("%H:%M:%S")
            row["line_col"] = [li, ci]
    row["dT38"] = round(row["sw038"]["max"] - row["sw038"]["bg"], 2)
    row["d38_105"] = round(row["sw038"]["max"] - row["ir105"]["max"], 2)
    out.append(row)
    print(
        row["nominal_utc"],
        row["scan_utc_est"],
        "BT3.8 max",
        row["sw038"]["max"],
        "bg",
        row["sw038"]["bg"],
        "±",
        row["sw038"]["sd"],
        "dT",
        row["dT38"],
        "BT10.5",
        row["ir105"]["max"],
    )
json.dump(out, open(data("gk2a_ign_series.json"), "w"), indent=1)
