"""Turn the raw border downloads into line lists ([[lon, lat], ...] per way) under data/gibs/border/.

- border_osm.json: admin_level=2 ways (and members of admin_level=2 relations) in the OSM API extracts
- border_osm_south.json: the ways of the Overpass extract
- border_ne.json: every part of the Natural Earth boundary lines whose bounding box touches 105–130°E, 40–55°N
"""

import glob
import json
import xml.etree.ElementTree as ET

import shapefile

from common import data


def osm_api():
    nodes, ways, rel_members = {}, {}, set()
    for f in sorted(glob.glob(str(data("raw", "osm", "map_*.osm")))):
        r = ET.parse(f).getroot()
        for n in r.iter("node"):
            nodes[n.get("id")] = (float(n.get("lon")), float(n.get("lat")))
        for w in r.iter("way"):
            tags = {t.get("k"): t.get("v") for t in w.iter("tag")}
            ways[w.get("id")] = ([nd.get("ref") for nd in w.iter("nd")], tags)
        for rl in r.iter("relation"):
            tags = {t.get("k"): t.get("v") for t in rl.iter("tag")}
            if tags.get("admin_level") == "2":
                rel_members |= {m.get("ref") for m in rl.iter("member") if m.get("type") == "way"}
    keep = set(rel_members)
    keep |= {k for k, (_, t) in ways.items() if t.get("admin_level") == "2" and t.get("boundary") == "administrative"}
    out = []
    for k in sorted(keep, key=int):
        if k in ways:
            out.append([nodes[n] for n in ways[k][0] if n in nodes])
    return out


def overpass():
    d = json.load(open(data("raw", "overpass", "border_admin2_south.json")))
    return [[[g["lon"], g["lat"]] for g in e["geometry"]] for e in d["elements"] if e["type"] == "way"]


def natural_earth(box=(105, 40, 130, 55)):
    r = shapefile.Reader(str(data("raw", "ne", "ne_10m_admin_0_boundary_lines_land.shp")))
    out = []
    for s in r.shapes():
        x0, y0, x1, y1 = s.bbox
        if x1 < box[0] or x0 > box[2] or y1 < box[1] or y0 > box[3]:
            continue
        parts = list(s.parts) + [len(s.points)]
        out += [[list(p) for p in s.points[a:b]] for a, b in zip(parts[:-1], parts[1:])]
    return out


def main():
    data("border").mkdir(parents=True, exist_ok=True)
    for name, segs in (
        ("border_osm.json", osm_api()),
        ("border_osm_south.json", overpass()),
        ("border_ne.json", natural_earth()),
    ):
        json.dump(segs, open(data("border", name), "w"))
        print(name, len(segs), "lines,", sum(map(len, segs)), "points")


if __name__ == "__main__":
    main()
