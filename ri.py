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

s = s[s.per != "2020Q1"].copy()
g = (s.state + "_" + s.per).values
pp = s.per
bin_ = np.select([pp < "2019Q1", pp >= "2025Q1", pp >= "2022Q2", pp >= "2020Q2"],
                 ["pre", "y25", "post", "restr"], "ref")
B = ["pre", "restr", "post", "y25"]
tt = (s.year + (s.qtr - 1) / 4 - 2019).values
y = s.y.values
ispre = np.isin(bin_, ["pre", "ref"])

def fe_resid(M, gg):
    return M - pd.DataFrame(M).groupby(gg).transform("mean").values

def est(tr, detrend):
    yy = y.copy()
    if detrend:  # 只用 2015–2019 估计处理组的线性趋势，再外推扣除
        x = fe_resid((tr * tt)[ispre][:, None], g[ispre])
        yr = fe_resid(y[ispre][:, None], g[ispre])
        yy = y - np.linalg.lstsq(x, yr[:, 0], rcond=None)[0][0] * tt * tr
    X = np.column_stack([(bin_ == b) * tr for b in B]).astype(float)
    return np.linalg.lstsq(fe_resid(X, g), fe_resid(yy[:, None], g)[:, 0], rcond=None)[0]

cty = s.drop_duplicates("area_fips")[["area_fips", "state", "treat"]]
rng = np.random.default_rng(0)
def perm():  # 州内置换处理标签
    c = cty.copy()
    c["treat"] = c.groupby("state").treat.transform(lambda v: rng.permutation(v.values))
    return s.area_fips.map(c.set_index("area_fips").treat).values

for d in [False, True]:
    b0 = est(s.treat.values, d)
    P = np.array([est(perm(), d) for _ in range(500)])
    p = (np.abs(P) >= np.abs(b0)).mean(0)
    print("\n" + ("去趋势" if d else "不去趋势"))
    print(pd.DataFrame({"b": b0, "p_RI": p}, index=B).round(3).to_string())

# V 形检验：以 2018–2019 为基准，dip = restr − after/2，对线性趋势稳健
pp = s.per
bin_ = np.select([pp < "2018Q1", pp >= "2024Q1", pp >= "2022Q2", pp >= "2020Q2"],
                 ["early", "late", "after", "restr"], "ref")
B = ["early", "restr", "after", "late"]
dip = lambda b: b[1] - b[2] / 2
b0 = est(s.treat.values, False)
dP = np.array([dip(est(perm(), False)) for _ in range(1000)])
print("\nV形检验:", dict(zip(B, b0.round(2))))
print(f"dip = {dip(b0):.2f}, p_RI = {(np.abs(dP) >= abs(dip(b0))).mean():.3f}")
