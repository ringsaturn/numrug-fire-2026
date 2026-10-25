"""route-port-ignition: shortest road paths on the OSM 2026-10-25 network from Sümber port and from the Khalkhgol sum
centre to the end of the track nearest the ignition point, over the DEM hillshade of the spread animation.
Also the straight lines from the ignition point to the sum centre and to the nearest border points, the banner
boundaries meeting the national border, the Nömrög reserve boundary and the rivers."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.lines as mlines
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from pyproj import Geod

from common import ARXAN, hillshade
from figkit import lang, osm

lang.init(__file__, figure="route-port-ignition")
C = "route-port-ignition."
W, E, S, N = 118.5, 120.05, 46.55, 47.72
ASP = 1 / np.cos(np.radians((S + N) / 2))
BG, FG, MUTED = "#101214", "#e8e6e3", "#9a9894"
ROUTE, BRANCH, RIVER, SPA, STRAIGHT = "#ffd84d", "#ff9a3c", "#5aa9e6", "#4fd17a", "#ffffff"
G = Geod(ellps="WGS84")
HALO = [pe.withStroke(linewidth=3, foreground=BG)]
O = osm.load()


def km(a, b):
    return G.inv(a[0], a[1], b[0], b[1])[2] / 1000


def cumulative(c):
    return np.r_[0, np.cumsum([km(a, b) for a, b in zip(c, c[1:])])]


def along(c, cum, p):
    """Distance along polyline c of the point on it nearest p (local equirectangular projection)."""
    xy = np.array(c) * [1 / ASP, 1]
    q = np.array(p) * [1 / ASP, 1]
    best = (1e9, 0)
    for i in range(len(xy) - 1):
        a, b = xy[i], xy[i + 1]
        t = np.clip(np.dot(q - a, b - a) / max(np.dot(b - a, b - a), 1e-18), 0, 1)
        d = np.hypot(*(a + t * (b - a) - q))
        if d < best[0]:
            best = (d, cum[i] + t * (cum[i + 1] - cum[i]))
    return best[1]


route = O["routes"]["port-to-track-end"]
town = O["routes"]["town-to-track-end"]
cum = cumulative(route)
on_route = {tuple(p) for p in route}
j = next(i for i, p in enumerate(town) if tuple(p) in on_route)  # where the sum-centre path joins
branch = town[: j + 1]
JUNC = tuple(town[j])
k_junc = cum[route.index(list(JUNC))]
k_branch = cumulative(branch)[-1]
k_town_road = cumulative(town)[-1]
k_end = cum[-1]
k_walk = km(osm.PLACES["track_end"], osm.IGNITION)
k_straight = km(osm.PLACES["sum"], osm.IGNITION)
k_bag = along(route, cum, osm.PLACES["bag"])
print(f"route {k_end:.1f} km, junction at {k_junc:.1f} km ({JUNC[1]:.4f}N {JUNC[0]:.4f}E), branch {k_branch:.1f} km,")
print(f"sum centre by road {k_town_road:.3f} + {k_walk:.3f} = {k_town_road + k_walk:.3f} km, straight {k_straight:.3f} km,")
print(f"Nömrög bag at {k_bag:.1f} km")

fig = plt.figure(figsize=(11, 14.0), dpi=140, facecolor=BG)
ax = fig.add_axes([0.03, 0.129, 0.94, 0.821])
ax.set_facecolor(BG)
ax.imshow(hillshade(W, E, S, N), extent=(W, E, S, N), aspect=ASP, interpolation="bilinear")

# context: roads, reserve, rivers, border
osm.roads(ax, ("unclassified", "track", "tertiary", "primary", "trunk", "residential"), color="#b9b4ab", lw=0.5,
          alpha=0.55, zorder=2)
osm.spa(ax, color=SPA, lw=1.1, alpha=0.9, zorder=3)
for w in O["rivers"]:
    named = w["name"] in ("Халх гол", "Дэлгэр гол")
    border_river = w["id"] == 161028141  # unnamed river along the border south of the ports
    if named or border_river:
        x, y = zip(*w["c"])
        ax.plot(x, y, color=RIVER, lw=1.3, zorder=3, solid_capstyle="round")
for w in O["border"]:
    x, y = zip(*w["c"])
    ax.plot(x, y, color="#f2f2f2", lw=1.2, ls=(0, (5, 3)), alpha=0.9, zorder=4)

# banner boundaries meeting the national border: a tick across the border line
for key, (x0, y0) in osm.JUNCTIONS.items():
    pts = np.array([p for w in O["border"] for p in w["c"]])
    d = np.hypot((pts[:, 0] - x0) / ASP, pts[:, 1] - y0)
    nb = pts[np.argsort(d)[1:6]]
    t = (nb - [x0, y0]) * [1 / ASP, 1]
    t = t[np.argmax(np.hypot(*t.T))]
    n = np.array([-t[1], t[0]]) / np.hypot(*t) * 0.022
    ax.plot([x0 - n[0] * ASP, x0 + n[0] * ASP], [y0 - n[1], y0 + n[1]], color="#ff5c8a", lw=2.6, zorder=6,
            solid_capstyle="butt")
    off, ha = {"ujimqin_horqin": ((-10, -14), "right"), "horqin_arxan": ((-12, -10), "right"),
               "arxan_barag": ((10, 14), "left")}[key]
    ax.annotate(lang.T(C + key), (x0, y0), xytext=off, textcoords="offset points", ha=ha, va="center",
                color="#ff9fbc", fontsize=9.5, path_effects=HALO, zorder=8)

# straight lines from the ignition point
IG = osm.IGNITION
for p, ls, lw, key, val, off in (
    (osm.PLACES["sum"], (0, (6, 4)), 1.4, "straight_label", k_straight, (0, 0)),
    (osm.NEAREST["arxan_segment"], (0, (2, 2)), 1.3, "hg_label", km(IG, osm.NEAREST["arxan_segment"]), (0, 0)),
    (osm.NEAREST["border"], (0, (2, 2)), 1.0, "border_label", km(IG, osm.NEAREST["border"]), (0, 0)),
):
    ax.plot([IG[0], p[0]], [IG[1], p[1]], color=STRAIGHT, lw=lw, ls=ls, zorder=5)
    ax.plot(*p, "o", ms=3.5, color=STRAIGHT, zorder=6)
ax.plot([IG[0], osm.PLACES["track_end"][0]], [IG[1], osm.PLACES["track_end"][1]], color="cyan", lw=1.6,
        ls=(0, (3, 2)), zorder=6)


def mid_label(a, b, text, f=0.5, off=(0, 0), rot=True, **kw):
    x, y = a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1])
    ang = np.degrees(np.arctan2(b[1] - a[1], (b[0] - a[0]) / ASP)) if rot else 0
    if ang > 90:
        ang -= 180
    if ang < -90:
        ang += 180
    ax.annotate(text, (x, y), xytext=off, textcoords="offset points", ha="center", va="center", rotation=ang,
                rotation_mode="anchor", color=kw.pop("color", FG), fontsize=kw.pop("fontsize", 10),
                path_effects=HALO, zorder=9, **kw)


mid_label(IG, osm.PLACES["sum"], lang.T(C + "straight_label", km=f"{k_straight:.1f}"), 0.5, (0, 9))
mid_label(IG, osm.NEAREST["arxan_segment"], lang.T(C + "hg_label", km=f"{km(IG, osm.NEAREST['arxan_segment']):.1f}"),
          0.55, (0, 9))
mid_label(IG, osm.NEAREST["border"], lang.T(C + "border_label", km=f"{km(IG, osm.NEAREST['border']):.1f}"), 0.5,
          (0, 9), fontsize=9)
mid_label(IG, osm.PLACES["track_end"], f"{k_walk:.1f} km", 0.5, (14, 0), rot=False, color="cyan", fontsize=9.5)

# road paths
x, y = zip(*branch)
ax.plot(x, y, color=BRANCH, lw=2.4, zorder=7, solid_capstyle="round", solid_joinstyle="round")
x, y = zip(*route)
ax.plot(x, y, color="black", lw=5.2, zorder=7, alpha=0.5, solid_joinstyle="round")
ax.plot(x, y, color=ROUTE, lw=3.4, zorder=7, solid_capstyle="round", solid_joinstyle="round")
# distance marks along the port route: (km, label offset in points)
MARKS = [
    (24.5, (-6, -8)),
    (61.8, (0, 10)),
    (k_junc, (0, 10)),
    (k_bag, (-10, 6)),
    (k_end, (-10, 2)),
]
for k, off in MARKS:
    i = int(np.argmin(np.abs(cum - k)))
    px, py = route[i]
    ax.plot(px, py, "o", ms=6, mfc=BG, mec=ROUTE, mew=1.8, zorder=8)
    text = lang.T(C + "km", km=f"{k:.1f}")
    if abs(k - k_junc) < 0.05:
        text = lang.T(C + "junction", km=f"{k:.1f}")
    ax.annotate(text, (px, py), xytext=off, textcoords="offset points", ha="right" if off[0] < 0 else "center",
                va="bottom" if off[1] >= 0 else "top", color=ROUTE, fontsize=10, weight="bold", path_effects=HALO, zorder=9)
ax.annotate(lang.T(C + "km", km="0"), route[0], xytext=(-4, -8), textcoords="offset points", ha="right", va="top",
            color=ROUTE, fontsize=10, weight="bold", path_effects=HALO, zorder=9)

# places
PL = [
    ("sumber", "^", (-8, 6), "right", "bottom"),
    ("arxan_port", "^", (8, -6), "left", "top"),
    ("zastav", "o", (7, 7), "left", "bottom"),
    ("bag", "o", (9, 5), "left", "bottom"),
    ("ford", "D", (9, -3), "left", "top"),
    ("sum", "s", (9, 6), "left", "bottom"),
    ("track_end", "s", (-9, -3), "right", "top"),
]
for key, mk, off, ha, va in PL:
    lo, la = osm.PLACES[key]
    ax.plot(lo, la, mk, ms=6 if mk != "D" else 4.5, mfc="white", mec="black", mew=0.9, zorder=10)
    ax.annotate(osm.T(key), (lo, la), xytext=off, textcoords="offset points", ha=ha, va=va, color="white",
                fontsize=9.5, family=osm.font(), path_effects=HALO, zorder=11)
ax.plot(*ARXAN, "s", ms=6, mfc="white", mec="black", zorder=10)
ax.annotate(lang.T(C + "arxan"), ARXAN, xytext=(-8, 6), textcoords="offset points", ha="right", color="white",
            fontsize=10, path_effects=HALO, zorder=11)
ax.plot(*IG, marker="*", ms=17, mfc="none", mec="cyan", mew=1.8, zorder=12)
ax.annotate(osm.T("ignition"), IG, xytext=(10, -6), textcoords="offset points", ha="left", va="top", color="cyan",
            fontsize=10.5, weight="bold", path_effects=HALO, zorder=12)

# rivers and regions
for key, xy, rot in (("khalkh", (118.83, 47.585), 24), ("delger", (119.262, 47.2), 80)):
    ax.text(*xy, osm.T(key), color=RIVER, fontsize=9.5, rotation=rot, ha="center", va="center", family=osm.font(),
            path_effects=HALO, zorder=9)
ax.text(118.56, 47.69, lang.T(C + "mongolia"), color=FG, fontsize=15, alpha=0.85, va="top")
ax.text(120.02, 46.58, lang.T(C + "china"), color=FG, fontsize=15, alpha=0.85, ha="right", va="bottom")
k20 = 20 / (111.32 * np.cos(np.radians(46.6)))
ax.plot([118.56, 118.56 + k20], [46.58, 46.58], color=FG, lw=3, zorder=9)
ax.text(118.56 + k20 / 2, 46.59, "20 km", color=FG, ha="center", va="bottom", fontsize=10, zorder=9)
ax.set_xlim(W, E)
ax.set_ylim(S, N)
ax.set_xticks([])
ax.set_yticks([])
for s in ax.spines.values():
    s.set_visible(False)

fig.text(0.03, 0.988, lang.T(C + "title"), color=FG, fontsize=float(lang.T(C + "title_size")), weight="bold", va="top")
fig.text(0.03, 0.967, lang.T(C + "subtitle", road=f"{k_town_road:.1f}", walk=f"{k_walk:.1f}",
                             total=f"{k_town_road + k_walk:.1f}", straight=f"{k_straight:.1f}"),
         color=MUTED, fontsize=11, va="top")

H = [
    (mlines.Line2D([], [], color=ROUTE, lw=3.4), lang.T(C + "route", km=f"{k_end:.1f}")),
    (mlines.Line2D([], [], color=BRANCH, lw=2.4), lang.T(C + "branch", km=f"{k_branch:.1f}", total=f"{k_town_road:.1f}")),
    (mlines.Line2D([], [], color=STRAIGHT, lw=1.4, ls=(0, (6, 4))), lang.T(C + "straight")),
    (mlines.Line2D([], [], color="cyan", lw=1.6, ls=(0, (3, 2))), lang.T(C + "walk")),
    (mlines.Line2D([], [], color=STRAIGHT, lw=1.3, ls=(0, (2, 2))), lang.T(C + "nearest")),
    (mlines.Line2D([], [], color="#f2f2f2", lw=1.2, ls=(0, (5, 3))), lang.T(C + "border")),
    (mlines.Line2D([], [], color="#ff5c8a", lw=2.6), lang.T(C + "tick")),
    (mlines.Line2D([], [], color=SPA, lw=1.1), osm.T("spa")),
    (mlines.Line2D([], [], color=RIVER, lw=1.3), lang.T(C + "rivers")),
    (mlines.Line2D([], [], color="#b9b4ab", lw=0.8), lang.T(C + "roads")),
]
leg = fig.legend(*zip(*H), loc="upper left", bbox_to_anchor=(0.03, 0.124), ncol=2, frameon=False, fontsize=10,
                 labelcolor=FG, handlelength=2.6, columnspacing=1.6)
fig.text(0.03, 0.012, lang.T(C + "footer"), color=MUTED, fontsize=8.5, va="bottom", linespacing=1.4)
fig.savefig(lang.out("route-port-ignition"), facecolor=BG)
