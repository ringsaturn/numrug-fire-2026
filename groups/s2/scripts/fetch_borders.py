"""Borders: OSM China–Mongolia ways from Overpass, and the Natural Earth 10m boundary lines clipped to the region.

Writes data/s2/border/osm_raw.json, border_osm.json and data/s2/derived/border_lines.json.
The figures were drawn with OSM ways 161028049 … 1464042583 (11 ways, 1,127 nodes, OSM base 2026-10-18);
a later OSM edit of those ways would move the yellow line."""

import json
import os
import urllib.parse
import urllib.request

from common import D

UA = {"User-Agent": "numrug-fire-2026/1.0"}
OVERPASS = "https://overpass-api.de/api/interpreter"
QUERY = '[out:json][timeout:60];way["boundary"="administrative"]["admin_level"="2"](46.3,118.5,47.8,120.5);out geom;'
NE_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_0_boundary_lines_land.geojson"
WAYS = [
    161028049,
    161028050,
    161028053,
    161028055,
    161028059,
    205108243,
    758670569,
    758719716,
    762201561,
    762201571,
    1464042583,
]

for sub in ("border", "ne", "derived"):
    os.makedirs(D(sub), exist_ok=True)

raw = D("border", "osm_raw.json")
if not raw.exists():
    req = urllib.request.Request(OVERPASS, data=urllib.parse.urlencode({"data": QUERY}).encode(), headers=UA)
    raw.write_bytes(urllib.request.urlopen(req, timeout=180).read())
osm = json.load(open(raw))
ways = [e for e in osm["elements"] if e["type"] == "way"]
if [w["id"] for w in ways] != WAYS:
    print("WARNING: Overpass returned different ways than the published figures used:", [w["id"] for w in ways])
segs = [[[g["lon"], g["lat"]] for g in w["geometry"]] for w in ways]
json.dump(segs, open(D("border", "border_osm.json"), "w"))
print("OSM:", len(segs), "ways,", sum(map(len, segs)), "nodes, base", osm["osm3s"]["timestamp_osm_base"])

nef = D("ne", "ne_10m_admin_0_boundary_lines_land.geojson")
if not nef.exists():
    nef.write_bytes(urllib.request.urlopen(urllib.request.Request(NE_URL, headers=UA), timeout=300).read())
out = []
for f in json.load(open(nef))["features"]:
    if {f["properties"].get("ADM0_LEFT"), f["properties"].get("ADM0_RIGHT")} != {"China", "Mongolia"}:
        continue
    g = f["geometry"]
    for p in g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]:
        q = [c for c in p if 115 <= c[0] <= 124 and 44 <= c[1] <= 50]
        if len(q) > 1:
            out.append(q)
json.dump(out, open(D("derived", "border_lines.json"), "w"))
print("Natural Earth:", len(out), "segments")
