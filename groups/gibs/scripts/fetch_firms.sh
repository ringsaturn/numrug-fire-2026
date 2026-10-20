#!/usr/bin/env bash
# FIRMS active-fire records for 2026-10-12 (day 285) from the LANCE FIRMS NRT daily archive.
# These are the records the FIRMS 7-day CSVs carried on 10-12; the 7-day files no longer reach back that far.
# The archive redirects to Earthdata login: put your credentials for urs.earthdata.nasa.gov in ~/.netrc.
set -euo pipefail
OUT="${NUMRUG_DATA:-../../data}/gibs/raw/firms"
mkdir -p "$OUT"
JAR="$(mktemp)"; trap 'rm -f "$JAR"' EXIT
B=https://nrt3.modaps.eosdis.nasa.gov/archive/FIRMS
for f in suomi-npp-viirs-c2/Global/SUOMI_VIIRS_C2_Global_VNP14IMGTDL_NRT_2026285.txt \
         noaa-20-viirs-c2/Global/J1_VIIRS_C2_Global_VJ114IMGTDL_NRT_2026285.txt \
         noaa-21-viirs-c2/Global/J2_VIIRS_C2_Global_VJ214IMGTDL_NRT_2026285.txt \
         modis-c6.1/Global/MODIS_C6_1_Global_MCD14DL_NRT_2026285.txt; do
  dst="$OUT/$(basename "$f")"
  [ -s "$dst" ] && { echo "kept $(basename "$f")"; continue; }
  curl -sfSL -n -c "$JAR" -b "$JAR" -A numrug-fire-2026/1.0 -o "$dst.part" "$B/$f"
  head -c 9 "$dst.part" | grep -q '^latitude' || { echo "not a FIRMS CSV (Earthdata login?): $f" >&2; rm -f "$dst.part"; exit 1; }
  mv "$dst.part" "$dst"; echo "got $(basename "$f")"
done
