"""Natural Earth 50 m coastline, country and province lines (GeoJSON) for the map backgrounds.

Pinned to natural-earth-vector commit ca96624a (v5.1.2 data); writes data/weather/base/.
"""

import sys
import urllib.request

from common import USER_AGENT, data

COMMIT = "ca96624a56bd078437bca8184e78163e5039ad19"
URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/{commit}/geojson/{name}.geojson"
NAMES = ["ne_50m_coastline", "ne_50m_admin_0_boundary_lines_land", "ne_50m_admin_1_states_provinces_lines"]

out = data("base")
out.mkdir(parents=True, exist_ok=True)
for name in NAMES:
    dest = out / f"{name}.geojson"
    if dest.exists() and dest.stat().st_size > 0:
        continue
    req = urllib.request.Request(URL.format(commit=COMMIT, name=name), headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as r:
        dest.write_bytes(r.read())
    print(dest, file=sys.stderr)
