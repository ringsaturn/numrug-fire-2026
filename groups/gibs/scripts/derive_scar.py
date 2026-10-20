"""Burn-scar masks and areas on the 10-12 and 10-13 GIBS zoom scenes (common.SCENES).

Thresholds in common.scar_layers (red/green > 1.4, green < 75, ...). The 10-13 scenes are also run with
green < 110, a sensitivity test for the 10-13 Terra scene, which sits on the swath edge where the scar
looks orange and its green channel is raised.

Writes scar/scar_masks.npz (<id>_main, <id>_all: largest patch and all patches >= 5 km², hole-filled; ids
ending in -g110 for the sensitivity run) and scar/scar_areas.json (km² per scene: main patch, all patches,
main patch outside the OSM border line, and the detached patches; plus the 10-12 five-scene summary).
"""

import json

import numpy as np

from common import SCENES, ZoomGrid, data, fc, rgb, scar_layers, tile


def detached(g, s):
    out = []
    lab, allc, main = s["lab"], s["filled"], s["main"]
    for i in np.unique(lab[allc & ~main]):
        if i == 0:
            continue
        k = lab == i
        ys, xs = np.where(k)
        out.append(
            dict(
                km2=round(float(g.pxa[ys, xs].sum()), 1),
                lat=round(float(g.lat[ys].mean()), 3),
                lon=round(float(g.lon[xs].mean()), 3),
                china_km2=round(g.area(k & ~g.in_mng), 1),
            )
        )
    return sorted(out, key=lambda c: -c["km2"])


def main():
    g = ZoomGrid()
    masks, areas = {}, {}
    runs = [(sid, d, sat, 75) for sid, d, sat, _ in SCENES] + [
        (sid, d, sat, 110) for sid, d, sat, _ in SCENES if d == "2026-10-13"
    ]
    for sid, d, sat, gmax in runs:
        a = rgb(tile("zoom", d, sat, fc(sat)))
        s = scar_layers(a, g.pxa, gmax)
        key = sid if gmax == 75 else f"{sid}-g110"
        masks[f"{key}_main"], masks[f"{key}_all"] = s["main"], s["filled"]
        r = dict(
            area_main=g.area(s["main"]),
            area_allcomp=g.area(s["filled"]),
            china=g.area(s["main"] & ~g.in_mng),
            detached=detached(g, s),
        )
        areas[key] = r
        print(
            f"{key:22s} main {r['area_main']:6.0f}  all {r['area_allcomp']:6.0f}  outside the line {r['china']:5.1f}",
            flush=True,
        )
    a12 = [areas[sid]["area_main"] for sid, d, *_ in SCENES if d == "2026-10-12"]
    areas["summary_20261012"] = dict(min=min(a12), max=max(a12), median=float(np.median(a12)))
    print("10-12 five scenes", areas["summary_20261012"])
    data("scar").mkdir(parents=True, exist_ok=True)
    np.savez_compressed(data("scar", "scar_masks.npz"), **masks)
    json.dump(areas, open(data("scar", "scar_areas.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
