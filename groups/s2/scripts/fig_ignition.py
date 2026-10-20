"""ignition-20261008-v2: the ignition box on the morning of 10-08 before the fire. Landsat 9 SWIR false colour and
B10 surface temperature (02:45Z), Sentinel-2C SWIR false colour (03:15Z), with the day's first VIIRS detections
(04:00–05:59Z); the fourth cell holds the legend."""

import datetime as dt

import numpy as np
from matplotlib.ticker import MaxNLocator

from common import BOX, D, SAT, aspect, borders_both, ext_of, firms_dots, fmt, gamma, lang, load, plt, swir, tk, utc

lang.init(__file__)
K = "ignition-20261008-v2."
ls = {b: np.load(D("landsat", f"IGN_{b}.npy")).astype("f4") * 2.75e-5 - 0.2 for b in ["red", "nir08", "swir22"]}
lst = np.load(D("landsat", "IGN_lwir11.npy")) * 0.00341802 + 149 - 273.15
print("LST max %.1f C" % lst.max())
el = BOX["IGN"]
X = load("2026-10-08", "IGN")
e, _, _ = ext_of("IGN", "2026-10-08", 10)
t_ls = utc("2026-10-08", "02:45")
t_s2 = utc("2026-10-08", SAT["2026-10-08"][1])
fig, axs = plt.subplots(2, 2, figsize=(7.2, 6.9), constrained_layout=True)


def sw(r, n, s):
    return gamma(
        np.dstack(
            [np.clip((s - 0.02) / 0.38, 0, 1), np.clip((n - 0.02) / 0.36, 0, 1), np.clip((r - 0.01) / 0.21, 0, 1)]
        ),
        0.75,
    )


a0, a1, a2, a3 = axs.flat
a0.imshow(sw(ls["red"], ls["nir08"], ls["swir22"]), extent=el, aspect=aspect(el))
a0.set_title(lang.T(K + "landsat_swir", **tk(t_ls)), fontsize=10)
im = a1.imshow(lst, extent=el, aspect=aspect(el), cmap="inferno", vmin=5, vmax=20)
a1.set_title(lang.T(K + "landsat_lst", tmax=lang.num(lst.max()), **tk(t_ls)), fontsize=10)
cb = fig.colorbar(im, ax=a1, shrink=0.8)
cb.set_label(lang.T(K + "unit"), fontsize=9)
cb.ax.tick_params(labelsize=9)
a2.imshow(swir(X), extent=e, aspect=aspect(e))
a2.set_title(lang.T(K + "s2_swir", **tk(t_s2)), fontsize=10)
# 12:08 and 13:48 are the FIRMS acquisition times of the first and last pass; the L2 granules start 2 min earlier.
label = lang.T(
    K + "fires", **tk(utc("2026-10-08", "04:08"), "a_"), **tk(utc("2026-10-08", "05:48"), "b_"), md=tk(t_s2)["md"]
)
for k, ax in enumerate((a0, a1, a2)):
    borders_both(ax)
    fmt(ax, el, 9)
    ax.set_xticks([119.30, 119.40, 119.50])
    ax.yaxis.set_major_locator(MaxNLocator(4))
    firms_dots(ax, dt.datetime(2026, 10, 8, 4, 0), dt.datetime(2026, 10, 8, 5, 59), el, label=label, s=24)
    if k == 1:
        ax.set_yticklabels([])
h, l = a0.get_legend_handles_labels()
a3.axis("off")
a3.legend(
    h, l, loc="center", fontsize=9, frameon=False, title=lang.T(K + "legend_title", **tk(t_s2)), title_fontsize=10
)
out = lang.out("ignition-20261008-v2")
fig.savefig(out, dpi=200)
print(out)
