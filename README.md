# numrug-fire-2026

Scripts that rebuild, from public satellite and weather data, every figure of a
write-up on the October 2026 grassland fire in the Numrug Strictly Protected Area
(Dornod, Mongolia) on the China–Mongolia border.

The write-up was published as
[蒙古国东方省努木尔格草原火：卫星监测与天气形势](https://blog.ringsaturn.me/posts/2026-10-12-arxan-fire/)
(Chinese, with English and Japanese versions). Its address and the figure file names
say "arxan" because the first fire detections were only known to lie west of Arxan;
the fire turned out to burn almost entirely inside the Mongolian reserve. Figure file
names keep the published names, so a rebuilt figure can replace the published one
directly.

Every figure renders in Chinese (`zh`), English (`en`) and Japanese (`ja`). All text
lives in TOML catalogs, so a new language needs no Python changes.

## Quick start

```sh
uv sync                                  # Python 3.12, pinned versions
uv run numrug-figs list                  # prepare steps and figures, per group
uv run numrug-figs prepare               # fetch and derive inputs into data/ (~15 GB)
uv run numrug-figs render --lang en      # out/<name>.en.png (and .mp4)
uv run numrug-figs webp --lang en        # out/webp/, as published
```

`prepare --group ahi` / `render --group ahi NAME` restrict a run. Set `NUMRUG_DATA`
and `NUMRUG_OUT` to move data and output elsewhere. The animation needs `ffmpeg`
with libx264.

Credentials: NASA Earthdata (VIIRS/MODIS L1B and L2, TROPOMI, the LANCE FIRMS
archive) is read from `~/.netrc`
(`machine urs.earthdata.nasa.gov login … password …`). Everything else is anonymous.
The weather group's xue model stores additionally need a checkout of
[xue](https://github.com/ringsaturn/xue); see `groups/weather/README.md`.

## Layout

| Path | What |
|---|---|
| `figkit/` | language switch and string catalogs (`lang.py`), paths, the `numrug-figs` runner |
| `i18n/<lang>.toml` | shared fonts, date/number formats and common strings per language |
| `groups/<group>/figures.toml` | the group's ordered `prepare` steps and its figures |
| `groups/<group>/scripts/` | fetch, derive and figure scripts |
| `groups/<group>/i18n/<lang>.toml` | the group's figure strings, one table per figure |
| `groups/<group>/snapshot/` | small inputs that can no longer be fetched (FIRMS NRT rows, an OSM border cut) |
| `snapshot/osm-20261025.json`, `figkit/osm.py` | OSM snapshot of 2026-10-25 shared by several groups: Mongolian-side roads, rivers, the reserve boundary, border ways, places, shortest road routes and three hand-digitised Sentinel-2 linear features |
| `groups/<group>/README.md` | sources, granule/item IDs, checks against the published figures, known differences |

| Group | Figures |
|---|---|
| `ahi` | Himawari-9 AHI hotspot series, B07 panels, visible maps, cover |
| `s2` | Sentinel-2 / Landsat 9 overviews, fire fronts, border zooms, dNBR |
| `gibs` | daily MODIS/VIIRS imagery from NASA GIBS, burn-scar extraction, border checks |
| `ign` | ignition (GK-2A, VIIRS L1B), TROPOMI smoke transport, PM2.5 at Hailar and Baicheng |
| `firms` | VIIRS/MODIS active-fire maps and series, the spread animation |
| `weather` | GEFS-Aerosols smoke maps, fire weather, model comparison, synoptic maps, sounding |

## Translating

1. Copy `i18n/en.toml` to `i18n/<xx>.toml` and set `[fonts]` (font files are glob
   patterns; missing ones are skipped) and `[fmt]` (date order, separators).
2. Copy each `groups/*/i18n/en.toml` to `<xx>.toml` and translate the values. Keep
   `{placeholders}` and `\n` line breaks; layout values such as `label_size` may be
   tuned for longer text.
3. `uv run numrug-figs render --lang xx`. Keys you have not translated fall back
   to English and are listed on stderr.

`numrug-figs compare a.png b.png` prints size and mean pixel difference between
two renders.

## Fidelity

With the data in place, the `en` and `ja` renders are pixel-identical to the
published English and Japanese figures. The `zh` renders carry the published
wording, numbers and line styles in the shared layout. Where an original source can
no longer be fetched identically (FIRMS NRT files past their window, GIBS layers
reprocessed to science quality), the scripts fetch the documented substitute or read
a snapshot. Each group README lists what differs and why.

## Data credits

NASA LANCE, FIRMS, GIBS, LAADS DAAC, LP DAAC and GES DISC; JMA Himawari-9 via the
NOAA Open Data Dissemination program; KMA GK-2A via NOAA; Copernicus Sentinel-2
(ESA) via Element 84 Earth Search; USGS Landsat via Microsoft Planetary Computer;
Copernicus DEM GLO-90; Copernicus Sentinel-5P TROPOMI; NOAA GEFS-Aerosols, GFS;
ECMWF open data; Open-Meteo (CC BY 4.0); China air-quality observations via
quotsoft.net; © OpenStreetMap contributors (ODbL); Natural Earth.

## License

The code is MIT-licensed (see `LICENSE`). Data fetched by the scripts, and the
snapshots under `groups/*/snapshot/`, stay under their providers' terms listed above.
