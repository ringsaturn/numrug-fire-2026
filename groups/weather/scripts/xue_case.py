# Adapted from github.com/ringsaturn/xue, .agents/skills/synoptic-analysis/scripts/case_data.py and
# xue_stac.py (MIT OR Apache-2.0, © 2026 Han Xiao): the store reading and sounding helpers only.
"""Cut the case the upper/surface/meteogram/skew-T figures read out of the rebuilt model runs.

Reads the Zarr stores that `xuebuild build-local` wrote (xue_build.sh) and the archived xue
sounding issue that was live at the original fetch (2026-10-13 14:36Z), and writes
data/weather/xue-case/:

- fields.npz   `<src>:<bundle>:<var>:<time>` maps over 40–54°N 108–132°E (+ `<src>:<bundle>:lat|lon`)
- point.npz    `<src>:<bundle>:<var>` series at 47.0°N 119.4°E (+ `<src>:<bundle>:time`, epoch s)
- soundings.json  station lines keyed by WMO number
- meta.json    the runs, times, box and point

Imported by the figure scripts for the shared helpers (parse_time, ascent_at, point_frame, …).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from common import USER_AGENT, data

MISSING = -32768
RUNS = {"ecmwf": "2026101300", "gfs": "2026101306", "ifshres": "2026101300", "aifs": "2026101306"}
MAP_SOURCES = ["ecmwf", "gfs"]
MAP_BUNDLES = ["prmsl", "hgt500", "wind250", "prate", "wind10m"]
BOX = [40.0, 54.0, 108.0, 132.0]  # S N W E
TIMES = ["2026-10-13T12:00Z", "2026-10-17T12:00Z"]
POINT = [47.0, 119.4]
POINT_SOURCES = ["ecmwf", "gfs", "ifshres", "aifs"]
POINT_BUNDLES = ["prmsl", "prate", "gust", "wind10m"]
SOUNDINGS = ["50527", "54102", "54135"]
SOUNDING_ISSUE = "https://dataset.ringsaturn.me/xue/sounding/2026/10/13/sounding.2026101314/"
CASE = data("xue-case")


# --- time and sounding helpers (case_data.py) ------------------------------------


def norm_time(t: str) -> str:
    """'2026-09-21T06Z' | '2026-09-21T06:00Z' | '2026-09-21T06:00:00Z' -> '2026-09-21T06:00Z'."""
    t = t.strip().rstrip("Z")
    if len(t) == 13:
        t += ":00"
    return t[:16] + "Z"


def parse_time(t: str) -> datetime:
    return datetime.strptime(norm_time(t), "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)


def ascent_at(station: dict, time: str) -> dict | None:
    t = norm_time(time)
    for a in station["soundings"]:
        if norm_time(a["time"]) == t:
            return a
    return None


def profile(ascent: dict, p_min: int = 10000):
    """Arrays (p hPa, z, t °C, td °C, wd, ws m/s) with NaN for missing, above p_min."""
    p = np.array(ascent["p"], float)
    ok = (p != MISSING) & (p >= p_min)

    def f(k, scale, off=0.0):
        a = np.array(ascent[k], float)[ok]
        return np.where(a == MISSING, np.nan, a / scale + off)

    return p[ok] / 100, f("z", 1), f("t", 100, -273.15), f("td", 100, -273.15), f("wd", 1), f("ws", 10)


# --- point series (case_data.py) ---------------------------------------------------


def point_series(pt, src: str, bundle: str, var: str, tz_hours: float):
    tz = timezone(timedelta(hours=tz_hours))
    t = pt[f"{src}:{bundle}:time"].astype("int64")
    return [datetime.fromtimestamp(int(x), tz=timezone.utc).astimezone(tz) for x in t], pt[f"{src}:{bundle}:{var}"]


def point_frame(pt, src: str, tz_hours: float) -> dict:
    """Aligned columns for a source: t (local datetimes), p, ws, gust, rate."""
    keys = {k.split(":")[1] for k in pt.files if k.startswith(src + ":")}
    if "wind10m" not in keys and "prate" not in keys:
        return {}
    base = "wind10m" if "wind10m" in keys else "prate"
    t, _ = point_series(pt, src, base, "ugrd10m" if base == "wind10m" else "prate", tz_hours)

    def col(b, v):
        if b not in keys:
            return np.full(len(t), np.nan)
        tt, s = point_series(pt, src, b, v, tz_hours)
        if len(tt) == len(t):
            return s
        m = dict(zip(tt, s))
        return np.array([m.get(x, np.nan) for x in t])

    u, v = col("wind10m", "ugrd10m"), col("wind10m", "vgrd10m")
    return {
        "t": t,
        "p": col("prmsl", "prmsl"),
        "ws": np.hypot(u, v),
        "gust": col("gust", "gust"),
        "rate": col("prate", "prate"),
    }


def accumulate(t, rate):
    ts = np.array([x.timestamp() for x in t])
    acc = np.zeros(len(rate))
    for i in range(1, len(rate)):
        acc[i] = acc[i - 1] + (0 if np.isnan(rate[i]) else rate[i] * (ts[i] - ts[i - 1]) / 3600)
    return acc


# --- stores (xue_stac.py) ------------------------------------------------------------


def open_store(path):
    """One bundle store as an xarray Dataset, every array dequantized to its physical unit
    (float32, NaN where nodata), including the log1p codebook that CF decoding cannot express."""
    import xarray as xr

    ds = xr.open_zarr(path, consolidated=True)
    meta = ds.attrs["xue"]
    if isinstance(meta, str):
        meta = json.loads(meta)
    return xr.Dataset(
        {v["id"]: _dequantize(ds[v["id"]], v) for v in meta["variables"]}, coords=ds.coords, attrs={"xue": meta}
    )


def _dequantize(da, var: dict):
    q = var["quantization"]
    # xarray applied scale_factor/add_offset for linear codebooks and masked _FillValue;
    # for log1p it returned raw codes with nodata masked.
    if q["type"] == "linear":
        return da.astype("float32").assign_attrs(units=var["unit"], long_name=var["label"])
    if q["type"] == "log1p":
        import xarray as xr

        span = q["maximumCode"] - 1
        lo = np.log1p(q["trace"] / q["scale"])
        hi = np.log1p(q["maximum"] / q["scale"])
        rate = q["scale"] * np.expm1(lo + (da - 1) / span * (hi - lo))
        rate = xr.where(da == q["zeroCode"], 0.0, rate)
        return rate.astype("float32").assign_attrs(units=var["unit"], long_name=var["label"])
    raise ValueError(f"unknown codebook {q['type']}")


def sel_box(da, south, north, west, east):
    """Latitude runs north-to-south in every store, so the slice is (north, south)."""
    return da.sel(latitude=slice(north, south), longitude=slice(west, east))


def sel_time(da, t):
    """The frame nearest a valid time; raises if it is outside the axis."""
    t = np.datetime64(t.replace("Z", ""))
    times = da.time.values
    if t < times[0] or t > times[-1]:
        raise ValueError(f"{t} is outside the axis {times[0]} .. {times[-1]}")
    return da.sel(time=t, method="nearest")


def stores(run_dir: Path) -> dict[str, Path]:
    return {p.name[:-5]: p for p in sorted(run_dir.glob("*.zarr")) if not p.name.endswith(".series.zarr")}


def fetch_fields(out: dict):
    for src in MAP_SOURCES:
        st = stores(data("xue", "local", f"{src}.{RUNS[src]}"))
        for b in MAP_BUNDLES:
            ds = open_store(st[b])
            for v in ds.data_vars:
                da = sel_box(ds[v], *BOX)
                for T in TIMES:
                    out[f"{src}:{b}:{v}:{T}"] = sel_time(da, T).values.astype("float32")
                out[f"{src}:{b}:lat"] = da.latitude.values
                out[f"{src}:{b}:lon"] = da.longitude.values
            print(f"  {src} {b}", file=sys.stderr)


def fetch_point(out: dict, cells: dict):
    # The meteogram spans the whole axis, so it reads the longer point builds (local-full).
    for src in POINT_SOURCES:
        st = stores(data("xue", "local-full", f"{src}.{RUNS[src]}"))
        for b in POINT_BUNDLES:
            if b not in st:
                continue
            ds = open_store(st[b])
            for v in ds.data_vars:
                s = ds[v].sel(latitude=POINT[0], longitude=POINT[1], method="nearest")
                out[f"{src}:{b}:{v}"] = s.values.astype("float32")
                out[f"{src}:{b}:time"] = s.time.values.astype("datetime64[s]").astype("int64")
                cells[src] = [float(s.latitude), float(s.longitude)]
        print(f"  point {src}", file=sys.stderr)


def fetch_soundings() -> dict:
    import requests

    sess = requests.Session()
    sess.headers["User-Agent"] = USER_AGENT
    idx = sess.get(SOUNDING_ISSUE + "index.json", timeout=60).json()
    out = {}
    for s in idx["stations"]:
        if s["wmo"] in SOUNDINGS or s["id"] in SOUNDINGS:
            r = sess.get(
                SOUNDING_ISSUE + "soundings.jsonl",
                timeout=60,
                headers={"Range": f"bytes={s['offset']}-{s['offset'] + s['length'] - 1}"},
            )
            r.raise_for_status()
            out[s["wmo"] or s["id"]] = json.loads(r.content)
    print(f"  soundings {sorted(out)} from issue generated {idx.get('generated')}", file=sys.stderr)
    return out


def main():
    CASE.mkdir(parents=True, exist_ok=True)
    fields, pt, cells = {}, {}, {}
    fetch_fields(fields)
    np.savez_compressed(CASE / "fields.npz", **fields)
    fetch_point(pt, cells)
    np.savez_compressed(CASE / "point.npz", **pt)
    (CASE / "soundings.json").write_text(json.dumps(fetch_soundings()))
    meta = {
        "box": BOX,
        "times": TIMES,
        "sources": MAP_SOURCES,
        "runs": {k: f"{k}.{v}" for k, v in RUNS.items()},
        "point": POINT,
        "point_sources": POINT_SOURCES,
        "point_cell": cells,
        "sounding_issue": SOUNDING_ISSUE,
    }
    (CASE / "meta.json").write_text(json.dumps(meta, indent=1))
    print(f"wrote {CASE}", file=sys.stderr)


if __name__ == "__main__":
    main()
