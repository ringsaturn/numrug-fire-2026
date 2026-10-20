#!/bin/sh
# Natural Earth 10m land boundary lines (v5.1.0, public domain) into data/ahi/ne/.
set -eu
R="${NUMRUG_DATA:-../../data}/ahi/ne"; mkdir -p "$R"
N=ne_10m_admin_0_boundary_lines_land
[ -s "$R/$N.shp" ] && exit 0
curl -sfL -o "$R/$N.zip" "https://naciscdn.org/naturalearth/10m/cultural/$N.zip"
unzip -o -q "$R/$N.zip" -d "$R" && rm "$R/$N.zip"
