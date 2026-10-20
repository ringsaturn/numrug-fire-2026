"""Rebuild Open-Meteo forecast-API responses as they were served on 2026-10-13, from the Single
Runs API (single-runs-api.open-meteo.com).

For every hour the forecast API shows the newest run (init <= hour) that has a value there:
each new run overwrites from its first step on, and a shorter run leaves the older run's tail in
place. This script stitches the archived runs the same way, up to the last run each model had
published at the moment of the original request. A run's analysis-hour gust is skipped, because
the archive does not keep it. Checked against historical-forecast-api over 10-07..10-12: max |Δ| = 0.

Raw run responses are cached in data/weather/om/runs/; the stitched responses go to data/weather/om/.

    om_runs.py [NAME ...]      # default: every request in REQUESTS
"""

import json
import sys
import time
from datetime import datetime, timedelta

import pandas as pd
import requests

from common import USER_AGENT, data

API = "https://single-runs-api.open-meteo.com/v1/forecast"
CACHE = data("om", "runs")
STEP_H = 6
FIVE = "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m,precipitation"

# name: (lat, lon, start, end, variables, {model: cutoff}, suffix columns with the model)
# A cutoff is the last run (UTC) the forecast API was serving; "PART@CUTOFF+PART@CUTOFF" is a
# seamless model whose parts were at different runs (the first part wins where it has a value).
REQUESTS = {
    # fire-weather: forecast API, default model (best_match = ECMWF IFS 9 km here), 10-13 05:28Z.
    # The 10-13 00Z run's files reached the archive at 05:30Z, after the request.
    "fire_weather_20261013T0528Z": (
        47.0,
        119.4,
        "2026-10-05T00",
        "2026-10-21T23",
        "temperature_2m,dew_point_2m,relative_humidity_2m,precipitation,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
        {"ecmwf_ifs": "2026-10-12T18"},
        False,
    ),
    # models-daily, previous report (10-13 05:34Z). gfs_seamless then took T, RH, wind and
    # precipitation from GFS 0.13° 10-13 00Z, and gusts from GFS 0.25° 10-12 18Z (0.13° has no gust).
    "models_20261013T0534Z": (
        47.0,
        119.5,
        "2026-10-12T00",
        "2026-10-21T23",
        FIVE,
        {
            "ecmwf_ifs025": "2026-10-12T18",
            "gfs_seamless": "ncep_gfs013@2026-10-13T00+ncep_gfs025@2026-10-12T18",
            "cma_grapes_global": "2026-10-12T18",
            "icon_seamless": "2026-10-13T00",
        },
        True,
    ),
    # models-daily, this report (10-13 14:14Z): every model at its 10-13 06Z run.
    "models_20261013T1414Z": (
        47.0,
        119.5,
        "2026-10-12T00",
        "2026-10-21T23",
        FIVE,
        {
            "ecmwf_ifs025": "2026-10-13T06",
            "gfs_seamless": "2026-10-13T06",
            "cma_grapes_global": "2026-10-13T06",
            "icon_seamless": "2026-10-13T06",
        },
        True,
    ),
}

S = requests.Session()
S.headers["User-Agent"] = USER_AGENT


def run(model, init, lat, lon, vars_):
    f = CACHE / f"{model}_{init:%Y%m%d%H}_{lat}_{lon}.json"
    if not f.exists():
        for k in range(5):
            r = S.get(
                API,
                params=dict(
                    latitude=lat,
                    longitude=lon,
                    hourly=vars_,
                    models=model,
                    run=f"{init:%Y-%m-%dT%H:%M}",
                    wind_speed_unit="ms",
                    timezone="GMT",
                    forecast_days=16,
                ),
                timeout=120,
            )
            if r.status_code == 200:
                break
            print(model, init, r.status_code, r.text[:200], file=sys.stderr)
            if r.status_code == 400:
                return None  # run not served
            time.sleep(5 * (k + 1))
        else:
            return None
        f.write_text(r.text)
    d = json.loads(f.read_text())
    if "hourly" not in d:
        return None
    h = pd.DataFrame(d["hourly"])
    h["time"] = pd.to_datetime(h.time)
    return d, h.set_index("time")


def stitch(model, cutoff, lat, lon, start, end, vars_):
    first = start - timedelta(hours=24)  # older runs only matter for the window's first hours
    inits, t = [], cutoff
    while t >= first:
        inits.append(t)
        t -= timedelta(hours=STEP_H)
    out, used, head = None, {}, None
    for init in inits:  # newest first; fill only what is still empty
        got = run(model, init, lat, lon, vars_)
        if got is None:
            continue
        d, h = got
        head = head or d
        h = h[(h.index >= init) & (h.index >= start) & (h.index <= end)]
        if out is None:
            out = pd.DataFrame(index=pd.date_range(start, end, freq="h"), columns=h.columns, dtype=float)
        for c in h.columns:
            m = out[c].isna() & out.index.isin(h.index)
            if c.startswith("wind_gusts"):
                m &= out.index != init
            vals = h[c].reindex(out.index)
            fill = m & vals.notna()
            if fill.any():
                out.loc[fill, c] = vals[fill]
                used.setdefault(c, set()).add(init.strftime("%m-%d %HZ"))
    return head, out, {k: sorted(v) for k, v in used.items()}


def build(name):
    lat, lon, start, end, vars_, models, suffix = REQUESTS[name]
    start, end = datetime.fromisoformat(start), datetime.fromisoformat(end)
    hourly, info, head = {}, {}, None
    for model, cut in models.items():
        parts = [p.split("@") for p in cut.split("+")] if "@" in cut else [(model, cut)]
        df, used, hd = None, {}, None
        for pm, pc in parts:
            h1, d1, u1 = stitch(pm, datetime.strptime(pc, "%Y-%m-%dT%H"), lat, lon, start, end, vars_)
            hd = hd or h1
            used[f"{pm}@{pc}"] = u1
            df = d1 if df is None else df.combine_first(d1)
        head = head or hd
        info[model] = {"cutoff": cut, "runs_used": used, "grid": [hd["latitude"], hd["longitude"]]}
        for c in df.columns:
            hourly[f"{c}_{model}" if suffix else c] = [None if pd.isna(v) else float(v) for v in df[c]]
        hourly["time"] = [t.strftime("%Y-%m-%dT%H:%M") for t in df.index]
    res = {k: head[k] for k in ("latitude", "longitude", "elevation")}
    res["hourly"] = hourly
    res["rebuilt_from"] = info
    dest = data("om", f"{name}.json")
    dest.write_text(json.dumps([res]))
    print(dest, file=sys.stderr)


if __name__ == "__main__":
    CACHE.mkdir(parents=True, exist_ok=True)
    for name in sys.argv[1:] or REQUESTS:
        build(name)
