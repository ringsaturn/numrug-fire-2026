"""OSM downloads -> data/firms/border_osm_mapbbox.json and border_osm_overpass.json, each a list of [[lon, lat], ...] ways.

mapbbox: every way of an admin_level=2 relation or tagged boundary=administrative + admin_level=2 in the map tiles,
ordered by way id. overpass: the ways of the Overpass answer in its order."""

import glob
import json
import xml.etree.ElementTree as ET

from common import D, RAW

nodes, ways, members = {}, {}, set()
for f in sorted(glob.glob(str(RAW / "osm" / "map_*.osm"))):
    r = ET.parse(f).getroot()
    for n in r.iter("node"):
        nodes[n.get("id")] = (float(n.get("lon")), float(n.get("lat")))
    for w in r.iter("way"):
        ways[w.get("id")] = ([nd.get("ref") for nd in w.iter("nd")], {t.get("k"): t.get("v") for t in w.iter("tag")})
    for rl in r.iter("relation"):
        if {t.get("k"): t.get("v") for t in rl.iter("tag")}.get("admin_level") == "2":
            members |= {m.get("ref") for m in rl.iter("member") if m.get("type") == "way"}
for k, (_, tags) in ways.items():
    if tags.get("admin_level") == "2" and tags.get("boundary") == "administrative":
        members.add(k)
out = [[nodes[n] for n in ways[k][0] if n in nodes] for k in sorted(members, key=int) if k in ways]
json.dump(out, open(D / "border_osm_mapbbox.json", "w"))
print("mapbbox:", len(out), "ways,", sum(map(len, out)), "points")

el = json.load(open(RAW / "osm" / "overpass_admin2.json"))["elements"]
out = [[[g["lon"], g["lat"]] for g in e["geometry"]] for e in el]
json.dump(out, open(D / "border_osm_overpass.json", "w"))
print("overpass:", len(out), "ways,", sum(map(len, out)), "points")
