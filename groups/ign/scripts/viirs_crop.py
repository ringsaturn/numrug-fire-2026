"""Crop VIIRS L1B (I-bands, plus M3/M4/M5 for NOAA-21) around the Arxan ignition point onto a regular ~375 m lat/lon grid
-> data/ign/viirs_<pass>.npz."""

import glob

import h5py
import numpy as np
from pyresample import geometry, kd_tree

from common import data

S, N, W, E, D = 46.30, 47.40, 118.70, 120.30, 0.0035
lon = np.arange(W, E, D)
lat = np.arange(N, S, -D)
area = geometry.GridDefinition(*np.meshgrid(lon, lat))


def band(f, b):
    d = f["observation_data/" + b]
    raw = d[...]
    if b + "_brightness_temperature_lut" in f["observation_data"]:
        lut = f["observation_data/" + b + "_brightness_temperature_lut"][...]
        out = lut[np.clip(raw, 0, len(lut) - 1)].astype("f4")
    else:
        out = raw * d.attrs["scale_factor"][0] + d.attrs["add_offset"][0]
    return np.where(raw >= 65528, np.nan, out).astype("f4")


def crop(l1, geo, bands):
    g = h5py.File(geo)
    la = g["geolocation_data/latitude"][...]
    lo = g["geolocation_data/longitude"][...]
    vz = g["geolocation_data/sensor_zenith"][...]
    vz = vz * g["geolocation_data/sensor_zenith"].attrs.get("scale_factor", [1])[0]
    m = (la > S - 0.3) & (la < N + 0.3) & (lo > W - 0.3) & (lo < E + 0.3)
    r, c = np.where(m)
    sl = (slice(r.min(), r.max() + 1), slice(c.min(), c.max() + 1))
    sw = geometry.SwathDefinition(lons=lo[sl], lats=la[sl])
    f = h5py.File(l1)
    out = {}
    for b in bands:
        # VIIRS drops bow-tie overlap pixels as fill; resample only the valid ones so the gaps close from neighbours
        v = band(f, b)[sl]
        ok = np.isfinite(v)
        sv = geometry.SwathDefinition(lons=lo[sl][ok], lats=la[sl][ok])
        out[b] = kd_tree.resample_nearest(
            sv, v[ok], area, radius_of_influence=1000 if b[0] == "I" else 2000, fill_value=np.nan
        )
    out["vza"] = kd_tree.resample_nearest(sw, vz[sl].astype("f4"), area, radius_of_influence=1200, fill_value=np.nan)
    return out


P = [
    (
        "N21_0406",
        "VJ202IMG.A2026281.0406",
        "VJ203IMG.A2026281.0406",
        "VJ202MOD.A2026281.0406",
        "VJ203MOD.A2026281.0406",
    ),
    ("NPP_0442", "VNP02IMG.A2026281.0442", "VNP03IMG.A2026281.0442", None, None),
    ("N20_0500", "VJ102IMG.A2026281.0500", "VJ103IMG.A2026281.0500", None, None),
]
for tag, l1, geo, ml1, mgeo in P:
    fn = lambda p: glob.glob(str(data("viirs", p + "*.nc")))[0]
    o = crop(fn(l1), fn(geo), ["I01", "I02", "I03", "I04", "I05"])
    if ml1:
        o.update(crop(fn(ml1), fn(mgeo), ["M03", "M04", "M05", "M11", "M13"]))
    np.savez_compressed(data(f"viirs_{tag}.npz"), lat=lat, lon=lon, **o)
    print(tag, {k: (np.nanmin(v).round(2), np.nanmax(v).round(2)) for k, v in o.items()})
