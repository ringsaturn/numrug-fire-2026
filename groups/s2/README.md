# s2: Sentinel-2 and Landsat close-ups

Eight figures of the burn scar, the fire fronts and the China–Mongolia border at 10–40 m resolution.

| Figure | Script | What it shows |
|---|---|---|
| `s2-overview` | `fig_overview.py` | Sentinel-2 L2A on 10-05, 10-08, 10-10 over the fire area (40 m), true colour and SWIR, VIIRS detections of 10-08 and 10-10 |
| `ignition-20261008-v2` | `fig_ignition.py` | Landsat 9 SWIR and B10 surface temperature (02:45Z) and Sentinel-2C SWIR (03:15Z) over the ignition box, first VIIRS detections of 10-08 |
| `s2-fronts-20261010` | `fig_crops.py fronts` | SE fire front and NW fire head at 10 m on 10-10 03:05Z, NOAA-21 VIIRS 03:30Z |
| `border-a` | `fig_crops.py border-a` | Zone A near the Arxan border crossing, 10-05 (20 m) and 10-10 (10 m), VIIRS/MODIS 10-10 11:00Z – 10-11 04:59Z |
| `border-south-zoom-20261013-v2` | `fig_south_zoom.py` | Southern border section: 10-05, 10-08, 10-10 and dNBR 10-05 -> 10-10 |
| `s2-south-20261013-v2` | `fig_zone13.py south` | Same section on 10-13 with dNBR 10-05 -> 10-13 |
| `s2-west-arxan-20261013-v2` | `fig_zone13.py west` | Border section west of Arxan on 10-13 with dNBR 10-05 -> 10-13 |
| `s2-island-20261015` | `fig_island.py` | South edge of the unburned island on 10-15: saturated SWIR pixels and FIRMS 24 h detections |

## Data

| Input | Source | Step |
|---|---|---|
| Sentinel-2 L2A | Element84 Earth Search STAC `sentinel-2-l2a` (`https://earth-search.aws.element84.com/v1`), COGs read through a WarpedVRT onto EPSG:4326 grids; tiles of one day mosaicked by increasing no-data share. BOA offset already removed in this collection. About 1 GB of `.npy`. Item IDs per window in `data/s2/s2/*_meta.json`. | `s2-sentinel2` |
| Landsat 9 | Microsoft Planetary Computer `landsat-c2-l2`, item `LC09_L2SP_122027_20261008_02_T1`, 30 m | `s2-landsat` |
| VIIRS 375 m active fire | `VNP14IMG`, `VJ114IMG`, `VJ214IMG` v002 (NASA LP DAAC) listed from CMR for 10-08 00Z – 10-11 06Z over 46.4–47.6°N, 118.8–120.2°E (42 granules, 82 MB); the newest production version of each granule is used | `s2-fires-fetch`, `s2-fires-tables` |
| MODIS 1 km active fire | `MOD14.A2026283.1120`, `MOD14.A2026283.1255`, `MYD14.A2026283.2025` (C6.1, LP DAAC) | `s2-fires-fetch`, `s2-fires-tables` |
| OSM border | Overpass `way[boundary=administrative][admin_level=2](46.3,118.5,47.8,120.5)`: ways 161028049 … 1464042583, 11 ways, 1,127 nodes. The query still returned the identical geometry on 2026-10-20; the step warns if the way list changes. | `s2-borders` |
| Natural Earth border | `ne_10m_admin_0_boundary_lines_land.geojson` (nvkelso/natural-earth-vector, master), China–Mongolia features clipped to 115–124°E, 44–50°N | `s2-borders` |

Credentials: an Earthdata login in `~/.netrc` (`machine urs.earthdata.nasa.gov login … password …`) for the VIIRS and
MODIS granules. Sentinel-2, Landsat, Overpass and Natural Earth need none.

### Snapshot (`snapshot/`, 8 KB)

FIRMS near-real-time files are rolling (24 h / 7 d) and the October 2026 rows are no longer served, so the two
FIRMS extracts the figures use are kept here (NASA FIRMS, free to redistribute with attribution):

- `firms_modis_7d_20261011.csv` (4.9 KB): FIRMS `MODIS_C6_1_Global_7d.csv` rows of the 10-11 00:54Z Terra pass in the
  fire box (46.4–47.6°N, 118.8–120.2°E), downloaded 2026-10-18; `side` A = Mongolian side, `dkm` = km to the OSM line.
  Used by `border-a` (2 points in zone A).
- `firms_24h_20261015.csv` (3.6 KB): rows of 10-15 from the four FIRMS global 24 h files (S-NPP, NOAA-20, NOAA-21
  VIIRS, MODIS), downloaded 2026-10-15 22:30 UTC+8, same box; `cty` from the OSM line. Used by `s2-island-20261015`.

### Derived (`data/s2/derived/`, rebuilt by `prepare`)

- `border_lines.json` (Natural Earth clip), `viirs_box.csv`, `modis_l2_box.csv`
- `ZA_dnbr_1005_1010.npy`, `ZA_dnbr_1005_1013.npy`, `ZB_dnbr_1005_1013.npy`, `zones_check.json` (`zones.py`)
- `zone_i_hot.json` (`island_hot.py`)

## Checks

- dNBR (`zones_check.json`): ZA 10-05 -> 10-10 burned area on the Chinese side (dNBR > 0.27) 22.55 km², largest
  patch 12.04 km², cloud on the Chinese side 27.8 %; 10-13 cloud ZA 55.7 %, ZB 77.3 %; new in ZA since 10-10 0.14 km².
- Island: 164 saturated SWIR pixels, all on the Mongolian side; FIRMS 9 / 18 / 11 / Aqua 4.
- Fire detections drawn: overview 10-08 65, 10-10 NOAA-21 67; fronts SE 1, NW 17; ignition 65; border-a 158
  (VIIRS 132, MODIS L2 24, FIRMS MODIS 2). Landsat B10 maximum over the ignition box 21.2 °C.

## Differences from the published figures

- Fire points: the published figures read FIRMS NRT CSVs that are gone. VIIRS and MODIS points before 10-11 00:54Z
  now come from the standard L2 products (same algorithm; positions may differ from NRT by a few pixels). en/ja
  label them "VIIRS active fire (NASA)"; zh keeps the published "VIIRS … 火点" and says "VIIRS/MODIS" where the
  published zh said "FIRMS". L2 times are granule start times; the ignition and overview legends keep the FIRMS
  acquisition times 04:08 / 05:48Z (12:08 / 13:48 UTC+8) of the same passes.
- zh: the layout is the shared en/ja one. The overview footer is split into two lines (the published single line ran
  off the image) and names both no-data wedges (top left on 10-05 and 10-10, bottom right on 10-08). The 10-13 dNBR
  panels say 灰为云和云影, matching the mask and the zh caption. Clock times are HH:MM throughout.
