# weather: smoke model and weather figures

| Figure | Script | What it shows |
|---|---|---|
| `smoke-pm25-maps` | `scripts/smoke_maps.py` | GEFS-Aerosols surface PM2.5 with observed city PM2.5, 10-11 08:00 and 10-12 20:00 UTC+8; the 10-08 00Z run (before this fire entered the model) against two runs with it |
| `smoke-pm25-series` | `scripts/smoke_series.py` | Hailar and Baicheng: observed PM2.5 and CO against the model at the city |
| `fire-weather-20261013` | `scripts/fire_weather.py` | Hourly T, Td, precipitation, RH, wind and gust at the fire, 10-08..10-21 |
| `models-daily-20261013-2000` | `scripts/models_daily.py` | Daily min RH, max gust, 14:00 wind direction and precipitation from ECMWF, GFS, CMA-GRAPES, ICON; this report against the previous one |
| `upper-20261013-2000` | `scripts/synoptic.py upper` | 500 hPa height and 250 hPa jet, ECMWF 10-13 00Z and GFS 10-13 06Z |
| `surface-20261013-2000` | `scripts/synoptic.py surface` | Sea-level pressure, 10 m wind, rain rate, same runs |
| `meteogram-20261013-2000` | `scripts/synoptic.py meteogram` | Pressure, wind/gust, rain rate and accumulation at the fire from ECMWF, GFS, IFS HRES, AIFS |
| `skewt-20261013-2000-v2` | `scripts/skewt.py` | 10-13 12Z soundings at Hailar 50527, Xilinhot 54102, Tongliao 54135 |

Times on the figures are Beijing time (UTC+8). Strings are in `i18n/<lang>.toml`; `[synoptic]`
holds the ones the three xue-run figures share.

## Prepare steps and data sources

All in `figures.toml`, run in order by `numrug-figs prepare --group weather`. No credentials are needed.

| Step | Source | Output (`data/weather/`) |
|---|---|---|
| `weather-base` | Natural Earth 50 m coastline, admin-0 and admin-1 lines, GeoJSON from `github.com/nvkelso/natural-earth-vector` at commit `ca96624a` (public domain) | `base/` (3 MB) |
| `gefs-aerosols` | NOAA GEFS-Aerosols (GEFSv12 chemistry, control, 0.25°), `noaa-gefs-pds` on AWS, `gefs.YYYYMMDD/HH/chem/pgrb2ap25/gefs.chem.tHHz.a2d_0p25.fFFF.grib2`, six records per file by `.idx` byte range: AOD 550 total/POM/BC, surface PM2.5, column BC/POM. Runs 2026-10-08 00Z to +120 h; 10-08 12Z..10-13 00Z every 12 h to +48 h | `gefs/<run>/fFFF.grib2` (900 MB) |
| `aq-fetch` | China National Environmental Monitoring Centre hourly site data via the quotsoft.net mirror, `https://quotsoft.net/air/data/china_sites_YYYYMMDD.csv`, 10-07..10-14 | `aq/` (12 MB) |
| `aq-cities` | the above + `snapshot/stations.csv` | `aq/city_hourly.csv` |
| `gefs-points` | `gefs/` | `gefs-points/points.csv`, `fire_box.csv` |
| `openmeteo` | Open-Meteo Single Runs API (`single-runs-api.open-meteo.com`), ~180 archived runs of `ecmwf_ifs`, `ecmwf_ifs025`, `ncep_gfs013`/`ncep_gfs025`/`gfs_seamless`, `cma_grapes_global`, `icon_seamless` | `om/runs/` cache, `om/*.json` |
| `xue-runs` | `xuebuild build-local` from a checkout of `github.com/ringsaturn/xue` at tag `v0.40.0` (set `XUE_REPO`; needs that repo's `uv sync`, GDAL, and om2nc for IFS HRES). GFS from `noaa-gfs-bdp-pds`, ECMWF IFS and AIFS from ECMWF open data (`ecmwf-forecasts` bucket), IFS HRES 0.1° from Open-Meteo's open-data bucket | `xue/local/`, `xue/local-full/` (Zarr, 35 MB), `xue/raw/` (7.5 GB) |
| `xue-case` | the stores above, and the archived xue sounding issue `https://dataset.ringsaturn.me/xue/sounding/2026/10/13/sounding.2026101314/` (generated 10-13 14:34Z, live at the original fetch) | `xue-case/` |

### How the forecasts are pinned

- **fire-weather.** The original request (10-13 05:28Z) asked the forecast API for the default
  model at 47.0°N 119.4°E; that is ECMWF IFS 9 km (`ecmwf_ifs`, grid 46.9947/119.3669). Rebuilt
  with runs up to 10-12 18Z: the 10-13 00Z files reached the archive at 05:30Z, after the request.
  Stitching `best_match` itself would be wrong after +90 h of the 18Z run, because the single-run
  best_match fills that tail with GFS.
- **models-daily.** This report = all four models at 10-13 06Z (served 14:14Z). The previous report
  (05:34Z): ECMWF 0.25° 10-12 18Z, CMA 10-12 18Z, ICON 10-13 00Z, and `gfs_seamless` mixed: T, RH,
  wind and precipitation from GFS 0.13° 10-13 00Z, gusts from GFS 0.25° 10-12 18Z (0.13° has no
  gust and 0.25° had not updated yet). Identified from the daily precipitation logged at the time
  and the published dotted GFS gust line.
- **xue runs.** ECMWF 2026101300, GFS 2026101306, IFS HRES 2026101300, AIFS 2026101306, as the
  10-13 14:36Z fetch recorded; crop 105–135°E 38–56°N. `local/` holds the map bundles to +192 h;
  `local-full/` the point bundles to +240 h (GFS, ECMWF), +360 h (AIFS) and +192 h (IFS HRES, where
  the archive ends), because the meteogram's y limits autoscale over the whole axis.

## Snapshot

- `snapshot/stations.csv` (1.3 kB): the 24 national monitoring sites of the seven cities, from the
  quotsoft.net site list `站点列表-2022.02.13起.csv` (code, name, city, lon, lat, control site). The
  full list is only distributed through a Baidu Pan share, so the rows used are kept here.

## Known differences from the published figures

Each en/ja render is pixel-identical to the rebuilt English/Japanese figures; zh shares their layout.

- **models-daily:** the Single Runs and Previous Runs archives have no `ecmwf_ifs025` gusts between
  +90 and ~+150 h in any run, so ECMWF's 10-17 daily max gust is 11.7 m/s against 12.4 published, and
  its 10-21 minimum RH 54 % against 55 %. The previous-report precipitation agrees to 0.1–0.3 mm/day
  (GFS, ICON). Daily bars of this report differ by up to ~0.2 mm.
- **meteogram:** rain rates are within a few per cent of the published ones (AIFS accumulates ~19.8
  against ~20.3 mm, IFS HRES ~14.7 against 15.0). Likely the prate quantization of xue v0.40.0
  against the encoder that built the live runs on 10-13; not verified. The AIFS gust legend entry
  is dropped because AIFS has no gust.
- **upper / surface:** the en/ja titles add that the 5880 gpm contour is not reached and where the
  17.2 m/s contour occurs; zh keeps the published wording.
- **zh layout** (shared with en/ja): times as HH:MM, a local-time axis label on every time axis,
  smoke-series headroom and two-column legend, the fire-weather wind legend below 0 m/s, the
  models-daily RH axis to 97 %, thousands separators in the skew-T values.
- **air quality:** the quotsoft mirror has since filled some missing hours of 10-13 and 10-14. A
  fresh `aq-fetch` (checked 2026-10-20) gets 1,116 city-hours instead of 997, and both smoke
  figures come out pixel-identical.
