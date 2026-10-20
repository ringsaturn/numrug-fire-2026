# ahi: Himawari-9 AHI figures

Geostationary view of the fire: 10-minute hotspot detection on Himawari-9 AHI B07/B14,
visible imagery of the smoke, and the blog cover.

| Figure | Script | What it shows |
|---|---|---|
| `cover` | `cover.py` | true colour 2026-10-12 06:00Z, B03-sharpened to 0.5 km, 1920×1080, no axes |
| `ahi-hotspots-20261013-2200` | `timeseries.py` | hotspot pixels, ΣΔT and max BT7 every 10 min, 10-07 18:00Z to 10-13 14:00Z, with VIIRS per overpass |
| `ahi-b07-1008-1012-v3` | `b07_panels.py key` | B07 at eight key frames 10-08 to 10-12 (Natural Earth border) |
| `ahi-b07-1012-evening-v2` | `b07_panels.py evening` | B07 at eight frames, 10-12 afternoon to night (OSM border) |
| `ahi-front-progression` | `progression.py` | first detection time per 2 km pixel up to 10-12 04:40Z, 12 h centroid track |
| `ahi-latest-hotspots` | `latest.py r2` | hotspot pixels 10-12 08:50–11:40Z |
| `ahi-latest-hotspots-20261013` | `latest.py r3` | hotspot pixels 10-13 02:20–05:10Z |
| `ahi-latest-hotspots-20261013-2200` | `latest.py r5` | hotspot pixels 10-13 05:20–14:00Z |
| `ahi-vis-20261011-1300`, `-20261012-1400`, `-20261013-0900`, `-20261013-1400` | `vis.py` | B03 red band and true colour at 10-11 05Z, 10-12 06Z, 10-13 01Z, 10-13 06Z |

## Data and prepare steps

`numrug-figs prepare --group ahi` runs, in order:

1. `ahi-fetch-ir`: Himawari-9 AHI L1b HSD, bands B07 and B14, 2 km, segment 2 (`S0210`), every
   10 min from 2026-10-07 18:00Z to 10-13 14:00Z, from the NOAA open-data bucket
   `https://noaa-himawari9.s3.amazonaws.com/AHI-L1b-FLDK/` (anonymous). Keys in
   `granules/ahi_ir.txt` (1,654 files, 3.4 GB). Fourteen slots in that range are not in the
   bucket and are not listed: the daily 02:40Z and 14:40Z housekeeping slots and 10-07 20:30Z,
   10-08 23:00Z, 10-09 11:00Z. That leaves 827 frames.
2. `ahi-fetch-vis`: B01–B04, segments 1 and 2, at 10-11 05:00Z, 10-12 06:00Z, 10-13 01:00Z and
   10-13 06:00Z (`granules/ahi_vis.txt`, 32 files).
3. `ne-fetch`: Natural Earth 10m `ne_10m_admin_0_boundary_lines_land` v5.1.0 (public domain).
4. `viirs-fetch`: VIIRS 375 m active-fire L2 granules (VNP14IMG, VJ114IMG, VJ214IMG collection
   002, NASA LP DAAC), 54 granules, 100 MB, listed with their production versions in
   `granules/viirs_l2.txt`. Needs a NASA Earthdata login in `~/.netrc`
   (`machine urs.earthdata.nasa.gov login … password …`). The list was taken from CMR
   (`cmr.earthdata.nasa.gov/search/granules.json?short_name=VNP14IMG&version=002&bounding_box=118.8,46.4,120.2,47.6`,
   same for VJ114IMG and VJ214IMG), one production version per overpass (the newest), granule
   start before 2026-10-12 00:00Z.
5. `ahi-extract`: rows 530:640, cols 1920:2120 of the 2 km full disk for every frame →
   `data/ahi/ahi_b07_b14_crop.npz` (about 1.5 min on 8 cores).
6. `ahi-detect`: hotspot mask and statistics per frame → `ahi_hotmask.npz`,
   `ahi_hotspots_10min.csv`. Absolute test BT7 > 320 K (day) / 310 K (night), or contextual
   test BT7−BT14 > 4σ above the 21×21 background mean and > 10 K; BT14 cloud screen; box
   46.3–47.8°N, 118.4–120.4°E; day = solar zenith < 85°.
7. `viirs-box`: VIIRS fire pixels in the same box → `viirs_box.csv`.

Each published update covered a different frame range; `common.ROUNDS` gives them
(update 1 to 10-12 04:40Z, update 2 10-12 03:00–11:40Z, update 3 to 10-13 05:10Z, update 5 to
10-13 14:00Z). Detection is per frame, so one run serves all of them.

The `snapshot/` directory holds the one input that is not fetched (see `snapshot/README.md`).

## Differences from the published figures

- VIIRS points in the time series: the published figure used FIRMS NRT 7-day CSVs fetched
  around 10-12 05Z. FIRMS 7-day files no longer reach these dates, so the points come from the
  standard (non-NRT) L2 granules: 10,348 points, 10-08 04:06Z to 10-11 18:00Z. Per-overpass
  counts and FRP match the published markers (e.g. 10-08 17:00Z NOAA-20 480 points,
  10-11 05:40Z NOAA-20 903) except S-NPP 10-10 19:36Z, where the standard granules put 10 points
  into a separate 19:40 marker. The legend therefore says "VIIRS" (zh: no "FIRMS").
- Vis maps of 10-11 and 10-12 have an empty wedge at the top right: they were drawn with
  segment 2 only. `vis.py` reproduces this.
- `ahi-vis-20261013-1400`: AHI detected no hotspot pixel at 10-13 06:00Z (fire under cloud). The
  title leaves out "smoke plume" and the key says there is no hotspot, in every language; the
  published zh figure said 烟羽 and named a red outline that was not drawn.
- en and ja follow the in-figure style rules of the English rebuild (local time first, UTC+8,
  thousands separators, legends outside data). zh keeps the published wording and Beijing time.
- The time-series night-shading note sits in the footer in all languages (zh published it in the
  x-axis label).
