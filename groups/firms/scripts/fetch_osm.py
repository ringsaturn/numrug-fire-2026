"""OpenStreetMap China-Mongolia border around the fire (ODbL).

- Four OSM API map tiles (118.85-119.90°E, 46.40-47.50°N), the source of the border on the FIRMS figures.
- One Overpass query for admin_level=2 ways in 46.3-47.8°N, 118.5-120.5°E, the border of the animation.

The border segment here was not edited between 2026-10-12 and 2026-10-19, so a fresh download reproduces it."""

import requests

from common import RAW

UA = {"User-Agent": "numrug-fire-2026/1.0"}
TILES = [
    "118.85,47.10,119.40,47.50",
    "118.90,46.60,119.40,47.10",
    "119.40,46.40,119.90,46.85",
    "119.40,46.85,119.90,47.35",
]
OVERPASS = '[out:json][timeout:60];way["boundary"="administrative"]["admin_level"="2"](46.3,118.5,47.8,120.5);out geom;'

d = RAW / "osm"
d.mkdir(parents=True, exist_ok=True)
for bb in TILES:
    f = d / f"map_{bb}.osm"
    if not f.exists():
        r = requests.get("https://api.openstreetmap.org/api/0.6/map", params={"bbox": bb}, headers=UA, timeout=120)
        r.raise_for_status()
        f.write_bytes(r.content)
    print(f.name, f.stat().st_size)
f = d / "overpass_admin2.json"
if not f.exists():
    r = requests.post("https://overpass-api.de/api/interpreter", data={"data": OVERPASS}, headers=UA, timeout=120)
    r.raise_for_status()
    f.write_bytes(r.content)
print(f.name, f.stat().st_size)
