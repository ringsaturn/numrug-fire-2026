#!/usr/bin/env bash
# Download every URL in a list (granules/*.txt) into data/ign/<subdir>/, skipping files already there.
#   fetch.sh LIST SUBDIR [earthdata]
# "earthdata" sends ~/.netrc credentials (urs.earthdata.nasa.gov) and keeps the session cookie.
set -euo pipefail
list=$1
dst="${NUMRUG_DATA:-../../data}/ign/$2"
mkdir -p "$dst"
auth=()
if [ "${3:-}" = earthdata ]; then
  jar=$(mktemp)
  trap 'rm -f "$jar"' EXIT
  auth=(-n -c "$jar" -b "$jar")
fi
grep -v '^#' "$list" | while read -r u; do
  [ -n "$u" ] || continue
  f="$dst/$(basename "$u")"
  [ -e "$f" ] && continue
  echo "get $u"
  curl -sSfL ${auth[@]+"${auth[@]}"} -A 'numrug-fire-2026/1.0' --retry 5 --retry-delay 20 -o "$f.part" "$u"
  mv "$f.part" "$f"
done
echo "$2: $(ls "$dst" | wc -l | tr -d ' ') files"
