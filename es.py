import numpy as np, pandas as pd
from pathlib import Path
D = Path(__file__).resolve().parent; O = D / "port_analysis"
g = pd.read_csv(O / "county_port_distance.csv", dtype={"area_fips": str})
p = pd.read_parquet(D / "panel_2015_2026" / "panel_sector.parquet",
                    columns=["area_fips", "industry_code", "year", "qtr", "emp_q"])
p["industry_code"] = p.industry_code.astype(str).str.strip()
p = p.merge(g[["area_fips", "group"]], on="area_fips").dropna(subset=["group"])
p["per"] = p.year.astype(int).astype(str) + "Q" + p.qtr.astype(int).astype(str)

import numpy as np, pandas as pd
nq = p.per.nunique()
s = p[p.industry_code == __import__("sys").argv[1]].copy()
b = s[s.year == 2019][["area_fips","qtr","emp_q"]].rename(columns={"emp_q":"b19"})
s = s.merge(b, on=["area_fips","qtr"]); s = s[(s.emp_q > 0) & (s.b19 > 0)]
s["y"] = 100 * (np.log(s.emp_q) - np.log(s.b19))
full = s.groupby("area_fips").per.nunique(); s = s[s.area_fips.isin(full[full == nq].index)]
s = s[s.group.isin(["ca","far"])].copy()
s["treat"] = (s.group == "ca").astype(int)
s["state"] = pd.to_numeric(s.area_fips).astype(int).astype(str).str.zfill(5).str[:2]

c = s.drop_duplicates("area_fips")
sup = c.groupby("state").treat.agg(n_treat="sum", n="size"); sup["n_ctrl"] = sup.n - sup.n_treat
print(sup[sup.n_treat > 0].sort_values("n_treat", ascending=False).to_string())
ok = sup[(sup.n_treat > 0) & (sup.n_ctrl > 0)].n_treat.sum()
print(f"\n有同州对照的处理县: {ok} / {sup.n_treat.sum()}\n")

s["evt"] = s.per.where(s.year != 2019, "ref")

def es(s, g):
    g = g.values
    pers = sorted(x for x in s.evt.unique() if x != "ref")
    X = np.column_stack([((s.evt == k) & (s.treat == 1)).values.astype(float) for k in pers])
    Xd = X - pd.DataFrame(X).groupby(g).transform("mean").values
    yd = s.y.values - pd.Series(s.y.values).groupby(g).transform("mean").values
    bb = np.linalg.lstsq(Xd, yd, rcond=None)[0]
    e = yd - Xd @ bb
    A = np.linalg.pinv(Xd.T @ Xd)
    cl = s.state.values; M = np.zeros((len(pers), len(pers)))
    for k in np.unique(cl):
        u = Xd[cl == k].T @ e[cl == k]; M += np.outer(u, u)
    G = len(np.unique(cl))
    V = A @ M @ A * G / (G - 1)
    return pd.DataFrame({"b": bb, "se": np.sqrt(np.diag(V))}, index=pers)

r0 = es(s, s.per)                    # m0: 季度固定效应
r1 = es(s, s.state + "_" + s.per)    # m1: 州×季度固定效应
out = pd.concat([r0.add_suffix("0"), r1.add_suffix("1")], axis=1)
k = ["2015Q2","2016Q2","2017Q2","2018Q2","2020Q2","2020Q4","2021Q2","2021Q4",
     "2022Q2","2022Q4","2023Q4","2024Q4","2025Q4"]
print(out.loc[[x for x in k if x in out.index]].round(1).to_string())
print("\n全部季度:"); print(out.round(1).to_string())
