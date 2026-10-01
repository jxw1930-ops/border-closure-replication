import sys, numpy as np, pandas as pd
from pathlib import Path
D = Path(__file__).resolve().parent; O = D / "port_analysis"
a = sys.argv[1:]
IND = a[0] if a else "44-45"; BORDER = a[1] if len(a) > 1 else "ca"
NPERM = int(a[2]) if len(a) > 2 else 300
LAM = float(next((x.split("=")[1] for x in a if x.startswith("lam=")), 15))
rng = np.random.default_rng(0); out = []
def say(x=""): print(x); out.append(str(x))
BNAME = {"ca": "US-Canada Border", "mx": "US-Mexico Border"}[BORDER]

gd = pd.read_csv(O / "county_port_distance.csv", dtype={"area_fips": str})
p = pd.read_parquet(D / "panel_2015_2026" / "panel_sector.parquet",
                    columns=["area_fips", "industry_code", "year", "qtr", "emp_q"])
p["industry_code"] = p.industry_code.astype(str).str.strip()
p["area_fips"] = pd.to_numeric(p.area_fips).astype(int).astype(str).str.zfill(5)
gd["area_fips"] = pd.to_numeric(gd.area_fips).astype(int).astype(str).str.zfill(5)
R19 = p[(p.industry_code == "44-45") & (p.year == 2019)].groupby("area_fips").emp_q.mean()
p = p.merge(gd[["area_fips", "group"]], on="area_fips").dropna(subset=["group"])
p["per"] = p.year.astype(int).astype(str) + "Q" + p.qtr.astype(int).astype(str)
nq = p.per.nunique()
s = p[p.industry_code == IND].copy()
b = s[s.year == 2019][["area_fips", "qtr", "emp_q"]].rename(columns={"emp_q": "b19"})
s = s.merge(b, on=["area_fips", "qtr"]); s = s[(s.emp_q > 0) & (s.b19 > 0)]
s["y"] = 100 * (np.log(s.emp_q) - np.log(s.b19))
full = s.groupby("area_fips").per.nunique(); s = s[s.area_fips.isin(full[full == nq].index)]
s = s[s.group.isin([BORDER, "far"])].copy()
s["treat"] = (s.group == BORDER).astype(int)
s["state"] = s.area_fips.str[:2]
s = s[s.per != "2020Q1"]
if "noAK" in a: s = s[s.state != "02"]
s = s.reset_index(drop=True)

PEOPLE = ["Personal Vehicle Passengers", "Pedestrians", "Bus Passengers", "Train Passengers"]
bts = pd.read_csv(D / "bts_border_crossing.csv")
bts = bts[(bts.Border == BNAME) & bts.Latitude.notna() & (bts.Latitude != 0) & bts.Measure.isin(PEOPLE)].copy()
dt = pd.to_datetime(bts.Date, format="%b %Y")
bts["per"] = dt.dt.year.astype(str) + "Q" + ((dt.dt.month - 1) // 3 + 1).astype(str)
V = bts.groupby(["Port Code", "per"]).Value.sum().unstack(fill_value=0)
loc = bts.groupby("Port Code")[["Latitude", "Longitude"]].first().loc[V.index]
q19 = [f"2019Q{k}" for k in range(1, 5)]
keep = V[q19].sum(axis=1) > 0; V, loc = V[keep], loc[keep]

gz = pd.read_csv(D / "2020_Gaz_counties_national.txt", sep="\t", dtype={"GEOID": str})
gz.columns = [c.strip() for c in gz.columns]; gz["area_fips"] = gz.GEOID.str.zfill(5)
la1, lo1 = np.radians(gz.INTPTLAT.values)[:, None], np.radians(gz.INTPTLONG.values)[:, None]
la2, lo2 = np.radians(loc.Latitude.values)[None, :], np.radians(loc.Longitude.values)[None, :]
dist = 2 * 3958.8 * np.arcsin(np.sqrt(np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2))
Rc = gz.area_fips.map(R19).fillna(0).values
A = Rc[:, None] * np.exp(-dist / LAM) * (dist <= 75)
share = A / np.where(A.sum(0) > 0, A.sum(0), 1)[None, :]
F = pd.DataFrame(share @ V.values, index=gz.area_fips, columns=V.columns)
F19q = {k: F[f"2019Q{k}"] for k in range(1, 5)}
ann19 = F[q19].sum(axis=1)
expo = pd.Series(np.where(Rc > 0, ann19.values / np.where(Rc > 0, Rc, 1), 0), index=gz.area_fips)

cty = s.drop_duplicates("area_fips")[["area_fips", "state", "treat"]].reset_index(drop=True)
pers = sorted(s.per.unique())
Dm = np.zeros((len(cty), len(pers)))
for j, pr in enumerate(pers):
    if pr not in F.columns: continue
    q = int(pr[-1]); base = F19q[q].reindex(cty.area_fips).values
    cur = F[pr].reindex(cty.area_fips).values
    Dm[:, j] = np.where(base > 0, cur / np.where(base > 0, base, 1) - 1, 0)
Dm[cty.treat.values == 0, :] = 0
dose = np.log1p(expo.reindex(cty.area_fips).fillna(0).values)
sd = dose[cty.treat.values == 1].std(); dose = np.where(cty.treat.values == 1, dose / (sd if sd > 0 else 1), 0)

ci = pd.Series(range(len(cty)), index=cty.area_fips).reindex(s.area_fips).values
pi = pd.Series(range(len(pers)), index=pers).reindex(s.per).values
per = s.per.values
BIN = np.select([per < "2019Q1", per >= "2025Q1", per >= "2022Q2", per >= "2020Q2"], ["pre", "y25", "post", "restr"], "ref")
B = ["pre", "restr", "post", "y25"]
g = pd.factorize(s.state + "_" + s.per)[0]; gn = np.bincount(g)
def resid(M):
    M = np.asarray(M, float).copy()
    for j in range(M.shape[1]): M[:, j] -= (np.bincount(g, weights=M[:, j], minlength=len(gn)) / gn)[g]
    return M
yr = resid(s.y.values[:, None])[:, 0]
DET = "detrend" in a
tt = (s.year.values + (s.qtr.values - 1) / 4 - 2019)
ispre = np.isin(BIN, ["pre", "ref"])
gp = pd.factorize(pd.Series(g[ispre]))[0]; gpn = np.bincount(gp)
def resid_pre(v):
    v = np.asarray(v, float).copy()
    return v - (np.bincount(gp, weights=v, minlength=len(gpn)) / gpn)[gp]
ypre = resid_pre(s.y.values[ispre])
def est(P, use_dose):
    w = dose[P[ci]] if use_dose else cty.treat.values[P[ci]].astype(float)
    x = Dm[P[ci], pi] * (dose[P[ci]] if use_dose else 1.0)
    yy = yr
    if DET:
        Tp = resid_pre((tt * w)[ispre])
        c = (Tp @ ypre) / (Tp @ Tp) if (Tp @ Tp) > 0 else 0.0
        yy = resid((s.y.values - c * tt * w)[:, None])[:, 0]
    X = np.column_stack([x] + [x * (BIN == k) for k in B])
    b_all = np.linalg.lstsq(resid(X[:, :1]), yy, rcond=None)[0]
    b_per = np.linalg.lstsq(resid(X[:, 1:]), yy, rcond=None)[0]
    return np.r_[b_all, b_per]
st = cty.state.values
def perm():
    P = np.arange(len(cty))
    for u in np.unique(st):
        i = np.where(st == u)[0]; P[i] = rng.permutation(i)
    return P

say(f"{'DETRENDED ' if DET else ''}Industry {IND}, border {BORDER}, LAM={LAM}, perms={NPERM}, treated={int(cty.treat.sum())}, control={int((cty.treat==0).sum())}")
tr = cty.treat.values == 1
for k in B:
    m = np.isin(np.array(pers), np.unique(per[BIN == k]))
    say(f"  mean flow shortfall among treated, {k:5s}: {Dm[tr][:, m].mean():+.2f}")
lab = ["pooled"] + B
for use_dose, name in [(False, "shortfall x 1 (every treated county equally)"), (True, "shortfall x dose (1 SD of log(1+visitors/retail worker))")]:
    b0 = est(np.arange(len(cty)), use_dose)
    Pb = np.array([est(perm(), use_dose) for _ in range(NPERM)])
    pv = (np.abs(Pb) >= np.abs(b0)).mean(0)
    say(f"\n== {name} ==")
    say("  coefficient = change in employment (log points x100) per 100% change in visitor flow")
    for l, bb, pp in zip(lab, b0, pv):
        say(f"  {l:7s} beta={bb:+7.2f}  p_RI={pp:.3f}   -> a 50% shortfall implies {(-0.5*bb):+.2f}")
f = O / f"flow_{IND}_{BORDER}_lam{int(LAM)}{'_noAK' if 'noAK' in a else ''}{'_det' if DET else ''}.txt"
f.write_text("\n".join(out)); print(f"\nSaved to {f}")
