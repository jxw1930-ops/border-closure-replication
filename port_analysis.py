import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

D = Path(__file__).resolve().parent
OUT = D / "port_analysis"; OUT.mkdir(exist_ok=True)
CLOSE, REOPEN = pd.Timestamp("2020-03-21"), pd.Timestamp("2021-11-08")
NEAR, FAR = 50, 150
PEOPLE = ["Personal Vehicle Passengers", "Pedestrians", "Bus Passengers", "Train Passengers"]
SECTORS = {"44-45": "Retail Trade", "72": "Accommodation and Food Services",
           "31-33": "Manufacturing (comparison)"}
GROUPS = {"mx": f"Within {NEAR} mi of a US-Mexico land port",
          "ca": f"Within {NEAR} mi of a US-Canada land port",
          "far": f"More than {FAR} mi from any land port"}
COLORS = {"mx": "#c0392b", "ca": "#2471a3", "far": "#7f8c8d"}
log = []
def say(s): print(s); log.append(s)
def vlines(ax):
    ax.axvline(CLOSE, color="k", ls="--", lw=1); ax.axvline(REOPEN, color="k", ls=":", lw=1)

b = pd.read_csv(D / "bts_border_crossing.csv")
b["date"] = pd.to_datetime(b["Date"], format="%b %Y")
p19 = b[(b.date.dt.year == 2019) & b.Measure.isin(PEOPLE)].groupby("Port Code")["Value"].sum()
ports = (b[b.Latitude.notna() & (b.Latitude != 0)]
         .groupby(["Port Code", "Port Name", "State", "Border"], as_index=False)[["Latitude", "Longitude"]].first())
ports = ports[ports["Port Code"].isin(p19[p19 > 0].index)]
say(f"Land ports with passenger traffic in 2019: {len(ports)} "
    f"({(ports.Border=='US-Mexico Border').sum()} Mexico, {(ports.Border=='US-Canada Border').sum()} Canada)")
b["kind"] = np.where(b.Measure.isin(PEOPLE), "People", np.where(b.Measure.eq("Trucks"), "Trucks (exempt)", None))
fs = b[b.kind.notna() & (b.date >= "2015-01-01")].groupby(["Border", "kind", "date"], as_index=False)["Value"].sum()
base = fs[fs.date.dt.year == 2019].groupby(["Border", "kind"], as_index=False)["Value"].mean().rename(columns={"Value": "base"})
fs = fs.merge(base, on=["Border", "kind"]); fs["idx"] = fs.Value / fs.base * 100
fig, axes = plt.subplots(1, 2, figsize=(14, 4.5), sharey=True)
for ax, bd in zip(axes, ["US-Mexico Border", "US-Canada Border"]):
    for k, c in [("People", "#c0392b"), ("Trucks (exempt)", "#7f8c8d")]:
        s = fs[(fs.Border == bd) & (fs.kind == k)].sort_values("date")
        ax.plot(s.date, s.idx, color=c, label=k, lw=1.8)
    vlines(ax); ax.axhline(100, color="grey", lw=0.6)
    ax.set_title(f"{bd}: inbound crossings (2019 mean = 100)"); ax.grid(alpha=0.3); ax.legend()
plt.tight_layout(); plt.savefig(OUT / "fig1_first_stage_crossings.png", dpi=150); plt.close()

g = pd.read_csv(D / "2020_Gaz_counties_national.txt", sep="\t", dtype={"GEOID": str})
g.columns = [c.strip() for c in g.columns]
g["area_fips"] = g["GEOID"].str.zfill(5)
R = 3958.8
lat1, lon1 = np.radians(g.INTPTLAT.values)[:, None], np.radians(g.INTPTLONG.values)[:, None]
for key, bd in [("mx", "US-Mexico Border"), ("ca", "US-Canada Border")]:
    pp = ports[ports.Border == bd]
    lat2, lon2 = np.radians(pp.Latitude.values)[None, :], np.radians(pp.Longitude.values)[None, :]
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    g[f"dist_{key}"] = (2 * R * np.arcsin(np.sqrt(a))).min(axis=1)
g["dist_any"] = g[["dist_mx", "dist_ca"]].min(axis=1)
g["group"] = np.select([g.dist_mx <= NEAR, g.dist_ca <= NEAR, g.dist_any > FAR], ["mx", "ca", "far"], None)
g[["area_fips", "NAME", "USPS", "dist_mx", "dist_ca", "dist_any", "group"]].to_csv(OUT / "county_port_distance.csv", index=False)
say("\nCounty groups: " + ", ".join(f"{k}={int((g.group == k).sum())}" for k in GROUPS)
    + f", excluded (between {NEAR} and {FAR} mi)={int(g.group.isna().sum())}")
check = {"06073": "San Diego CA", "48141": "El Paso TX", "04019": "Pima AZ", "53073": "Whatcom WA",
         "36029": "Erie NY", "26163": "Wayne MI", "17031": "Cook IL", "39049": "Franklin OH"}
say("Sanity check (miles):")
for f, n in check.items():
    r = g[g.area_fips == f]
    if len(r):
        r = r.iloc[0]; say(f"  {n:14s} Mexico {r.dist_mx:7.1f}  Canada {r.dist_ca:7.1f}  group={r.group}")

p = pd.read_parquet(D / "panel_2015_2026" / "panel_sector.parquet",
                    columns=["area_fips", "industry_code", "year", "qtr", "emp_q", "suppressed"])
p["industry_code"] = p["industry_code"].astype(str).str.strip()
p = p.merge(g[["area_fips", "group"]], on="area_fips", how="inner")
p = p[p.group.notna()]
p["date"] = pd.to_datetime(dict(year=p.year.astype(int), month=p.qtr.astype(int) * 3 - 2, day=1))
nq = p.date.nunique()
fig, axes = plt.subplots(1, len(SECTORS), figsize=(18, 5))
for ax, (code, nm) in zip(axes, SECTORS.items()):
    s = p[p.industry_code == code].copy()
    say(f"\n{nm} ({code})  suppressed share: "
        + ", ".join(f"{k}={s[s.group==k].suppressed.mean():.0%}" for k in GROUPS))
    b19 = s[s.year == 2019][["area_fips", "qtr", "emp_q"]].rename(columns={"emp_q": "b19"})
    s = s.merge(b19, on=["area_fips", "qtr"], how="inner")
    s = s[(s.emp_q > 0) & (s.b19 > 0)]
    s["dev"] = np.log(s.emp_q) - np.log(s.b19)
    full = s.groupby("area_fips")["date"].nunique()
    s = s[s.area_fips.isin(full[full == nq].index)]
    say("  balanced counties: " + ", ".join(f"{k}={s[s.group==k].area_fips.nunique()}" for k in GROUPS))
    m = s.groupby(["group", "date"], as_index=False)["dev"].mean()
    for k, lab in GROUPS.items():
        mm = m[m.group == k].sort_values("date")
        if len(mm): ax.plot(mm.date, mm.dev * 100, color=COLORS[k], lw=1.8, label=lab)
    vlines(ax); ax.axhline(0, color="grey", lw=0.6)
    ax.set_title(nm); ax.set_ylabel("Log change vs same quarter of 2019 (x100)"); ax.grid(alpha=0.3)
axes[0].legend(fontsize=8, loc="lower left")
fig.suptitle("County employment relative to 2019, by distance to nearest land port\n"
             "dashed: restrictions begin (Mar 2020); dotted: reopening (Nov 2021)")
plt.tight_layout(); plt.savefig(OUT / "fig2_employment_by_port_distance.png", dpi=150); plt.close()
(OUT / "summary.txt").write_text("\n".join(log))
print(f"\nDone. See {OUT}")
