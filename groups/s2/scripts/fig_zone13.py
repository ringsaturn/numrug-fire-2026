"""Border sections on 10-13 (Sentinel-2B): an earlier true-colour panel, 10-13 true colour and SWIR, and dNBR
10-05 -> 10-13 with cloud and cloud shadow greyed (zones.py).

    fig_zone13.py south   s2-south-20261013-v2       ZA window, 10-10 true colour, arrow to the pre-existing strip
    fig_zone13.py west    s2-west-arxan-20261013-v2  ZB window, 10-05 true colour, arrow to the burn east of the line
"""

import sys

import matplotlib.patheffects as pe
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.ticker import MaxNLocator

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
PE = [pe.withStroke(linewidth=2.2, foreground="black")]
B8 = ("red", "green", "blue", "nir", "nir08", "swir16", "swir22", "scl")
m5, m10, m13 = (tk(utc(d))["md"] for d in ("2026-10-05", "2026-10-10", "2026-10-13"))


def panel(g, z, pre, name, figh, strip=None, arrow=None):
    """strip: (x0, y0, x1) arrow to xy from a label whose left edge is x1 just above the bottom frame;
    arrow: (x0, y0, x1, y1, text) arrow to (x0, y0) from a label at (x1, y1)."""
    K = name + "."
    e, _, _ = ext_of(g, "2026-10-05")
    D13 = load("2026-10-13", g, B8)
    dn = np.load(D("derived", f"{g}_dnbr_1005_1013.npy"))
    fig, axs = plt.subplots(2, 2, figsize=(7.2, figh), constrained_layout=True)
    fig.get_layout_engine().set(
        rect=(0.015, 0, 0.985, 1)
    )  # keep y tick labels and the colour-bar label off the image edge
    cm = ListedColormap(DNBR_CMAP)
    P = [
        pre,
        (truecolor(D13, 0.3), lang.T("zone13.true", md=m13)),
        (swir(D13), lang.T("zone13.swir", md=m13)),
        (None, lang.T("zone13.dnbr", a_md=m5, b_md=m13)),
    ]
    for k, (ax, (img, t)) in enumerate(zip(axs.flat, P)):
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
        else:
            ax.imshow(img, extent=e, aspect=aspect(e), interpolation="nearest")
        borders_osm(ax, 1.4)
        fmt(ax, z, 9, latnd=3)
        ax.set_title(t, fontsize=9.5)
        ax.set_xticks([z[0] + 0.03, (z[0] + z[1]) / 2, z[1] - 0.03])
        ax.yaxis.set_major_locator(MaxNLocator(4))
        if k % 2:
            ax.set_yticklabels([])
        if k < 2:
            ax.set_xticklabels([])
        if strip:
            x0, y0, x1 = strip
            arrow_label(ax, (x0, y0), lang.T("s2.strip"), x1 + lang.T(K + "strip_dx"), z[2] + 0.0025, lw=1)
        if arrow:
            x0, y0, x1, y1, txt = arrow
            a = ax.annotate("", (x0, y0), xytext=(x1, y1), arrowprops=dict(color="white", lw=1))
            a.arrow_patch.set_path_effects([pe.withStroke(linewidth=3.4, foreground="black")])
            ax.text(x1, y1, txt, va="bottom", color="white", fontsize=9, path_effects=PE)
    cb = fig.colorbar(im, ax=axs[:, 1], shrink=0.8, ticks=DNBR_TICKS)
    cb.ax.set_yticklabels(lang.T("s2.dnbr_ticks"), fontsize=8)
    cb.set_label("dNBR", fontsize=9)
    fig.suptitle(lang.T(K + "title", md=m13), fontsize=12)
    flush_labels(fig)
    out = lang.out(name)
    fig.savefig(out, dpi=200)
    print(out)


if sys.argv[1] == "south":
    D10 = load("2026-10-10", "ZA", ("red", "green", "blue"))
    panel(
        "ZA",
        (119.37, 119.55, 46.585, 46.655),
        (truecolor(D10), lang.T("s2-south-20261013-v2.pre", md=m10)),
        "s2-south-20261013-v2",
        4.9,
        strip=(119.468, 46.6035, 119.488),
    )
else:
    D5 = load("2026-10-05", "ZB", ("red", "green", "blue"))
    panel(
        "ZB",
        (119.66, 119.84, 47.08, 47.22),
        (truecolor(D5), lang.T("s2-west-arxan-20261013-v2.pre", md=m5)),
        "s2-west-arxan-20261013-v2",
        7.2,
        arrow=(119.735, 47.160, 119.765, 47.192, lang.T("s2-west-arxan-20261013-v2.burned")),
    )
