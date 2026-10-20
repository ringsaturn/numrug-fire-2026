#!/bin/sh
# Download the Himawari-9 AHI HSD segments listed in a key file (one bucket key per line)
# from the NOAA open-data bucket into data/ahi/raw/. Anonymous HTTPS, 8 at a time; files
# already present are skipped, so the step can be re-run after an interruption.
set -eu
R="${NUMRUG_DATA:-../../data}/ahi/raw"; mkdir -p "$R"
xargs -P 8 -n 1 sh -c '
  f="$0/$(basename "$1")"; [ -s "$f" ] && exit 0
  curl -sf --retry 5 --retry-delay 5 -o "$f.part" "https://noaa-himawari9.s3.amazonaws.com/$1" && mv "$f.part" "$f" || echo "FAIL $1"
' "$R" < "$1"
