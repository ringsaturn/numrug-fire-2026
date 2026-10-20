"""border-south-zoom-20261013-v2: southern border section (ZA window, 10 m), 10-05 true colour and SWIR, 10-08 SWIR,
10-10 true colour and SWIR, and dNBR 10-05 -> 10-10 (zones.py), with the pre-existing strip marked."""

import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap

from common import (
    D,
    DNBR_BOUNDS,
    DNBR_CMAP,
    DNBR_TICKS,
    arrow_label,
    aspect,
    borders_osm,
    ext_of,
    flush_labels,
    fmt,
    lang,
    load,
    plt,
    swir,
    tk,
    truecolor,
    utc,
)

lang.init(__file__)
K = "border-south-zoom-20261013-v2."
z = (119.37, 119.55, 46.585, 46.655)
e, _, _ = ext_of("ZA", "2026-10-05")
D5 = load("2026-10-05", "ZA")
D8 = load("2026-10-08", "ZA")
D10 = load("2026-10-10", "ZA")
dn = np.load(D("derived", "ZA_dnbr_1005_1010.npy"))
m5, m8, m10 = (tk(utc(d))["md"] for d in ("2026-10-05", "2026-10-08", "2026-10-10"))
fig, axs = plt.subplots(3, 2, figsize=(7.2, 7.4), sharex=True, sharey=True, layout="constrained")
fig.get_layout_engine().set(rect=(0.015, 0, 0.985, 1))  # keep y tick labels and colour-bar labels off the image edge
cm = ListedColormap(DNBR_CMAP)
P = [
    (truecolor(D5), lang.T(K + "pre_true", md=m5)),
    (swir(D5), lang.T(K + "pre_swir", md=m5)),
    (swir(D8), lang.T(K + "ign_swir", md=m8)),
    (truecolor(D10), lang.T(K + "fire_true", md=m10)),
    (swir(D10), lang.T(K + "fire_swir", md=m10)),
    (None, lang.T(K + "dnbr", a_md=m5, b_md=m10)),
]
for ax, (img, t) in zip(axs.ravel(), P):
    if img is None:
        ax.set_facecolor("#bbbbbb")
        im = ax.imshow(
            np.ma.masked_invalid(dn),
            extent=e,
            aspect=aspect(e),
            cmap=cm,
            norm=BoundaryNorm(DNBR_BOUNDS, cm.N),
            interpolation="nearest",
        )
        cb = fig.colorbar(im, ax=ax, shrink=0.9, pad=0.02, ticks=DNBR_TICKS)
        cb.ax.set_yticklabels(lang.T("s2.dnbr_ticks"))
        cb.ax.tick_params(labelsize=8)
    else:
        ax.imshow(img, extent=e, aspect=aspect(e), interpolation="nearest")
    borders_osm(ax, 1.8)
    fmt(ax, z, 9)
    ax.set_title(t, fontsize=10)
    ax.set_xticks([119.40, 119.45, 119.50])
    ax.set_yticks([46.60, 46.62, 46.64])
    arrow_label(ax, (119.468, 46.6035), lang.T("s2.strip"), lang.T(K + "strip_x"), 46.5875)
fig.suptitle(lang.T(K + "title"), fontsize=12)
flush_labels(fig)
out = lang.out("border-south-zoom-20261013-v2")
fig.savefig(out, dpi=200)
print(out)
