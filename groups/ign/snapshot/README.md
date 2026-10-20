# snapshot/

- `border_osm.json` (28 KB): China–Mongolia border near the fire as lists of [lon, lat]. © OpenStreetMap contributors,
  ODbL 1.0. From an Overpass query for `admin_level=2` ways in 46.3–47.8°N, 118.5–120.5°E (11 ways, 2026-10), minus the
  one way lying wholly west of 118.9°E and south of 46.7°N, which the published figures did not have. Shipped because
  OSM changes over time.
- `pm25_published_missing.json` (1 KB): the 16 hours (10-13 18:00 … 10-14 09:00 UTC+8) that the quotsoft mirror lacked
  for Hulunbuir and Baicheng when the published Chinese air-quality figure was fetched (10-14 16:38 UTC+8). Found by
  matching masked renders against the published image. Used only where a catalog sets `mirror_as_published = true`.
