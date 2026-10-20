#!/bin/sh
# Copernicus DEM GLO-90 tiles over 46-48°N, 118-121°E from the public AWS bucket (no credentials).
set -eu
dir="$NUMRUG_DATA/firms/raw/dem"
mkdir -p "$dir"
for lat in 46 47; do
  for lon in 118 119 120; do
    t="Copernicus_DSM_COG_30_N${lat}_00_E${lon}_00_DEM"
    [ -e "$dir/$t.tif" ] || curl -sf -o "$dir/$t.tif" "https://copernicus-dem-90m.s3.amazonaws.com/$t/$t.tif"
  done
done
ls "$dir"
