"""Shared inputs of the ign figures: data paths, the ignition point, the border and the GK-2A navigation."""

import json

import numpy as np

from figkit import paths

GROUP = "ign"
SNAPSHOT = paths.group_dir(GROUP) / "snapshot"

# Ignition point (VIIRS, 2026-10-08 04:06 UTC), lat / lon
IGN_LAT, IGN_LON = 46.883, 119.395


def data(*parts):
    return paths.data(GROUP, *parts)


def border():
    """China–Mongolia border near the fire as lists of (lon, lat), OSM (see snapshot/README.md)."""
    return [p for p in json.load(open(SNAPSHOT / "border_osm.json")) if len(p) > 1]


def geos_lc(lat, lon, sub, cfac, lfac, coff, loff):
    """GK-2A full-disk column / line of a lat/lon (CGMS geostationary projection, normalized geostationary angles)."""
    la = np.radians(lat)
    lo = np.radians(lon)
    c_lat = np.arctan(0.993243 * np.tan(la))
    rl = 6356.7523 / np.sqrt(1 - 0.00675701 * np.cos(c_lat) ** 2)
    r1 = 42164 - rl * np.cos(c_lat) * np.cos(lo - sub)
    r2 = -rl * np.cos(c_lat) * np.sin(lo - sub)
    r3 = rl * np.sin(c_lat)
    rn = np.sqrt(r1**2 + r2**2 + r3**2)
    x = np.degrees(np.arctan(-r2 / r1))
    y = np.degrees(np.arcsin(-r3 / rn))
    return coff + x * 2**-16 * cfac, loff - y * 2**-16 * lfac  # lfac is stored negative: north is up (small line)


def gk2a_bt(d, dn):
    """GK-2A AMI IR counts -> brightness temperature K."""
    L = dn * d.DN_to_Radiance_Gain + d.DN_to_Radiance_Offset
    # AMI IR radiance is mW m-2 sr-1 (cm-1)-1; Planck in wavenumber form, SI units
    nu = 1 / (float(d.channel_center_wavelength) * 1e-6)
    h, k, c = d.Plank_constant_h, d.Boltzmann_constant_k, d.light_speed
    L = np.where(L > 0, L, np.nan) * 1e-5
    te = h * c * nu / k / np.log(1 + 2 * h * c**2 * nu**3 / L)
    return d.Teff_to_Tbb_c0 + d.Teff_to_Tbb_c1 * te + d.Teff_to_Tbb_c2 * te**2


def gk2a_lc(d, lat=IGN_LAT, lon=IGN_LON):
    return geos_lc(lat, lon, d.sub_longitude, d.cfac, d.lfac, d.coff, d.loff)
