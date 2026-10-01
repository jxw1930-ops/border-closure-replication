import zipfile
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
OUT_DIR = DATA_DIR / "panel_2015_2026"
YEARS = range(2015, 2027)
OWN_CODE = 5
LEVELS = {"supersector": 73, "sector": 74}
USECOLS = ["area_fips","own_code","industry_code","agglvl_code","year","qtr",
           "disclosure_code","qtrly_estabs","month1_emplvl","month2_emplvl",
           "month3_emplvl","total_qtrly_wages","avg_wkly_wage"]
DTYPES = {"area_fips": str, "industry_code": str, "disclosure_code": str}
NUM = ["qtrly_estabs","month1_emplvl","month2_emplvl","month3_emplvl",
       "total_qtrly_wages","avg_wkly_wage"]

def is_county(f):
    f = f.astype(str).str.strip()
    return (f.str.len()==5) & f.str.isdigit() & ~f.str.endswith("000") & ~f.str.endswith("999")

def read_year(y):
    zp = DATA_DIR / f"{y}_qtrly_singlefile.zip"
    if not zp.exists():
        print(f"  skip {y}: file not found"); return None
    parts = []
    with zipfile.ZipFile(zp) as z:
        name = [n for n in z.namelist() if n.endswith(".csv")][0]
        with z.open(name) as fh:
            for ch in pd.read_csv(fh, usecols=USECOLS, dtype=DTYPES,
                                  chunksize=1_000_000, low_memory=False):
                ch = ch[(ch["own_code"]==OWN_CODE) & ch["agglvl_code"].isin(LEVELS.values())]
                parts.append(ch[is_county(ch["area_fips"])])
    df = pd.concat(parts, ignore_index=True)
    df["disclosure_code"] = df["disclosure_code"].fillna("").astype(str).str.strip()
    for c in NUM:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
    df["suppressed"] = df["disclosure_code"].eq("N")
    df.loc[df["suppressed"], NUM] = float("nan")
    df["emp_q"] = df[["month1_emplvl","month2_emplvl","month3_emplvl"]].mean(axis=1)
    df["period"] = df["year"].astype(int).astype(str) + "Q" + df["qtr"].astype(int).astype(str)
    df["state_fips"] = df["area_fips"].str[:2]
    return df

OUT_DIR.mkdir(exist_ok=True)
frames, log = [], []
for y in YEARS:
    print(f"Processing {y} ...")
    df = read_year(y)
    if df is None:
        log.append(f"{y} MISSING"); continue
    frames.append(df)
    for nm, code in LEVELS.items():
        s = df[df["agglvl_code"]==code]
        line = (f"{y} {nm:12s} rows={len(s):>9,} "
                f"quarters={sorted(s['qtr'].astype(int).unique().tolist())} "
                f"suppressed={s['suppressed'].mean():.1%}")
        log.append(line); print("  " + line)

full = pd.concat(frames, ignore_index=True)
log.append("duplicate key rows: " + str(full.duplicated(
    ["area_fips","industry_code","agglvl_code","year","qtr"]).sum()))
for nm, code in LEVELS.items():
    out = full[full["agglvl_code"]==code].sort_values(
        ["area_fips","industry_code","year","qtr"]).reset_index(drop=True)
    out.to_parquet(OUT_DIR / f"panel_{nm}.parquet", index=False)
    out.to_csv(OUT_DIR / f"panel_{nm}.csv", index=False)
    log.append(f"wrote panel_{nm}: {len(out):,} rows, "
               f"{out['area_fips'].nunique():,} counties, "
               f"{out['industry_code'].nunique()} industries, "
               f"{out['period'].min()} to {out['period'].max()}")
(OUT_DIR / "build_log.txt").write_text("\n".join(log))
print("\n".join(log[-3:]))
print("Done:", OUT_DIR)
