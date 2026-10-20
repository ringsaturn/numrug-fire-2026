"""Area and extent of the separate scar south of the main one (burned 10-15, first clear on 10-16).

Reads the 10-16 NOAA-21 and S-NPP 'anim' tiles (118.8–120.2°E, 46.4–47.6°N, 1400 x 1600), thresholds
red/green > 1.4, green < 75, red > 20 with one 3x3 opening (no size filter, no hole fill), and lists every
component lying wholly south of 46.56°N and larger than 1 km², with how many sampled pixels fall on the
Mongolian side of the OSM border. Writes scar/south_scar_20261016.json.
"""

import json

import numpy as np
from PIL import Image
from scipy import ndimage as nd
from shapely.geometry import Point, Polygon

from common import BOXES, FC_VIIRS, data, main_line, mongolia_polygon, osm_border_south, tile

W, S, E, N = BOXES["anim"][0]
MNG = Polygon(mongolia_polygon(main_line(osm_border_south())))


def components(path):
    a = np.asarray(Image.open(path).convert("RGBA")).astype(float)
    r, g = a[..., 0], a[..., 1]
    h, w = r.shape
    lat = N - (np.arange(h) + 0.5) * (N - S) / h
    lon = W + (np.arange(w) + 0.5) * (E - W) / w
    A = np.broadcast_to(((111.32 * np.cos(np.radians(lat)) * (E - W) / w) * (110.95 * (N - S) / h))[:, None], r.shape)
    m = nd.binary_opening((r > 1.4 * g) & (g < 75) & (r > 20), np.ones((3, 3), bool))
    lab, n = nd.label(m)
    out = []
    for k in range(1, n + 1):
        yy, xx = np.nonzero(lab == k)
        if lat[yy].max() < 46.56 and A[yy, xx].sum() > 1:
            ys, xs = lat[yy], lon[xx]
            side = sum(MNG.contains(Point(x, y)) for x, y in zip(xs[::20], ys[::20]))
            out.append(
                dict(
                    km2=round(float(A[yy, xx].sum()), 1),
                    lat=[round(float(ys.min()), 3), round(float(ys.max()), 3)],
                    lon=[round(float(xs.min()), 3), round(float(xs.max()), 3)],
                    mng_side_samples=[int(side), len(xs[::20])],
                )
            )
    return out


def main():
    res = {}
    for sat in ("VIIRS_NOAA21", "VIIRS_SNPP"):
        res[sat] = components(tile("anim", "2026-10-16", sat, FC_VIIRS))
        for c in res[sat]:
            print(sat, c)
    data("scar").mkdir(parents=True, exist_ok=True)
    json.dump(res, open(data("scar", "south_scar_20261016.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
