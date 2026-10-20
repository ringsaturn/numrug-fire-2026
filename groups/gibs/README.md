# gibs: NASA GIBS imagery and burn-scar figures

Eleven figures drawn on NASA GIBS Corrected Reflectance tiles (MODIS 250–500 m, VIIRS 375 m), with burn-scar
areas from a colour threshold and the China–Mongolia border from OpenStreetMap.

| Figure | Script | What it shows |
|---|---|---|
| `south-scar-20261016` | `fig_south_scar.py` | separate scar south of the main fire, 10-14 vs 10-16, with the three MODIS detections of 10-15 |
| `gibs-daily-1007-1009-v2`, `gibs-daily-1010-1012-v3` | `fig_gibs_daily.py a\|b` | daily true / false colour mosaics, 10-07..10-12 |
| `gibs-wide-20261012-v2` | `fig_gibs_wide.py` | the five 10-12 true-colour mosaics, 44–50°N, 114–124°E |
| `final-scar-20261012-v3` | `fig_final_scar_1012.py` | burned area on the five 10-12 scenes (3,249–4,450 km², median 3,672) |
| `final-scar-20261013-v2` | `fig_final_scar_1013.py` | main patch vs all patches, 10-12 VIIRS and 10-13 Terra (green < 75 and < 110) |
| `scar-delta-20261015` | `fig_scar_delta.py` | new scar on 10-14 / 10-15 against the 10-12 NOAA-21 reference (249 / 279 km² inside the unburned island) |
| `border-gibs-20261013-south`, `-west-arxan` | `fig_border_gibs.py south\|west-arxan` | scar edge and border in two sections, area outside the line in a box |
| `border-east-20261012-falsecolor`, `-truecolor` | `fig_border_east.py falsecolor\|truecolor` | eastern front 13–17 km west of Arxan, with same-overpass FIRMS detections |

The en/ja posts publish `gibs-daily-1010-1012` and `final-scar-20261012` as `-v2` (see `published` in `figures.toml`).

## Data and prepare steps

All inputs land in `data/gibs/`. Run `numrug-figs prepare --group gibs`.

| Step | Writes | Source |
|---|---|---|
| `gibs-fetch-tiles` | `raw/gibs/<box>_<day>_<sat>_CorrectedReflectance_<bands>.{jpg,png}` (40 tiles, 22 MB) | GIBS WMS `https://gibs.earthdata.nasa.gov/wms/epsg4326/all/wms.cgi`, layers `MODIS_{Terra,Aqua}_CorrectedReflectance_{TrueColor,Bands721}_v6.1_NRT`, `VIIRS_SNPP_…_v2_NRT`, `VIIRS_NOAA2{0,1}_…_v2.1_NRT`; boxes in `scripts/common.py` (`BOXES`) |
| `gibs-fetch-borders` | `raw/osm/map_*.osm`, `raw/overpass/border_admin2_south.json`, `raw/ne/` | OSM API 0.6 `/map` for four tiles over 118.85–119.90°E, 46.40–47.50°N; Overpass `way[admin_level=2][boundary=administrative](46.3,118.5,47.8,120.5); out geom;`; Natural Earth `ne_10m_admin_0_boundary_lines_land` v5.1.0 (naciscdn) |
| `gibs-fetch-firms` | `raw/firms/*_NRT_2026285.txt` (9 MB) | LANCE FIRMS NRT daily archive `https://nrt3.modaps.eosdis.nasa.gov/archive/FIRMS/<sensor>/Global/`, day 285 = 10-12; **needs an Earthdata login in `~/.netrc`** (`machine urs.earthdata.nasa.gov login … password …`) |
| `gibs-borders` | `border/border_osm.json`, `border_osm_south.json`, `border_ne.json` | line lists from the three border sources |
| `gibs-firms` | `firms/firms_20261012.csv` | 10-12 detections in 46.3–47.9°N, 118.3–120.6°E with side of the OSM border (`cty`) |
| `gibs-scar` | `scar/scar_masks.npz`, `scar/scar_areas.json` | burn-scar masks and areas on the 10-12 and 10-13 zoom scenes |
| `gibs-scar-delta` | `scar/scar_delta_20261015.json` | new burned area 10-14 / 10-15, split into island / east front / edge band |
| `gibs-south-scar` | `scar/south_scar_20261016.json` | area of the south scar on 10-16 (NOAA-21 10.1 km², S-NPP 4.5 km², all on the Chinese side) |

Burn-scar rule (`common.scar_layers`): red/green > 1.4, green < 75, red > 20; binary opening ×2; keep patches
≥ 5 km²; closing ×3; fill holes; the main patch is the largest. "Outside the border line" means on the Chinese side of
the OSM line, which is closed westward along 117.5°E. Pixel areas use 111.32·cos(lat) × 110.95 km per degree.

Files other groups may read: `border/border_osm.json`, `border/border_osm_south.json`, `border/border_ne.json`,
`firms/firms_20261012.csv`, `scar/scar_masks.npz` (keys `<scene>_main`, `<scene>_all`, scenes in
`common.SCENES`, `-g110` for the green < 110 run), `scar/scar_areas.json`, `scar/south_scar_20261016.json`.

### Snapshot

- `snapshot/firms_box_20261014_20261015.csv` (14 KB): FIRMS detections in 46.4–47.6°N, 118.8–120.2°E from the four
  global FIRMS 24 h CSVs (VIIRS S-NPP / NOAA-20 / NOAA-21 C2, MODIS C6.1) downloaded 2026-10-15 13:30 UTC, with side
  of the OSM border and distance to it. The 24 h files of that day are no longer served. Source: NASA FIRMS
  (LANCE), free to redistribute with attribution. Only `scar-delta-20261015` reads it.

## Why the NRT layers

In October 2026 the GIBS `best` endpoint served the NRT imagery. By 10-19 it serves the science-quality MODIS
imagery (`*_v6.1_STD`) for 10-09..10-13, which moves the 10-12 MODIS scar areas (Terra 3,248 vs 3,249 km²; Aqua
3,691 vs 3,672 km², 28.5 vs 26.7 km² outside the line). The versioned NRT layers reproduce every published number;
`fetch_gibs.py` requests them explicitly. The 10-13 S-NPP and NOAA-21 tiles are blank and are not fetched.

## Checks against the published figures

All printed numbers match the published figures: 10-12 areas 3,249 / 3,437 / 4,450 / 4,378 / 3,672 km² with
19 / 20 / 40 / 39 / 27 km² outside the line; 10-13 main patch 2,046 (green < 75) and 4,193 km² (green < 110);
scar-delta reference 4,450 km², new inside the island 249 and 279 km²; border-gibs south 17.3 km² / 4.2 km,
13.1 / 2.9, 15.9 / 3.2, 9.9 / 3.2, west of Arxan 0.0 in all four panels.

The border-gibs figures were first drawn from the scar masks of a run that had only the Terra scene for 10-13.
The masks of every scene they use are identical to those of the full 10-13 run (`gibs-scar`), so they read
`scar/scar_masks.npz` like the other figures.

## Known differences

- `scar-delta-20261015` en/ja differ from the earlier renders in 0.02 % of pixels: where two OSM ways meet, the
  black halo of one way is drawn over the other in a different order (the way order is now sorted by OSM id).
- Line styles of borders and of the scar-delta reference scar come from the catalogs (`osm`, `ne`, `ref_line` tables
  per figure). The Chinese catalog keeps the published Chinese styling, which the Chinese captions describe: dashed
  yellow OSM line (south-scar, gibs-daily, final-scar-20261013, border-gibs), pale dashed yellow Natural Earth line
  (gibs-daily, gibs-wide), and in scar-delta a yellow reference scar with a dashed cyan OSM line. en/ja use solid
  yellow OSM, dashed cyan Natural Earth and a white haloed reference scar.
- The scar-delta reference area is printed with a thousands separator (4,450 km²); the published Chinese figure had 4450.

## Credits

Imagery: NASA GIBS / Worldview (LANCE NRT). Fire detections: NASA FIRMS. Borders: © OpenStreetMap contributors
(ODbL); Natural Earth (public domain).
