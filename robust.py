import sys, glob, numpy as np, pandas as pd
from pathlib import Path
D = Path(__file__).resolve().parent; O = D / "port_analysis"
IND = sys.argv[1] if len(sys.argv) > 1 else "44-45"
NPERM = int(sys.argv[2]) if len(sys.argv) > 2 else 300
NEAR = 50
rng = np.random.default_rng(0)
lines = []
def say(x=""): print(x); lines.append(str(x))

gd = pd.read_csv(O / "county_port_distance.csv", dtype={"area_fips": str})
p = pd.read_parquet(D / "panel_2015_2026" / "panel_sector.parquet",
                    columns=["area_fips", "industry_code", "year", "qtr", "emp_q"])
p["industry_code"] = p.industry_code.astype(str).str.strip()
p = p.merge(gd[["area_fips", "group"]], on="area_fips").dropna(subset=["group"])
p["per"] = p.year.astype(int).astype(str) + "Q" + p.qtr.astype(int).astype(str)
nq = p.per.nunique()
s = p[p.industry_code == IND].copy()
b = s[s.year == 2019][["area_fips", "qtr", "emp_q"]].rename(columns={"emp_q": "b19"})
s = s.merge(b, on=["area_fips", "qtr"]); s = s[(s.emp_q > 0) & (s.b19 > 0)]
s["y"] = 100 * (np.log(s.emp_q) - np.log(s.b19))
full = s.groupby("area_fips").per.nunique(); s = s[s.area_fips.isin(full[full == nq].index)]
s = s[s.group.isin(["ca", "far"])].copy()
s["treat"] = (s.group == "ca").astype(int)
s["area_fips"] = pd.to_numeric(s.area_fips).astype(int).astype(str).str.zfill(5)
s["state"] = s.area_fips.str[:2]
s = s[s.per != "2020Q1"].copy()
if "noAK" in sys.argv: s = s[s.state != "02"].copy(); say("Alaska excluded")

PEOPLE = ["Personal Vehicle Passengers", "Pedestrians", "Bus Passengers", "Train Passengers"]
bts = pd.read_csv(D / "bts_border_crossing.csv")
bts = bts[(bts.Border == "US-Canada Border") & bts.Latitude.notna() & (bts.Latitude != 0)]
bts["yr"] = pd.to_datetime(bts.Date, format="%b %Y").dt.year
pv = bts[(bts.yr == 2019) & bts.Measure.isin(PEOPLE)].groupby("Port Code").Value.sum()
ports = bts.groupby("Port Code")[["Latitude", "Longitude"]].first().join(pv.rename("v19"), how="inner")
ports = ports[ports.v19 > 0]
gz = pd.read_csv(D / "2020_Gaz_counties_national.txt", sep="\t", dtype={"GEOID": str})
gz.columns = [c.strip() for c in gz.columns]; gz["area_fips"] = gz.GEOID.str.zfill(5)
R = 3958.8
la1, lo1 = np.radians(gz.INTPTLAT.values)[:, None], np.radians(gz.INTPTLONG.values)[:, None]
la2, lo2 = np.radians(ports.Latitude.values)[None, :], np.radians(ports.Longitude.values)[None, :]
dist = 2 * R * np.arcsin(np.sqrt(np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2))
gz["cross19"] = ((dist <= NEAR) * ports.v19.values[None, :]).sum(axis=1)
pop = pd.read_csv(D / "county_pop_2019.csv", encoding="latin-1", dtype={"SUMLEV": str, "STATE": str, "COUNTY": str})
pop = pop[pop.SUMLEV.astype(int) == 50]
pop["area_fips"] = pop.STATE.str.zfill(2) + pop.COUNTY.str.zfill(3)
ex = gz[["area_fips", "cross19"]].merge(pop[["area_fips", "POPESTIMATE2019"]], on="area_fips", how="left")
LAM = float(next((a.split("=")[1] for a in sys.argv if a.startswith("lam=")), 15)); say(f"distance decay LAM = {LAM} mi")
r19 = pd.read_parquet(D / "panel_2015_2026" / "panel_sector.parquet", columns=["area_fips", "industry_code", "year", "emp_q"])
r19 = r19[(r19.industry_code.astype(str).str.strip() == "44-45") & (r19.year == 2019)].copy()
r19["area_fips"] = pd.to_numeric(r19.area_fips).astype(int).astype(str).str.zfill(5)
r19 = r19.groupby("area_fips").emp_q.mean()
Rc = gz.area_fips.map(r19).fillna(0).values
A = Rc[:, None] * np.exp(-dist / LAM) * (dist <= 75)
share = A / np.where(A.sum(0) > 0, A.sum(0), 1)[None, :]
ex = gz[["area_fips"]].copy(); ex["flow"] = share @ ports.v19.values; ex["R"] = Rc
ex["expo"] = np.where(ex.R > 0, ex.flow / np.where(ex.R > 0, ex.R, 1), np.nan)
s = s.merge(ex[["area_fips", "expo"]], on="area_fips", how="left")
s.loc[s.treat == 0, "expo"] = 0.0
miss = s[(s.treat == 1) & s.expo.isna()].area_fips.unique()
if len(miss): say(f"treated counties missing population, dropped: {list(miss)}")
s = s[s.expo.notna()].reset_index(drop=True)
_t = s[s.treat==1].drop_duplicates("area_fips").merge(gz[["area_fips","NAME","USPS"]], on="area_fips").sort_values("expo", ascending=False)
say("Top exposure treated counties:\n" + _t[["area_fips","NAME","USPS","expo"]].head(12).round(1).to_string(index=False))

rf = [f for f in glob.glob(str(D / "*")) if any(k in Path(f).name.lower() for k in ["rucc", "ruralurban", "rural_urban", "rural-urban", "continuum"])]
rucc = None
if rf:
    f = rf[0]
    r = pd.read_excel(f) if f.lower().endswith(("xls", "xlsx")) else pd.read_csv(f, encoding="latin-1")
    fc = [c for c in r.columns if "fips" in c.lower()][0]
    if "Attribute" in r.columns:
        r = r[r.Attribute.astype(str).str.upper().str.startswith("RUCC")].rename(columns={"Value": "rucc"})
    else:
        r = r.rename(columns={[c for c in r.columns if "rucc" in c.lower()][0]: "rucc"})
    r["area_fips"] = pd.to_numeric(r[fc], errors="coerce").dropna().astype(int).astype(str).str.zfill(5)
    rucc = r[["area_fips", "rucc"]].dropna().drop_duplicates("area_fips")
    say(f"RUCC file: {Path(f).name}, {len(rucc)} counties")
else:
    say("RUCC file not found in qcew_data; RUCC spec skipped")

def codes(a): return pd.factorize(pd.Series(a))[0]
def resid(M, groups, tol=1e-9, maxit=200):
    M = np.asarray(M, float).copy()
    cs = [(c, np.bincount(c)) for c in groups]
    for _ in range(maxit if len(cs) > 1 else 1):
        old = M.copy()
        for c, n in cs:
            for j in range(M.shape[1]):
                M[:, j] -= (np.bincount(c, weights=M[:, j], minlength=len(n)) / n)[c]
        if len(cs) == 1 or np.max(np.abs(M - old)) < tol: break
    return M

def run(name, d, groups, tr_col="treat", perm_within="state"):
    per = d.per.values; t = (d.year + (d.qtr - 1) / 4 - 2019).values
    binA = np.select([per < "2019Q1", per >= "2025Q1", per >= "2022Q2", per >= "2020Q2"],
                     ["pre", "y25", "post", "restr"], "ref")
    BA = ["pre", "restr", "post", "y25"]
    binV = np.select([per < "2018Q1", per >= "2024Q1", per >= "2022Q2", per >= "2020Q2"],
                     ["early", "late", "after", "restr"], "ref")
    BV = ["early", "restr", "after", "late"]
    m = {k: t[binV == k].mean() for k in ["ref", "restr", "after"]}
    w = (m["restr"] - m["ref"]) / (m["after"] - m["ref"])
    yr = resid(d.y.values[:, None], groups)[:, 0]
    def est(tr, bins, B):
        X = np.column_stack([(bins == k) * tr for k in B])
        return np.linalg.lstsq(resid(X, groups), yr, rcond=None)[0]
    cty = d.drop_duplicates("area_fips")[["area_fips", perm_within, tr_col]].set_index("area_fips")
    idx = d.area_fips.values
    def perm():
        v = cty.groupby(perm_within)[tr_col].transform(lambda x: rng.permutation(x.values))
        return v.reindex(idx).values
    tr0 = d[tr_col].values
    bA = est(tr0, binA, BA); bV = est(tr0, binV, BV); dip0 = bV[1] - w * bV[2]
    PA, PD = [], []
    for _ in range(NPERM):
        tp = perm(); PA.append(est(tp, binA, BA)); bv = est(tp, binV, BV); PD.append(bv[1] - w * bv[2])
    pA = (np.abs(np.array(PA)) >= np.abs(bA)).mean(0); pD = (np.abs(np.array(PD)) >= abs(dip0)).mean()
    nt = int((cty[tr_col] != 0).sum()); nc = len(cty) - nt
    say(f"\n== {name} ==  treated {nt}, control {nc}")
    say("  " + "  ".join(f"{k}={b_:+.2f}(p={p_:.2f})" for k, b_, p_ in zip(BA, bA, pA)))
    say(f"  V-test: restr={bV[1]:+.2f}, after={bV[2]:+.2f}, w={w:.3f}, dip={dip0:+.2f}, p_RI={pD:.3f}")

sq = lambda d: [codes(d.state + "_" + d.per)]
say(f"Industry {IND}, permutations {NPERM}, NEAR={NEAR} mi")
run("baseline: state x quarter FE", s, sq(s))
if rucc is not None:
    sr = s.merge(rucc, on="area_fips", how="inner")
    run("+ RUCC x quarter FE", sr, sq(sr) + [codes(sr.rucc.astype(str) + "_" + sr.per)])
for st, nm in [("36", "New York"), ("26", "Michigan"), ("53", "Washington"), ("02", "Alaska")]:
    d = s[s.state != st].reset_index(drop=True)
    run(f"drop {nm}", d, sq(d))
s["dose"] = np.log1p(s.expo)
sd = s.loc[s.treat == 1].drop_duplicates("area_fips").dose.std()
sd = sd if (sd == sd and sd > 0) else 1.0
s["dose"] = s.dose / sd
te = s[s.treat == 1].drop_duplicates("area_fips")
say(f"\nExposure among treated (2019 visitors per retail worker): median {te.expo.median():.1f}, max {te.expo.max():.1f}")
run("continuous dose (per 1 SD of log(1+visitors/retail worker))", s, sq(s), tr_col="dose")
med = te.expo.median()
for lab, cond in [("high exposure", s.expo > med), ("low exposure", (s.treat == 1) & (s.expo <= med))]:
    d = s[(s.treat == 0) | cond].reset_index(drop=True)
    run(f"treated = {lab} only", d, sq(d))
OUTF = O / f"robust_{IND}_lam{int(LAM)}{'_noAK' if 'noAK' in sys.argv else ''}.txt"; OUTF.write_text("\n".join(lines))
print(f"\nSaved to {OUTF}")
