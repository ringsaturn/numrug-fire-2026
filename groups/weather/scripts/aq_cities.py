"""City-mean hourly PM2.5, PM10 and CO for the seven cities around the fire.

Reads data/weather/aq/china_sites_*.csv and the site list snapshot/stations.csv; writes
data/weather/aq/city_hourly.csv (time_bjt, city, n_sites, pm25, pm10, co, time_utc).
A city value is the mean of its sites that report that hour, control sites included,
because the city mean is what is quoted; sites marked 停运 (closed) are left out.
"""

from pathlib import Path

import pandas as pd

from common import data

CITIES = {
    "呼伦贝尔": "Hailar",
    "白城": "Baicheng",
    "兴安盟": "Ulanhot",
    "齐齐哈尔": "Qiqihar",
    "通辽": "Tongliao",
    "松原": "Songyuan",
    "锡林郭勒盟": "Xilinhot",
}
AQ = data("aq")

st = pd.read_csv(Path("snapshot/stations.csv"))
st = st[st["城市"].isin(CITIES) & ~st["监测点名称"].str.contains("停运")]
codes = dict(zip(st["监测点编码"], st["城市"]))

rows = []
for f in sorted(AQ.glob("china_sites_*.csv")):
    df = pd.read_csv(f)
    df = df[df["type"].isin(["PM2.5", "PM10", "CO"])]
    keep = [c for c in df.columns if c in codes]
    rows.append(df.melt(id_vars=["date", "hour", "type"], value_vars=keep, var_name="site").dropna(subset=["value"]))
obs = pd.concat(rows)
obs["city"] = obs["site"].map(codes).map(CITIES)
obs["time_bjt"] = pd.to_datetime(obs["date"].astype(str)) + pd.to_timedelta(obs["hour"], unit="h")
wide = obs.pivot_table(index=["time_bjt", "city", "site"], columns="type", values="value").reset_index()
city = (
    wide.groupby(["time_bjt", "city"])
    .agg(n_sites=("site", "nunique"), pm25=("PM2.5", "mean"), pm10=("PM10", "mean"), co=("CO", "mean"))
    .reset_index()
)
city["time_utc"] = city["time_bjt"] - pd.Timedelta(hours=8)
city.to_csv(AQ / "city_hourly.csv", index=False, float_format="%.2f")
print(AQ / "city_hourly.csv", len(city), "rows")
