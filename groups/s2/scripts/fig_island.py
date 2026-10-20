"""s2-island-20261015: south edge of the unburned island on 10-15 (Sentinel-2C, 03:05Z), true colour and SWIR,
with the saturated SWIR pixels (island_hot.py) and the FIRMS 24 h daytime detections of the same midday."""

import csv
import json

from matplotlib.lines import Line2D

from common import D, SNAP, aspect, borders_osm, ext_of, lang, load, plt, swir, tk, truecolor, utc

lang.init(__file__)
K = "s2-island-20261015."
B8 = ("red", "green", "blue", "nir", "nir08", "swir16", "swir22", "scl")
e, _, _ = ext_of("ZI", "2026-10-15")
X = load("2026-10-15", "ZI", B8)
hot = json.load(open(D("derived", "zone_i_hot.json")))
# FIRMS 24 h rows of 10-15, daytime, north of 46.9°N (drops the unrelated 46.50°N Aqua point).
Fd = [
    r
    for r in csv.DictReader(open(SNAP / "firms_24h_20261015.csv"))
    if r["t"].startswith("2026-10-15") and r["dn"] == "D" and float(r["lat"]) > 46.9
]
MK = {
    "N": ("o", "#00e5ff", "S-NPP"),
    "N20": ("^", "#ff00ff", "NOAA-20"),
    "N21": ("D", "#ffff00", "NOAA-21"),
    "A": ("s", "#ffffff", "Aqua"),
}
z = (119.54, 119.65, 47.04, 47.12)
fig, axs = plt.subplots(1, 2, figsize=(7.2, 5.3), constrained_layout=True)
for k, (ax, img, t) in enumerate(zip(axs, [truecolor(X, 0.3), swir(X)], [lang.T(K + "true"), lang.T(K + "swir")])):
    ax.imshow(img, extent=e, aspect=aspect(e), interpolation="nearest")
    borders_osm(ax, 1.6)
    for s, (mk, c, nm) in MK.items():
        g = [r for r in Fd if r["sat"] == s]
        if g:
            when = lang.T(K + "time", **tk(utc(*g[0]["t"].split())))
            ax.scatter(
                [float(r["lon"]) for r in g],
                [float(r["lat"]) for r in g],
                s=36,
                marker=mk,
                facecolors="none",
                edgecolors=c,
                linewidths=1.2,
                label=lang.T(K + ("pass_area" if s == "A" else "pass"), sat=nm, time=when, n=len(g)),
                zorder=5,
            )
    for hp in hot["hot_px"]:
        ax.plot(hp["lon"], hp["lat"], "x", color="red", ms=7, mew=1.6, zorder=6)
    ax.set_xlim(z[0], z[1])
    ax.set_ylim(z[2], z[3])
    ax.set_title(t, fontsize=10)
    ax.set_xticks([119.56, 119.60, 119.64])
    ax.set_yticks([47.05, 47.07, 47.09, 47.11])
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: f"{v:.2f}°E"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: f"{v:.2f}°N"))
    ax.tick_params(labelsize=9)
    if k:
        ax.set_yticklabels([])
h, l = axs[0].get_legend_handles_labels()
h.append(Line2D([], [], marker="x", ls="", color="red", mew=1.6))
l.append(lang.T(K + "hot", n=hot["hot_mn"]))
fig.legend(
    h,
    l,
    loc="outside lower center",
    ncol=2,
    fontsize=9,
    frameon=True,
    facecolor="#9e9e9e",
    edgecolor="none",
    title=lang.T(K + "legend_title"),
    title_fontsize=9,
)
fig.suptitle(lang.T(K + "title", **tk(utc("2026-10-15", "03:05"))), fontsize=11)
out = lang.out("s2-island-20261015")
fig.savefig(out, dpi=200, bbox_inches=None)
plt.close(fig)
print(out)
