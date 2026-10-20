#!/usr/bin/env bash
# Rebuild the four model runs of 2026-10-13 as Zarr stores with xue's `build-local`, cropped to
# 105–135°E 38–56°N. Needs a checkout of github.com/ringsaturn/xue at tag v0.40.0 with its
# environment set up (`uv sync`; GDAL, and om2nc for IFS HRES), given as XUE_REPO.
#
#   data/weather/xue/local/<model>.<run>/       map bundles to +192 h (upper, surface)
#   data/weather/xue/local-full/<model>.<run>/  point bundles over the axis the meteogram autoscales on
#   data/weather/xue/raw/                       the downloaded GRIB / om2nc NetCDF (about 7.5 GB)
#
# GFS from noaa-gfs-bdp-pds, ECMWF IFS and AIFS from the ecmwf-forecasts bucket (ECMWF open data),
# IFS HRES 0.1° from Open-Meteo's open-data bucket. A run whose manifest exists is skipped.
set -euo pipefail
: "${XUE_REPO:?set XUE_REPO to a checkout of github.com/ringsaturn/xue at v0.40.0}"
W="${NUMRUG_DATA:-$(pwd)/../../data}/weather/xue"
mkdir -p "$W"
W="$(cd "$W" && pwd)"
BBOX=105,38,135,56

build() {  # OUT MODEL RUN HOURS BUNDLE...
  local out=$1 model=$2 run=$3 hours=$4; shift 4
  if [ -f "$W/$out/$model.$run/manifest.json" ]; then
    echo "skip $out/$model.$run"; return
  fi
  (cd "$XUE_REPO" && uv run python -m xuebuild build-local --model "$model" --run "$run" --hours "$hours" \
     --bbox="$BBOX" --bundles "$@" --output-dir "$W/$out" --raw-dir "$W/raw" --work-dir "$W/work" --no-series)
}

build local ecmwf 2026101300 192 hgt500 wind250 prmsl wind10m prate
build local gfs   2026101306 192 hgt500 wind250 prmsl wind10m prate
build local-full ecmwf   2026101300 240 prmsl wind10m prate gust
build local-full gfs     2026101306 240 prmsl wind10m prate gust
build local-full aifs    2026101306 360 prmsl wind10m prate
# The IFS HRES archive behind om2nc ends at +192 h for this run.
build local-full ifshres 2026101300 192 prmsl wind10m prate gust
