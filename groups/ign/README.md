# ign: ignition and smoke transport

| Figure | What | Script |
|---|---|---|
| `ignition-gk2a-20261008-ir` | GK-2A 3.8 µm, five scans 11:41–12:21 UTC+8, ignition-pixel excess over background | `fig_gk2a.py ir` |
| `ignition-gk2a-20261008-vis` | GK-2A 0.64 µm, four scans 11:41–12:11 UTC+8 | `fig_gk2a.py vis` |
| `ignition-viirs-20261008` | First three VIIRS passes (NOAA-21, S-NPP, NOAA-20): composites, I4, fire detections | `fig_viirs.py` |
| `smoke-transport-s5p-20261011-1012-v2` | TROPOMI CO and UV aerosol index 10-11/10-12 with back trajectories (en/ja stem without `-v2`) | `fig_s5p.py` |
| `pm25-hailar-baicheng-20261007-1014-v2` | Hourly PM2.5/PM10/CO at Hulunbuir (Hailar) and Baicheng (en/ja stem without `-v2`) | `fig_pm25.py` |

Ignition point: 46.883°N 119.395°E. All local times are UTC+8.

## Data

| Input | Source | Prepare step |
|---|---|---|
| GK-2A AMI L1B full disk, `sw038`/`ir105` (2 km) and `vi006` (0.5 km), 2026-10-08 03:40–04:20 UTC | NOAA open data `s3://noaa-gk2a-pds/AMI/L1B/FD/202610/08/{03,04}/`, anonymous (`granules/gk2a.txt`, ~2.2 GB) | `ign-gk2a-download` |
| VIIRS L1B + geolocation: VJ202IMG/VJ203IMG/VJ202MOD/VJ203MOD A2026281.0406 (C2.1 `.021`), VNP02IMG/VNP03IMG A2026281.0442 (`.002`), VJ102IMG/VJ103IMG A2026281.0500 (`.021`) | NASA LAADS DAAC (`granules/viirs_l1b.txt`, ~1.5 GB) | `ign-viirs-download` |
| VIIRS 375 m active fire L2 v002: VJ214IMG A2026281.0406, VNP14IMG .0442, VJ114IMG .0500 | NASA LP DAAC (`granules/viirs_af.txt`, 7 MB) | `ign-viirs-af-download` |
| TROPOMI L2 OFFL `S5P_L2__CO_____HiR.2` and `S5P_L2__AER_AI_HiR.2`, orbits 46602/46603 (10-11) and 46616/46617 (10-12), processor 02.09.01 | NASA GES DISC (`granules/s5p.txt`, ~1.7 GB) | `ign-s5p-download` |
| `china_{cities,sites}_20261007…14.csv`, hourly national air quality | quotsoft.net mirror, no login (`granules/quotsoft.txt`, 16 MB) | `ign-quotsoft-download` |
| ECMWF IFS 0.25° hourly wind, 10 m / 925 / 850 / 700 hPa, 0.5° grid 43–51°N × 114–126°E, 10-09…10-12 UTC | Open-Meteo historical-forecast API, `models=ecmwf_ifs025` (3 MB) | `ign-wind-download` |
| China–Mongolia border | OSM, `snapshot/border_osm.json` | — |

Credentials: the NASA downloads need an Earthdata login in `~/.netrc`
(`machine urs.earthdata.nasa.gov login … password …`), with the LAADS, LP DAAC and GES DISC applications authorised in
your Earthdata profile. GK-2A, quotsoft and Open-Meteo need none. Downloads skip files already present.

Derived (prepare): `gk2a_ign_series.json` (`gk2a_series.py`: 5×5 maximum vs. median of the 25×25 window outside the
central 9×9; scan time interpolated by line within the full-disk scan), `viirs_*.npz` (`viirs_crop.py`: nearest-neighbour
resampling to a 0.0035° grid, bow-tie fill pixels dropped first), `viirs_af_1008.csv` (`viirs_af.py`), `traj/back_traj.json`
(`traj.py`: 36 h kinematic back trajectories, 10-min midpoint steps, no vertical motion or diffusion) and
`aq_hourly_long.csv` (`extract_aq.py`).

## Checked numbers

- GK-2A scans 11:41/11:51/12:01/12:11/12:21; excess +0.9/+8.4/+15.8/+18.1/+35.8 K; 11:41 pixel 298.57 K vs background
  297.62 ± 2.03 K, 12:21 331.28 K.
- VIIRS: detections / FRP 3 / 236 MW, 19 / 1,032 MW, 13 / 593 MW; I4 maximum 346.2 / 354.0 / 351.3 K (background 291.1 /
  294.1 / 292.5 K); hot pixels 22 / 43 / 49; view zenith 48.2 / 24.9 / 11.1°. The FRP sum is rounded to 0.1 MW first, so
  235.46 → 235.5 → "236".
- TROPOMI overpasses (scanline nearest the ignition point): 11:52, 13:31 (10-11); 11:33, 13:12 (10-12).
- Hailar 10-11 09:00 arrival: the 10 m trajectory passes 4 km from the fire at 10-10 11:00, 925 hPa 24 km at 12:50.
- Air quality peaks: Hulunbuir 10-11 10:00 PM2.5 75; Baicheng 10-12 PM2.5 up to 225, PM10 255.

## Differences from the published figures

- Fire detections: the published figure used FIRMS NRT, which no longer serves 10-08. The points here are the standard
  VIIRS L2 detections of the same three granules; counts and FRP agree with the published boxes. Their time is the granule
  start (04:06, 04:42, 05:00 UTC), so a pass is selected by granule, not by a window around the overpass time. The zh
  box keeps its published wording "FIRMS"; en/ja say "VIIRS active fire (NASA)".
- Air quality: the mirror has since filled 16 hours on 10-13/10-14 that were missing when the figure was published. en
  and ja draw the full series; zh drops those hours (`mirror_as_published`) and so matches the published curve. Both are
  cut at 10-14 15:00, the last hour at publication. The Baicheng satellite note names the actual TROPOMI passes
  (11:33, 13:12) as in the published `-v2`.
- zh layout follows the shared layout, so it is not pixel-identical to the published webp: the GK-2A "数字…" note is
  vertically centred, the VIIRS image is centred in a fixed 1606×1691 px frame instead of a tight bbox, and the
  PM2.5 "起火" label has a white halo. Wording, numbers and colours are the published ones.

## Language values

Besides strings, the catalogs hold: `excess_weight` (GK-2A panel numbers, zh semibold), `arxan_size` (ja 8 pt),
`ignition_dx`/`ignition_ha` (S5P ignition label placement), `panel_size` (S5P panel titles, zh 10 pt), `time_sep`,
`xlabel` (zh has no x-axis label) and `mirror_as_published`.
