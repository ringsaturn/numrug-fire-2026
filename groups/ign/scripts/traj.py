"""Kinematic back trajectories (36 h, 10-min midpoint steps, 10 m / 925 / 850 / 700 hPa winds of fetch_wind.py) from
Hailar, Baicheng and Ulanhot -> data/ign/traj/back_traj.json. Keys are '<site> <arrival UTC+8 %m-%dT%H> <level>'."""

import datetime as dt
import json

import numpy as np
from scipy.interpolate import RegularGridInterpolator

from common import data

J = json.load(open(data("traj", "wind_ecmwf_hist.json")))
la = np.array(J["lat"])
lo = np.array(J["lon"])
T = [dt.datetime.fromisoformat(t) for t in J["data"][0]["hourly"]["time"]]
nt = len(T)


def field(p):
    U = np.zeros((nt, len(la), len(lo)))
    Vv = np.zeros_like(U)
    for k, d in enumerate(J["data"]):
        i, j = divmod(k, len(lo))
        s = np.array(d["hourly"][f"wind_speed_{p}"], float)
        r = np.radians(np.array(d["hourly"][f"wind_direction_{p}"], float))
        U[:, i, j] = -s * np.sin(r)
        Vv[:, i, j] = -s * np.cos(r)
    t = np.arange(nt, dtype=float)
    return (
        RegularGridInterpolator((t, la, lo), U, bounds_error=False, fill_value=np.nan),
        RegularGridInterpolator((t, la, lo), Vv, bounds_error=False, fill_value=np.nan),
    )


FIRE = dict(S=46.55, N=47.45, W=118.8, E=120.0)


def back(p, lat, lon, t_end, hours=36, dt_h=1 / 6):
    fu, fv = field(p)
    t = (t_end - T[0]).total_seconds() / 3600
    path = [(t, lat, lon)]
    for _ in range(int(hours / dt_h)):

        def vel(tt, y, x):
            q = np.array([[tt, y, x]])
            return fu(q)[0], fv(q)[0]

        u, v = vel(t, lat, lon)
        ym = lat - v * dt_h * 3600 / 111e3 / 2
        xm = lon - u * dt_h * 3600 / (111e3 * np.cos(np.radians(lat))) / 2
        u, v = vel(t - dt_h / 2, ym, xm)
        lat -= v * dt_h * 3600 / 111e3
        lon -= u * dt_h * 3600 / (111e3 * np.cos(np.radians(ym)))
        t -= dt_h
        if np.isnan(lat):
            break
        path.append((t, lat, lon))
    return path


res = {}
U = dt.datetime
for name, (y, x), ends in [
    ("hailar", (49.22, 119.75), [U(2026, 10, 10, 23), U(2026, 10, 11, 1), U(2026, 10, 11, 3)]),
    ("baicheng", (45.62, 122.83), [U(2026, 10, 12, 8), U(2026, 10, 12, 11), U(2026, 10, 12, 14)]),
    ("ulanhot", (46.08, 122.05), [U(2026, 10, 12, 6), U(2026, 10, 12, 9)]),
]:
    for te in ends:
        for p in ("10m", "925hPa", "850hPa", "700hPa"):
            pa = back(p, y, x, te)
            hit = [
                (T[0] + dt.timedelta(hours=t), a, b)
                for t, a, b in pa
                if FIRE["S"] <= a <= FIRE["N"] and FIRE["W"] <= b <= FIRE["E"]
            ]
            dmin = min((np.hypot((b - 119.4) * 76, (a - 46.95) * 111), T[0] + dt.timedelta(hours=t)) for t, a, b in pa)
            k = f"{name} {te + dt.timedelta(hours=8):%m-%dT%H} {p}"
            res[k] = dict(
                passes_fire=bool(hit),
                first_in_fire_utc8=(hit[-1][0] + dt.timedelta(hours=8)).strftime("%m-%d %H:%M") if hit else None,
                hours_from_fire=round((te - hit[0][0]).total_seconds() / 3600, 1) if hit else None,
                closest_km=round(float(dmin[0])),
                closest_utc8=(dmin[1] + dt.timedelta(hours=8)).strftime("%m-%d %H:%M"),
                path=[
                    ((T[0] + dt.timedelta(hours=t)).strftime("%m-%dT%H"), round(a, 2), round(b, 2))
                    for t, a, b in pa[::6]
                ],
            )
            print(k, {kk: vv for kk, vv in res[k].items() if kk != "path"})
json.dump(res, open(data("traj", "back_traj.json"), "w"), indent=1)
