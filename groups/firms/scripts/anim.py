"""Fire-spread animation (arxan-fire-spread): VIIRS 375 m detections accumulating hour by hour from 10-08 03Z to
10-16 06Z over a Copernicus DEM hillshade, then a cross-fade to the GIBS 10-16 NOAA-21 false colour (dark red =
burn scar). Right panel: clock, running count, latest overpass and the FRP per overpass. The three MODIS
detections of the 10-15 fire south of the main scar are drawn as circles.

  anim.py --video full     render the 286 frames to out/frames/arxan-fire-spread.<lang>/ and encode the 1440 px mp4
  anim.py --video 960      encode the 960 px mp4 (renders the frames first if they are missing)
  anim.py --poster         frame 285 as a still; legend classes with no point in it are greyed
  anim.py --only N         render frame N into the frames directory
"""

import argparse
import datetime as dt
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from common import ANIM_BOX, GIBS, SAT_NAME, border, hillshade, in_box, modis_nrt, viirs
from figkit import lang, paths

lang.init(__file__, figure="arxan-fire-spread")
ap = argparse.ArgumentParser()
ap.add_argument("--video", choices=["full", "960"])
ap.add_argument("--poster", action="store_true")
ap.add_argument("--only", type=int)
a = ap.parse_args()
C = "arxan-fire-spread."
FPS = 12
FRAMES = paths.OUT / "frames" / f"arxan-fire-spread.{lang.LANG}"
POSTER_FRAME = 285

W, E, S, N = 118.8, 120.05, 46.40, 47.50
ASP = 1 / np.cos(np.radians((S + N) / 2))
BG, FG, MUTED = "#101214", "#e8e6e3", "#9a9894"
T0 = dt.datetime(2026, 10, 8, 3)
T1 = dt.datetime(2026, 10, 16, 6)
HOURS = int((T1 - T0).total_seconds() // 3600)
HOLD, FADE, HOLD2 = 2 * FPS, int(1.5 * FPS), 4 * FPS
TOTAL = HOURS + 1 + HOLD + FADE + HOLD2
BJ = dt.timedelta(hours=8)

# detections inside the case-anim fire box, ordered as the granules were read
v = in_box(viirs(), ANIM_BOX, strict=True)
v = v.sort_values(["t", "src"], kind="stable")
th = ((v.t - T0).dt.total_seconds() / 3600).to_numpy()
lon, lat = v.longitude.to_numpy(), v.latitude.to_numpy()
passes = {}
for h, s, d, f in zip(th, v.src, v.daynight, v.frp):
    passes.setdefault((h, s, d), []).append(f)
P = sorted((h, s, d, len(f), sum(f)) for (h, s, d), f in passes.items())
m = in_box(modis_nrt(), ANIM_BOX, strict=True)
m = m[(m.t >= "2026-10-15 06:52") & (m.latitude < 46.55)]
mh = [((t - T0).total_seconds() / 3600, y, x) for t, y, x in zip(m.t, m.latitude, m.longitude)]

# hillshade
base = hillshade(W, E, S, N)
# GIBS 10-16 NOAA-21 false colour, cropped from its 118.8-120.2°E / 46.4-47.6°N frame to the map box
fc = (
    np.asarray(Image.open(GIBS / "anim_2026-10-16_VIIRS_NOAA21_CorrectedReflectance_BandsM11-I2-I1.png").convert("RGB"))
    / 255
)
fh, fw = fc.shape[:2]
fc = fc[
    int((47.6 - N) / 1.2 * fh) : int((47.6 - S) / 1.2 * fh), int((W - 118.8) / 1.4 * fw) : int((E - 118.8) / 1.4 * fw)
]
fc = np.asarray(Image.fromarray((fc * 255).astype(np.uint8)).resize(base.shape[1::-1], Image.LANCZOS)) / 255

BORDER = border("overpass")
ARXAN = (119.9367, 47.1706)  # Arxan city centre (OSM Nominatim)
ign = th < 1.5  # first pass, 10-08 04:06Z


def bj(h):
    return T0 + dt.timedelta(hours=h) + BJ


def frame(i, poster=False):
    h = min(i, HOURS)
    fade = np.clip((i - HOURS - HOLD) / FADE, 0, 1)
    fig = plt.figure(figsize=(14.4, 10.8), dpi=100, facecolor=BG)
    ax = fig.add_axes([0.012, 0.02, 0.56, 0.96])
    ax.set_facecolor(BG)
    ax.imshow(base * (1 - fade) + fc * fade, extent=(W, E, S, N), aspect=ASP, interpolation="bilinear")
    for p in BORDER:
        ax.plot(p[:, 0], p[:, 1], color="#f2f2f2", lw=1.1, ls=(0, (5, 3)), alpha=0.85)
    ax.text(118.98, 47.43, lang.T(C + "mongolia"), color=FG, fontsize=15, alpha=0.8)
    ax.text(119.80, 46.47, lang.T(C + "china"), color=FG, fontsize=15, alpha=0.8)
    ax.plot(*ARXAN, "s", ms=6, mfc="white", mec="black")
    ax.text(ARXAN[0] - 0.01, ARXAN[1] + 0.025, lang.T(C + "arxan"), color="white", fontsize=12, ha="right")
    seen = th <= h + 1e-9
    age = h - th
    o = seen & (age >= 12)
    mid = seen & (age >= 3) & (age < 12)
    n = seen & (age < 3)
    ax.scatter(lon[o], lat[o], s=5, marker="s", c="#7a1712", alpha=0.75 * (1 - 0.8 * fade), lw=0)
    ax.scatter(lon[mid], lat[mid], s=7, marker="s", c="#ff7a1a", alpha=0.85, lw=0)
    ax.scatter(lon[n], lat[n], s=70, c="#ffb347", alpha=0.18, lw=0)
    ax.scatter(lon[n], lat[n], s=12, marker="s", c="#fff2a8", lw=0)
    if h >= 0.9:
        x0, y0 = lon[ign].mean(), lat[ign].mean()
        ax.scatter([x0], [y0], s=110, facecolors="none", edgecolors="white", lw=1.4)
        ax.annotate(
            lang.T(C + "first", time=lang.mdhm(dt.datetime(2026, 10, 8, 12, 6))),
            (x0, y0),
            xytext=(x0 - 0.42, y0 + 0.16),
            color=FG,
            fontsize=11,
            arrowprops=dict(arrowstyle="-", color=FG, lw=0.8),
            bbox=dict(fc=BG, alpha=0.6, lw=0, pad=2),
        )
    for mt, my, mx in mh:
        if h >= mt:
            ax.scatter([mx], [my], s=150, facecolors="none", edgecolors="#ffd84d", lw=1.6)
    if mh and h >= mh[0][0]:
        ax.annotate(
            lang.T(C + "south"),
            (119.555, 46.475),
            xytext=(119.08, 46.50),
            color="#ffd84d",
            fontsize=11,
            arrowprops=dict(arrowstyle="-", color="#ffd84d", lw=0.8),
        )
    km = 20 / (111.32 * np.cos(np.radians(46.45)))  # 20 km scale bar
    ax.plot([119.70, 119.70 + km], [46.425, 46.425], color=FG, lw=3)
    ax.text(119.70 + km / 2, 46.435, "20 km", color=FG, ha="center", fontsize=10)
    if fade > 0:
        ax.text(
            W + 0.02,
            S + 0.02,
            lang.T(C + "base"),
            color="white",
            fontsize=12,
            alpha=fade,
            va="bottom",
            bbox=dict(fc="#000000", alpha=0.45 * fade, lw=0),
        )
    ax.set_xlim(W, E)
    ax.set_ylim(S, N)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)

    # right panel
    X = 0.605
    fig.text(X, 0.945, lang.T(C + "title"), color=FG, fontsize=lang.T(C + "title_size"), weight="bold")
    fig.text(X, 0.928, lang.T(C + "subtitle"), color=MUTED, fontsize=lang.T(C + "subtitle_size"), va="top")
    now = bj(h)
    fig.text(X, 0.80, lang.T(C + "clock", t=now), color=FG, fontsize=40, weight="bold")
    utc = lang.mdhm(now - BJ)
    status = (
        lang.T(C + "status", utc=utc, day=int((h - 0.85) // 24) + 1)
        if h >= 0.85
        else lang.T(C + "status_before", utc=utc)
    )
    fig.text(X, 0.765, status, color=MUTED, fontsize=13)
    last = [p for p in P if p[0] <= h + 1e-9]
    fig.text(X, 0.700, lang.T(C + "so_far", n=lang.num(int(seen.sum()))), color=FG, fontsize=18)
    if last:
        lh, ls, ld, ln, lf = last[-1]
        fig.text(
            X,
            0.665,
            lang.T(
                C + "latest", time=lang.mdhm(bj(lh)), sat=SAT_NAME[ls], night=lang.T(C + "night") if ld == "N" else ""
            ),
            color=MUTED,
            fontsize=13,
        )
        if lf >= 1000:
            txt = lang.T(C + "last_gw", n=lang.num(ln), frp=lang.num(lf / 1000, 1))
        else:
            txt = lang.T(C + ("last_mw_one" if ln == 1 else "last_mw"), n=lang.num(ln), frp=lang.num(lf))
        fig.text(X, 0.638, txt, color=MUTED, fontsize=13)
    # legend; the poster greys the classes it does not show, the video frames keep the full legend
    ly = 0.575
    for c, cnt, key in [("#fff2a8", n.sum(), "recent"), ("#ff7a1a", mid.sum(), "mid"), ("#7a1712", o.sum(), "old")]:
        empty = poster and cnt == 0
        fig.add_artist(
            plt.Line2D(
                [X + 0.006],
                [ly + 0.006],
                marker="s",
                ms=7,
                color=c,
                alpha=0.3 if empty else 1,
                transform=fig.transFigure,
                lw=0,
            )
        )
        fig.text(
            X + 0.02,
            ly,
            lang.T(C + key) + (lang.T(C + "none_here") if empty else ""),
            color=MUTED if empty else FG,
            alpha=0.6 if empty else 1,
            fontsize=12,
        )
        ly -= 0.032
    fig.add_artist(
        plt.Line2D(
            [X + 0.006],
            [ly + 0.006],
            marker="o",
            ms=10,
            mfc="none",
            mec="#ffd84d",
            mew=1.6,
            transform=fig.transFigure,
            lw=0,
        )
    )
    fig.text(X + 0.02, ly, lang.T(C + "modis"), color=FG, fontsize=12)
    ly -= 0.032
    fig.add_artist(
        plt.Line2D([X, X + 0.014], [ly + 0.006] * 2, ls=(0, (5, 3)), color="#f2f2f2", lw=1.2, transform=fig.transFigure)
    )
    fig.text(X + 0.02, ly, lang.T(C + "border"), color=FG, fontsize=12)

    # FRP timeline
    tx = fig.add_axes([X + 0.035, 0.155, 0.355, 0.215])
    tx.set_facecolor(BG)
    for d in range(0, HOURS + 24, 24):  # night shading, 18:00-06:00 UTC+8
        tx.axvspan(d + 7, d + 19, color="#1d2228", lw=0)
    ph = np.array([p[0] for p in P])
    pf = np.array([p[4] for p in P]) / 1000
    vis = ph <= h + 1e-9
    tx.vlines(ph[~vis], 0, pf[~vis], color="#3a3f45", lw=2.2)
    tx.vlines(ph[vis], 0, pf[vis], color="#ff7a1a", lw=2.2)
    tx.axvline(h, color="#fff2a8", lw=1.2)
    tx.set_xlim(0, HOURS)
    tx.set_ylim(0, 33)
    days = [dt.datetime(2026, 10, d) for d in range(9, 17)]
    tx.set_xticks([(d - BJ - T0).total_seconds() / 3600 for d in days])
    tx.set_xticklabels([lang.md(d) for d in days], color=MUTED, fontsize=10)
    tx.tick_params(colors=MUTED, labelsize=10, length=3)
    for s in ["top", "right"]:
        tx.spines[s].set_visible(False)
    for s in ["left", "bottom"]:
        tx.spines[s].set_color("#555a60")
    tx.set_ylabel(lang.T(C + "frp_axis"), color=MUTED, fontsize=11)
    tx.set_xlabel(lang.T("common.local_time_axis"), color=MUTED, fontsize=9.5, labelpad=2)
    fig.text(X + 0.035, 0.385, lang.T(C + "night_note"), color=MUTED, fontsize=10)
    fig.text(
        X,
        0.030,
        lang.T(C + "footer"),
        color="#7d7b77",
        fontsize=lang.T(C + "footer_size"),
        linespacing=lang.T(C + "footer_linespacing"),
    )
    return fig


def render(frames):
    FRAMES.mkdir(parents=True, exist_ok=True)
    for i in frames:
        f = frame(i)
        f.savefig(FRAMES / f"f{i:04d}.png", facecolor=BG)
        plt.close(f)


def encode(name, vf, crf, preset):
    out = lang.out(name, "mp4")
    cmd = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-framerate",
        str(FPS),
        "-i",
        str(FRAMES / "f%04d.png"),
        *vf,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        str(crf),
        "-preset",
        preset,
        "-movflags",
        "+faststart",
        out,
    ]
    subprocess.run(cmd, check=True)
    print(out)


if a.poster:
    f = frame(POSTER_FRAME, poster=True)
    f.savefig(lang.out("arxan-fire-spread-poster"), facecolor=BG)
    print(lang.out("arxan-fire-spread-poster"))
elif a.only is not None:
    render([a.only])
elif a.video == "full":
    render(range(TOTAL))
    encode("arxan-fire-spread", [], 20, "slow")
elif a.video == "960":
    if len(list(FRAMES.glob("f*.png"))) != TOTAL:
        render(range(TOTAL))
    encode("arxan-fire-spread-960", ["-vf", "scale=960:-2"], 23, "medium")
else:
    ap.error("one of --video, --poster, --only")
