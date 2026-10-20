"""scar-delta-20261015: new burn scar on 10-14 S-NPP and 10-15 NOAA-21 against the 10-12 NOAA-21 reference, with the
same-day daytime FIRMS detections (2 x 2, notes in the fourth cell).

Reference mask from scar/scar_masks.npz, new-area numbers from scar/scar_delta_20261015.json, FIRMS points from
snapshot/firms_box_20261014_20261015.csv.
"""

import csv
import json

import matplotlib.patheffects as pe
import numpy as np
from matplotlib.lines import Line2D

from common import (
    ARXAN,
    FC_VIIRS,
    ZoomGrid,
    data,
    deg_fmt,
    halo,
    init,
    line,
    local,
    osm_border,
    plot_lines,
    rgb,
    save,
    scar_layers,
    tile,
    utc,
)

lang = init(__file__)
import matplotlib.pyplot as plt  # noqa: E402

T = lang.T
F = "scar-delta-20261015"
PE = [pe.withStroke(linewidth=2.2, foreground="black")]
g = ZoomGrid()
ref = np.load(data("scar", "scar_masks.npz"))["20261012-noaa21_main"]
J = json.load(open(data("scar", "scar_delta_20261015.json")))["scenes"]
FIRMS = list(csv.DictReader(open("snapshot/firms_box_20261014_20261015.csv")))
OSM = osm_border()


def scene(day, sat):
    a = rgb(tile("zoom", day, sat, FC_VIIRS)).astype(int)
    return a, scar_layers(a, g.pxa)["raw"]


a14, raw14 = scene("2026-10-14", "VIIRS_SNPP")
a15, raw15 = scene("2026-10-15", "VIIRS_NOAA21")
t12, t14, t15 = (
    local(utc(d, t)) for d, t in (("2026-10-12", "04:32"), ("2026-10-14", "04:32"), ("2026-10-15", "05:16"))
)
PANELS = [
    (
        rgb(tile("zoom", "2026-10-12", "VIIRS_NOAA21", FC_VIIRS)),
        None,
        T(f"{F}.ref", md=lang.md(t12), local=lang.hm(t12), area=lang.num(g.area(ref))),
        [],
    ),
    (
        a14,
        raw14,
        T(
            f"{F}.new_1014",
            md=lang.md(t14),
            local=lang.hm(t14),
            area=lang.num(J["2026-10-14 04:32 S-NPP"]["island_new"]),
        ),
        [r for r in FIRMS if r["t"] == "2026-10-14 04:32" and r["sat"] == "N"],
    ),
    (
        a15,
        raw15,
        T(
            f"{F}.new_1015",
            md=lang.md(t15),
            local=lang.hm(t15),
            area=lang.num(J["2026-10-15 05:16 NOAA-21"]["island_new"]),
        ),
        [r for r in FIRMS if r["t"].startswith("2026-10-15") and r["dn"] == "D" and float(r["lat"]) > 46.9],
    ),
]

fig, axs = plt.subplots(2, 2, figsize=(7.2, 8.0), constrained_layout=True)
for k, (ax, (a, raw, title, pts)) in enumerate(zip(axs.flat, PANELS)):
    ax.imshow(a, extent=g.ext, aspect=1 / np.cos(np.radians(47)))
    cs = ax.contour(g.lon, g.lat, ref.astype(float), [0.5], colors=T(f"{F}.ref_line.color"), linewidths=0.9)
    cs.set(**halo(T(f"{F}.ref_line.halo")))
    if raw is not None:
        ax.contour(g.lon, g.lat, (raw & ~ref).astype(float), [0.5], colors="magenta", linewidths=1.0)
    plot_lines(ax, OSM, **line(lang, f"{F}.osm"), **halo(T(f"{F}.osm.halo")))
    if pts:
        ax.scatter(
            [float(r["lon"]) for r in pts],
            [float(r["lat"]) for r in pts],
            s=14,
            c="orange",
            edgecolor="k",
            lw=0.4,
            zorder=5,
        )
    ax.plot(*ARXAN, marker="s", ms=4, mfc="white", mec="black")
    ax.annotate(
        T(f"{F}.arxan"),
        ARXAN,
        xytext=(-8, 6),
        textcoords="offset points",
        ha="right",
        color="white",
        fontsize=9,
        path_effects=PE,
    )
    ax.set_xlim(g.ext[0], g.ext[1])
    ax.set_ylim(g.ext[2], g.ext[3])
    ax.set_title(title, fontsize=10)
    deg_fmt(ax, "{:.1f}")
    ax.tick_params(labelsize=9)
    ax.set_xticks([119.0, 119.5, 120.0])
    ax.set_yticks([46.6, 46.8, 47.0, 47.2, 47.4])
    if k == 1:
        ax.set_yticklabels([])
ax = axs[1, 1]
ax.axis("off")
ax.legend(
    handles=[
        Line2D(
            [],
            [],
            color=T(f"{F}.ref_line.color"),
            lw=1.5,
            label=T(f"{F}.legend_ref"),
            **halo(T(f"{F}.ref_line.legend_halo")),
        ),
        Line2D([], [], color="magenta", lw=1.5, label=T(f"{F}.legend_new")),
        Line2D([], [], label=T(f"{F}.border_osm"), **line(lang, f"{F}.osm", lw=1.5), **halo(T(f"{F}.osm.legend_halo"))),
        Line2D([], [], marker="o", ls="", mfc="orange", mec="k", label=T(f"{F}.legend_firms")),
    ],
    loc="upper left",
    fontsize=9,
    frameon=False,
)
ax.text(0.02, 0.50, T(f"{F}.notes"), transform=ax.transAxes, fontsize=9, va="top")
fig.suptitle(T(f"{F}.title", d12=lang.md(t12), d14=lang.md(t14), d15=lang.md(t15)), fontsize=12)
save(fig, lang.out(F))
