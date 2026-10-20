#!/bin/sh
# Download every URL listed in $1 into $NUMRUG_DATA/firms/raw/$2 with Earthdata Login (~/.netrc), six at a time.
# Files already present (or symlinked) are skipped.
set -eu
list=$1
dir="$NUMRUG_DATA/firms/raw/$2"
mkdir -p "$dir"
get() {
  f="$dir/$(basename "$1")"
  [ -e "$f" ] && return 0
  curl -sfn -L -c "$dir/.cookies" -b "$dir/.cookies" -o "$f.part" "$1" && mv "$f.part" "$f" || echo "failed: $1" >&2
}
n=0
while read -r u; do
  [ -n "$u" ] || continue
  get "$u" &
  n=$((n + 1))
  [ $((n % 6)) -eq 0 ] && wait
done < "$list"
wait
echo "$(ls "$dir" | grep -c -v '^\.') files in $dir"
