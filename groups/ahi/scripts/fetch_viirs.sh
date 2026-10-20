#!/bin/sh
# Download the VIIRS 375 m active-fire L2 granules listed in granules/viirs_l2.txt
# (VNP14IMG / VJ114IMG / VJ214IMG v002, LP DAAC) into data/ahi/viirs_l2/.
# Needs a NASA Earthdata login in ~/.netrc (machine urs.earthdata.nasa.gov).
set -eu
R="${NUMRUG_DATA:-../../data}/ahi/viirs_l2"; mkdir -p "$R"
xargs -P 6 -n 1 sh -c '
  f="$0/$(basename "$1")"; [ -s "$f" ] && exit 0
  curl -sfn -L -c "$0/.cookies" -b "$0/.cookies" -o "$f.part" "$1" && mv "$f.part" "$f" || echo "FAIL $1"
' "$R" < "$1"
