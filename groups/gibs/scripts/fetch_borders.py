"""Fetch the border sources: OSM API map extracts, an Overpass query for the south map, Natural Earth 10m.

- OSM API 0.6 /map for four tiles over 118.85–119.90°E, 46.40–47.50°N -> raw/osm/map_<bbox>.osm
- Overpass: admin_level=2 boundary ways in 46.3–47.8°N, 118.5–120.5°E (with geometry)
  -> raw/overpass/border_admin2_south.json; this extract also covers the south-scar map east of 119.9°E
- Natural Earth ne_10m_admin_0_boundary_lines_land v5.1.0 -> raw/ne/
Existing files are kept.
"""

import io
import sys
import zipfile

import requests

from common import data

UA = {"User-Agent": "numrug-fire-2026/1.0"}
OSM_TILES = [
    "118.85,47.10,119.40,47.50",
    "118.90,46.60,119.40,47.10",
    "119.40,46.40,119.90,46.85",
    "119.40,46.85,119.90,47.35",
]
OVERPASS = "https://overpass-api.de/api/interpreter"
OVERPASS_Q = (
    '[out:json][timeout:120];way["admin_level"="2"]["boundary"="administrative"](46.3,118.5,47.8,120.5);out geom;'
)
NE_URL = "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_boundary_lines_land.zip"


def save(path, content: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    print(path.name, len(content))


def main():
    for bb in OSM_TILES:
        f = data("raw", "osm", f"map_{bb}.osm")
        if not f.exists():
            r = requests.get("https://api.openstreetmap.org/api/0.6/map", params={"bbox": bb}, headers=UA, timeout=300)
            r.raise_for_status()
            save(f, r.content)
    f = data("raw", "overpass", "border_admin2_south.json")
    if not f.exists():
        r = requests.post(OVERPASS, data={"data": OVERPASS_Q}, headers=UA, timeout=300)
        r.raise_for_status()
        save(f, r.content)
    shp = data("raw", "ne", "ne_10m_admin_0_boundary_lines_land.shp")
    if not shp.exists():
        r = requests.get(NE_URL, headers=UA, timeout=300)
        r.raise_for_status()
        zipfile.ZipFile(io.BytesIO(r.content)).extractall(shp.parent)
        print(shp.parent, "extracted")


if __name__ == "__main__":
    sys.exit(main())
