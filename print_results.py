import numpy as np, pandas as pd
from pathlib import Path
D = Path(__file__).resolve().parent; O = D / "port_analysis"
g = pd.read_csv(O / "county_port_distance.csv", dtype={"area_fips": str})
p = pd.read_parquet(D / "panel_2015_2026" / "panel_sector.parquet",
                    columns=["area_fips", "industry_code", "year", "qtr", "emp_q"])
p["industry_code"] = p.industry_code.astype(str).str.strip()
p = p.merge(g[["area_fips", "group"]], on="area_fips").dropna(subset=["group"])
p["per"] = p.year.astype(int).astype(str) + "Q" + p.qtr.astype(int).astype(str)
nq = p.per.nunique()
show = ["2017Q2","2018Q2","2019Q2","2020Q2","2020Q4","2021Q2","2021Q4","2022Q2","2022Q4","2023Q4","2024Q4","2025Q4"]
for code, nm in [("44-45","Retail"), ("72","Accommodation and Food"), ("31-33","Manufacturing")]:
    s = p[p.industry_code == code]
    b = s[s.year == 2019][["area_fips","qtr","emp_q"]].rename(columns={"emp_q":"b19"})
    s = s.merge(b, on=["area_fips","qtr"]); s = s[(s.emp_q > 0) & (s.b19 > 0)]
    s["dev"] = 100 * (np.log(s.emp_q) - np.log(s.b19))
    full = s.groupby("area_fips").per.nunique(); s = s[s.area_fips.isin(full[full == nq].index)]
    t = s.groupby(["per","group"]).dev.mean().unstack()[["mx","ca","far"]]
    t["mx-far"] = t.mx - t.far; t["ca-far"] = t.ca - t.far
    print(f"\n{nm}: log change vs same quarter of 2019 (x100)")
    print(t.loc[[x for x in show if x in t.index]].round(1).to_string())
bts = pd.read_csv(D / "bts_border_crossing.csv"); bts["date"] = pd.to_datetime(bts.Date, format="%b %Y")
P = ["Personal Vehicle Passengers","Pedestrians","Bus Passengers","Train Passengers"]
x = bts[bts.Measure.isin(P)].groupby(["Border","date"]).Value.sum().unstack(0)
x = 100 * x / x[x.index.year == 2019].mean()
print("\nInbound people crossings (2019 mean = 100)")
print(x.loc[pd.to_datetime(["2019-12-01","2020-04-01","2020-12-01","2021-06-01","2021-10-01",
                            "2021-12-01","2022-06-01","2023-06-01","2025-06-01"])].round(0).to_string())
