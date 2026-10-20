# firms: fire-spread animation and satellite fire-detection figures

| Figure | Script | What it shows |
|---|---|---|
| `arxan-fire-spread` (mp4, 1440×1080) | `anim.py --video full` | VIIRS 375 m detections accumulating hourly, 10-08 11:00 to 10-16 14:00 UTC+8, over a DEM hillshade; FRP per overpass; cross-fade to the 10-16 NOAA-21 false colour; the three MODIS detections of the 10-15 fire south of the main scar |
| `arxan-fire-spread-960` (mp4) | `anim.py --video 960` | the same frames scaled to 960 px |
| `arxan-fire-spread-poster` | `anim.py --poster` | frame 285 as a still; legend classes with no point in that frame are greyed |
| `firms-progression-20261013` | `fig_progression.py` | VIIRS detections by UTC+8 day, 10-08 to 10-13 morning |
| `firms-timeseries-20261013` | `fig_timeseries.py` | total FRP, pixel count and east/west edges per overpass, 10-08 to 10-13 morning |
| `firms-east-20261012` | `fig_east.py` | the three 10-12 daytime VIIRS passes along the border west of Arxan |
| `firms-20261013-1014-0911` | `fig_1013_1014.py` | six passes 10-13 day to 10-14 09:11 over the 10-12 NOAA-21 burn scar |
| `firms-20261014-1015` | `fig_1014_1015.py` | ten passes 10-14 day to 10-15 14:52 over the 10-14 NOAA-20 burn scar |

Frames go to `out/frames/arxan-fire-spread.<lang>/`. The mp4s need `ffmpeg` with libx264 on `PATH`
(full: `-crf 20 -preset slow`; 960: `-vf scale=960:-2 -crf 23`; both `-pix_fmt yuv420p -movflags +faststart`, 12 fps,
286 frames). Rendering the frames takes a few minutes per language.

## Data

| Input | Source | Prepare step | Notes |
|---|---|---|---|
| VIIRS 375 m active fire L2 | LP DAAC `VNP14IMG`, `VJ114IMG`, `VJ214IMG` v002 (10-07 12Z – 10-12 06Z); LANCE NRT `V??14IMG_NRT` (10-12 – 10-18 06Z) | `firms-fetch-viirs-l2` | 129 granules over 118.8–120.2°E, 46.4–47.6°N, pinned in `snapshot/viirs_l2_granules.txt` (from CMR `granules.json?short_name=…&bounding_box=118.8,46.4,120.2,47.6`). ~230 MB |
| MODIS active fire L2 | LP DAAC `MOD14` / `MYD14` C6.1, 10-07 12Z – 10-11 03Z | `firms-fetch-modis-l2` | 24 granules in `snapshot/modis_l2_granules.txt`. 9 MB |
| MODIS active fire NRT | FIRMS `MODIS_C6_1_Global_7d.csv` downloaded 2026-10-18 (10-11 to 10-18) | — (snapshot) | FIRMS no longer serves that file; `snapshot/MODIS_C6_1_Global_7d_box.csv` keeps its rows in 44–50.5°N, 110–124°E (`snapshot_modis_nrt.py` shows the cut) |
| Copernicus DEM GLO-90 | `copernicus-dem-90m.s3.amazonaws.com`, tiles N46–N47 × E118–E120 | `firms-fetch-dem` | 27 MB, no credentials |
| GIBS false colour | GIBS WMS `epsg4326/best`, `VIIRS_NOAA21_…_BandsM11-I2-I1` 10-16 (118.8–120.2°E, 46.4–47.6°N, 1400×1600) and 10-12; `VIIRS_NOAA20_…` 10-14 (118.8–120.1°E, 46.5–47.5°N, 1300×1460) | `firms-fetch-gibs` | A fresh download on 2026-10-20 was byte-identical to the files the figures were drawn from |
| Border (OSM, ODbL) | OSM API `map?bbox=` four tiles over 118.85–119.90°E, 46.40–47.50°N (FIRMS figures); Overpass `way[boundary=administrative][admin_level=2](46.3,118.5,47.8,120.5)` (animation) | `firms-fetch-osm`, `firms-border` | The Overpass answer of 2026-10-20 was identical to the one of 2026-10-18 |

Derived (`data/firms/`): `viirs_l2.csv`, `modis_l2.csv`, `main_r2.csv`, `main_r3.csv`, `passes_r2.csv`,
`passes_r3.csv`, `border_osm_mapbbox.json`, `border_osm_overpass.json`.

Credentials: an Earthdata Login in `~/.netrc` (`machine urs.earthdata.nasa.gov login … password …`) for the two
L2 fetch steps. Nothing else needs an account.

### Snapshot

- `snapshot/MODIS_C6_1_Global_7d_box.csv` (37 KB): FIRMS MODIS C6.1 NRT, NASA; the only source for MODIS after 10-11.
- `snapshot/viirs_l2_granules.txt` (20 KB), `snapshot/modis_l2_granules.txt` (4 KB): granule URLs.

## Rules that reproduce the published numbers

- Granules: CMR can list two production versions of one granule; the newest per (product, start time) is used,
  and an NRT granule only where no standard granule exists. Without this the NOAA-20 10-12 passes count twice.
- Detection time is the granule start (UTC). FIRMS `acq_time` is 2–4 min later; the 10-13/14 and 10-14/15 figures
  select each pass by (satellite, `acq_time` − 8 min … `acq_time`] and label it with the FIRMS time.
- MODIS before 10-11 00:30Z comes from the standard MOD14/MYD14 product, after it from FIRMS NRT. On the one
  overlapping pass (Terra 10-11 00:50Z) both give 74 detections, 3,571.69 MW.
- Tables (`tables.py`): box 46.3–47.9°N, 118.3–120.6°E; a pass is a 30-min UTC bin with ≥ 3 detections.
  Each report's table is cut where its FIRMS download ended: r2 at 10-12 06:35Z; r3 at 10-13 00:35Z, with NOAA-20
  only to 10-12 05:27Z because that report's NOAA-20 download failed. The r3 figures therefore lack the NOAA-20
  10-12 17:24Z and 10-13 03:30Z passes, as published.
- Burn scars (`common.scar_masks`): R > 1.4 G, G < 75, R > 20, opening ×2, components ≥ 5 km², closing ×3. The
  10-13/14 figure uses the largest hole-filled component of 10-12 NOAA-21 (4,450 km²), the 10-14/15 figure the
  unfilled mask of 10-14 NOAA-20.
- Side of the border: points inside the longest merged OSM border line, closed westwards at 117.5°E, are Mongolian.

## Differences from the published figures

- Every count, FRP sum and area equals the published value.
- `firms-20261014-1015` has a tenth legend entry, S-NPP 10-15 05:48Z (1 detection, 4.12 MW, 47.069°N 119.625°E),
  marked * and timed by its granule start. When the published figure was drawn the FIRMS S-NPP 7-day file still
  ended at 05:42Z, so this pass was not yet in it.
- The poster greys the "within 3 h" and "within 12 h" legend entries, which have no point in frame 285; the
  published Chinese poster was the plain video frame.
- Chinese renders use the shared layout of the English and Japanese versions (legend positions, place labels
  inside the frame, the East Ujimqin label, the time-axis label "北京时间" under the FRP timeline, HH:MM colour-bar ticks, the legend title
  of the time series and the * entry above) with the wording of the published Chinese figures. Numbers carry
  thousands separators (2,299 where the published Chinese figure had 2299).
