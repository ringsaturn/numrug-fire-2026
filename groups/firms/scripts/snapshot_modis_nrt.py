"""Writes snapshot/MODIS_C6_1_Global_7d_box.csv: the rows of the FIRMS MODIS C6.1 NRT global 7-day CSV
(downloaded 2026-10-18 from firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/) inside 44-50.5°N,
110-124°E. FIRMS no longer serves that file, so the subset ships with the repo; this script records how it was cut."""

import sys

import pandas as pd

from common import RAW, SNAPSHOT, WIDE_BOX, in_box

src = sys.argv[1] if len(sys.argv) > 1 else RAW / "MODIS_C6_1_Global_7d.csv"
m = pd.read_csv(src, dtype={"acq_time": str})
in_box(m, WIDE_BOX, strict=True).to_csv(SNAPSHOT / "MODIS_C6_1_Global_7d_box.csv", index=False)
