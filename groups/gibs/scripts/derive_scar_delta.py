"""Burn-scar change from 10-12 to 10-14 / 10-15 against the 10-12 NOAA-21 main patch (scar/scar_masks.npz).

Same thresholds as derive_scar.py, applied to the six VIIRS zoom scenes of 10-14 and 10-15. The new area
(raw scar, holes not filled, minus the reference) is split into: inside the unburned island of 10-12
(ISL box), the east front (EAST box), and an edge band by distance to the reference. est_km2 is the
hole-filled scar minus the filled-but-unburned part of the island. Writes scar/scar_delta_20261015.json.
"""

import json

import numpy as np
from scipy import ndimage

from common import FC_VIIRS, ZoomGrid, data, rgb, scar_layers, tile

SCENES = [
    ("2026-10-14", "VIIRS_NOAA21", "NOAA-21", "03:55"),
    ("2026-10-14", "VIIRS_SNPP", "S-NPP", "04:32"),
    ("2026-10-14", "VIIRS_NOAA20", "NOAA-20", "04:53"),
    ("2026-10-15", "VIIRS_SNPP", "S-NPP", "04:14"),
    ("2026-10-15", "VIIRS_NOAA20", "NOAA-20", "04:32"),
    ("2026-10-15", "VIIRS_NOAA21", "NOAA-21", "05:16"),
]


def main():
    g = ZoomGrid()
    lat, lon = g.lat[:, None], g.lon[None, :]
    ref = np.load(data("scar", "scar_masks.npz"))["20261012-noaa21_main"]
    ISL = (lat > 46.95) & (lat < 47.25) & (lon > 119.25) & (lon < 119.7)
    EAST = (lat > 46.85) & (lat < 47.13) & (lon > 119.70) & (lon < 119.93)
    dref = ndimage.distance_transform_edt(~ref) * g.px_km
    A = g.area
    out = {
        "ref": "2026-10-12 04:32 NOAA-21 main patch",
        "ref_km2": A(ref),
        "island_unburned_1012_km2": A(ISL & ~ref),
        "scenes": {},
    }
    for d, sat, nm, t in SCENES:
        a = rgb(tile("zoom", d, sat, FC_VIIRS)).astype(int)
        s = scar_layers(a, g.pxa)
        raw, fill = s["raw"], s["filled"]
        cl = ndimage.binary_dilation(a.min(-1) > 150, iterations=3)  # bright cloud, dilated
        z = ISL & ~ref
        new = raw & ~ref
        r = dict(
            clear_scar=float((~cl & ref).sum() / ref.sum()),
            clear_island=float((~cl & z).sum() / z.sum()),
            raw=A(raw),
            filled=A(fill),
            island_new=A(new & ISL),
            island_new_clear=A(new & ISL & ~cl),
            east_new=A(new & EAST & ~ISL),
            edge_le0p5=A(new & ~ISL & ~EAST & (dref <= 0.5)),
            edge_0p5_1p5=A(new & ~ISL & ~EAST & (dref > 0.5) & (dref <= 1.5)),
            other_gt1p5=A(new & ~ISL & ~EAST & (dref > 1.5)),
            filled_island_unburned=A(fill & ~raw & ISL),
            china_new=A(new & ~g.in_mng),
        )
        r["est_km2"] = r["filled"] - r["filled_island_unburned"]
        out["scenes"][f"{d} {t} {nm}"] = r
        print(d, t, nm, {k: round(v, 1) for k, v in r.items()})
    json.dump(out, open(data("scar", "scar_delta_20261015.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
