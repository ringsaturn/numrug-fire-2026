"""s2-overview: Sentinel-2 L2A on 10-05, 10-08 and 10-10 over the whole fire area (40 m overview grid), true colour
over SWIR false colour, with the OSM and Natural Earth borders and the VIIRS detections of 10-08 and 10-10.
Drawn at 2100x1650 px and resized to 2000 px wide, as published."""

import datetime as dt

from PIL import Image

from common import (
    OVERVIEW,
    SAT,
    aspect,
    borders_both,
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

lang.init(__file__)
K = "s2-overview."
dates = ["2026-10-05", "2026-10-08", "2026-10-10"]
ext = OVERVIEW
fig, axs = plt.subplots(2, 3, figsize=(21, 16.5))
for j, d in enumerate(dates):
    X = load(d, "A")
    sat, t = SAT[d]
    for i, (img, nm) in enumerate([(truecolor(X, 0.22), lang.T(K + "true")), (swir(X), lang.T(K + "swir"))]):
        ax = axs[i, j]
        ax.imshow(img, extent=ext, aspect=aspect(ext), interpolation="lanczos")
        borders_both(ax)
        town(ax)
        fmt(ax, ext)
        ax.set_title(lang.T(K + "panel", sat=sat, time=tloc(d, t), band=nm), fontsize=11)
    if d == "2026-10-10":
        firms_dots(
            axs[1, j],
            dt.datetime(2026, 10, 10, 3, 20),
            dt.datetime(2026, 10, 10, 3, 40),
            ext,
            label=lang.T("s2.fires_n21", **tk(utc(d, "03:30"))),
        )
        axs[1, j].legend(loc="lower left", fontsize=9)
    if d == "2026-10-08":
        # First detections: four passes in 04:00–05:59Z (FIRMS acquisition times 04:08 and 05:48 for the first and last).
        firms_dots(
            axs[1, j],
            dt.datetime(2026, 10, 8, 4, 0),
            dt.datetime(2026, 10, 8, 5, 59),
            ext,
            label=lang.T(K + "fires_1008", **tk(utc(d, "04:08"), "a_"), **tk(utc(d, "05:48"), "b_")),
        )
        axs[1, j].legend(loc="lower left", fontsize=9)
md = [tk(utc(d))["md"] for d in dates]
fig.suptitle(lang.T(K + "title", d1=md[0], d2=md[1], d3=md[2]), fontsize=15)
fig.text(0.5, 0.006, lang.T(K + "footer", d1=md[0], d2=md[1], d3=md[2]), ha="center", fontsize=10)
plt.tight_layout(rect=(0, 0.03, 1, 0.965), h_pad=2.5)
out = lang.out("s2-overview")
fig.savefig(out, dpi=100)
im = Image.open(out)
im.resize((2000, round(im.size[1] * 2000 / im.size[0])), Image.LANCZOS).save(out)
print(out)
