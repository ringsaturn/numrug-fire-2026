"""Full-resolution Sentinel-2 crops, true colour beside SWIR false colour, with borders and fire detections.

fig_crops.py fronts    s2-fronts-20261010: SE fire front and NW fire head on 10-10 (10 m), NOAA-21 VIIRS 03:30Z
fig_crops.py border-a  border-a: zone A near the Arxan border crossing, 10-05 (20 m) and 10-10 (10 m),
                       VIIRS/MODIS detections of 10-10 11:00Z – 10-11 04:59Z
"""

import datetime as dt
import sys

import matplotlib.patheffects as pe

from common import (
    ARXAN,
    SAT,
    aspect,
    borders_both,
    ext_of,
    firms_dots,
    fmt,
    lang,
    load,
    plt,
    tk,
    tloc,
    town,
    truecolor,
    swir,
    utc,
)

from figkit import osm

lang.init(__file__)


def crop_panels(rows, fig_key):
    """rows: (window, date, resolution in m, panel label, fire window (t0, t1, legend label) or None)."""
    fig, axs = plt.subplots(len(rows), 2, figsize=(16, 7.2 * len(rows)), squeeze=False)
    for i, (g, d, res, lab, fw) in enumerate(rows):
        X = load(d, g)
        e, _, _ = ext_of(g, d, res)
        sat, t = SAT[d]
        for j, (img, nm) in enumerate([(truecolor(X, 0.20), lang.T("s2.true")), (swir(X), lang.T("s2.swir"))]):
            ax = axs[i, j]
            ax.imshow(img, extent=e, aspect=aspect(e), interpolation="nearest")
            borders_both(ax, lw=1.6)
            fmt(ax, e)
            if e[0] < ARXAN[0] < e[1] and e[2] < ARXAN[1] < e[3]:
                town(ax)
            if fw and j == 1 and firms_dots(ax, fw[0], fw[1], e, label=fw[2], s=30, c="yellow"):
                ax.legend(loc="lower left", fontsize=9)
            ax.set_title(
                lang.T(
                    fig_key + ".panel",
                    label=lab,
                    sat=sat,
                    time=tloc(d, t),
                    band=nm,
                    sep=lang.T("s2.panel_sep"),
                    res=int(res),
                ),
                fontsize=11,
            )
    return fig, axs


def finish(fig, title, foot, name):
    fig.suptitle(title, fontsize=14)
    fig.text(0.5, 0.008, foot, ha="center", fontsize=9)
    bot = max(0.03, 0.006 + 0.012 * (foot.count("\n") + 1))  # room for the footer lines
    plt.tight_layout(rect=(0, bot, 1, 0.965), h_pad=2)
    out = lang.out(name)
    fig.savefig(out, dpi=110)
    plt.close(fig)
    print(out)


which = sys.argv[1]
if which == "fronts":
    K = "s2-fronts-20261010"
    t = utc("2026-10-10", "03:30")
    w = (dt.datetime(2026, 10, 10, 3, 20), dt.datetime(2026, 10, 10, 3, 40), lang.T("s2.fires_n21", **tk(t)))
    fig, _ = crop_panels(
        [("SE", "2026-10-10", 10, lang.T(K + ".se"), w), ("NW", "2026-10-10", 10, lang.T(K + ".nw"), w)], K
    )
    finish(fig, lang.T(K + ".title", **tk(utc("2026-10-10", "03:05"))), lang.T(K + ".footer"), K)
elif which == "border-a":
    K = "border-a"
    t0, t1 = dt.datetime(2026, 10, 10, 11), dt.datetime(2026, 10, 11, 4, 59)
    rng = {**tk(t0, "a_"), **tk(t1, "b_")}
    w = (t0, t1, lang.T(K + ".fires", **rng))
    fig, axs = crop_panels(
        [("SPA", "2026-10-05", 20, lang.T(K + ".pre"), w), ("SPA", "2026-10-10", 10, lang.T(K + ".during"), w)], K
    )
    halo = [pe.withStroke(linewidth=2.2, foreground="black")]
    for ax in axs.flat:
        e = (*ax.get_xlim(), *ax.get_ylim())
        kinds = ("unclassified", "track", "tertiary", "residential", "service")
        osm.roads(ax, kinds, box=e, color="white", lw=0.9, alpha=0.9, zorder=3, label=lang.T(K + ".roads"))
        for key, off, ha in (("sumber", (0, -9), "center"), ("arxan_port", (0, -9), "center")):
            lo, la = osm.PLACES[key]
            ax.plot(lo, la, "^", ms=8, mfc="white", mec="black", mew=1.2, zorder=6)
            ax.annotate(osm.T(key, wrap=True), (lo, la), xytext=off, textcoords="offset points", ha=ha, va="top",
                        color="white", fontsize=9.5, zorder=6, path_effects=halo, family=osm.font())
        ax.set_xlim(e[0], e[1])
        ax.set_ylim(e[2], e[3])
    for ax in axs[:, 0]:
        ax.legend(loc="lower left", fontsize=9)
    foot = lang.T(K + ".footer", **tk(utc("2026-10-10", "03:05"))) + "\n" + lang.T(K + ".osm")
    finish(fig, lang.T(K + ".title", **rng), foot, K)
