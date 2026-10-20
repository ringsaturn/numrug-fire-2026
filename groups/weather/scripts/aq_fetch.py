"""Hourly air quality at every Chinese national monitoring site, 10-07..10-14 (Beijing time):
the quotsoft.net daily CSVs of the China National Environmental Monitoring Centre release.

Writes data/weather/aq/china_sites_YYYYMMDD.csv (about 12 MB).
"""

import sys
import urllib.request
from datetime import date, timedelta

from common import USER_AGENT, data

URL = "https://quotsoft.net/air/data/china_sites_{d:%Y%m%d}.csv"
FIRST, LAST = date(2026, 10, 7), date(2026, 10, 14)

out = data("aq")
out.mkdir(parents=True, exist_ok=True)
d = FIRST
while d <= LAST:
    dest = out / f"china_sites_{d:%Y%m%d}.csv"
    if not dest.exists():
        req = urllib.request.Request(URL.format(d=d), headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=120) as r:
            dest.write_bytes(r.read())
        print(dest, file=sys.stderr)
    d += timedelta(days=1)
