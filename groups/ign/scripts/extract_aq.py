"""Hourly PM2.5 / PM10 / CO for selected cities and sites out of the quotsoft daily CSVs -> data/ign/aq_hourly_long.csv.
Times in the source are UTC+8; hour h is the hour-ending value. City and site names are the source's column headers."""

import csv
import glob

from common import data

CITIES = ["兴安盟", "锡林郭勒盟", "呼伦贝尔", "通辽", "白城", "齐齐哈尔", "赤峰"]
SITES = {
    "2200A": "兴安盟-胜华新制药厂(乌兰浩特)",
    "3035A": "兴安盟-北滨河(乌兰浩特)",
    "2201A": "兴安盟-科右前旗环保局",
    "2202A": "锡林郭勒盟-市环保监测站(锡林浩特)",
    "2203A": "锡林郭勒盟-市政府(锡林浩特)",
    "2192A": "呼伦贝尔-区环保局(海拉尔)",
    "2193A": "呼伦贝尔-市艺校(海拉尔)",
    "3061A": "呼伦贝尔-国华电力东(海拉尔)",
}
TYPES = {"PM2.5", "PM10", "CO"}


def rows(path, keys):
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        r = csv.reader(fh)
        head = next(r)
        idx = {k: head.index(k) for k in keys if k in head}
        for line in r:
            if len(line) < 3 or line[2] not in TYPES:
                continue
            for k, i in idx.items():
                v = line[i] if i < len(line) else ""
                yield line[0], int(line[1]), line[2], k, v


recs = []
for p in sorted(glob.glob(str(data("quotsoft", "china_cities_*.csv")))):
    recs += [(*x, "city") for x in rows(p, CITIES)]
for p in sorted(glob.glob(str(data("quotsoft", "china_sites_*.csv")))):
    recs += [(d, h, t, f"{k} {SITES[k]}", v, "site") for d, h, t, k, v in rows(p, list(SITES))]
with open(data("aq_hourly_long.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["date_bjt", "hour_bjt", "type", "where", "value", "level"])
    w.writerows(recs)
print(len(recs), "rows")
