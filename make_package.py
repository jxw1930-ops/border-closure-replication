import os, shutil, subprocess, sys, zipfile
from pathlib import Path
D = Path(__file__).resolve().parent
P = D / "replication_border_closure"
R = D / "port_analysis"
RUNS = [
    ("robust_44-45_lam15_noAK.txt", "robust.py 44-45 300 noAK"),
    ("robust_44-45_lam15.txt",      "robust.py 44-45 300"),
    ("robust_44-45_lam10_noAK.txt", "robust.py 44-45 300 noAK lam=10"),
    ("robust_44-45_lam25_noAK.txt", "robust.py 44-45 300 noAK lam=25"),
    ("robust_31-33_lam15_noAK.txt", "robust.py 31-33 300 noAK"),
    ("robust_72_lam15_noAK.txt",    "robust.py 72 300 noAK"),
    ("flow_44-45_ca_lam15_noAK.txt",     "flow.py 44-45 ca 300 noAK"),
    ("flow_72_ca_lam15_noAK.txt",        "flow.py 72 ca 300 noAK"),
    ("flow_31-33_ca_lam15_noAK.txt",     "flow.py 31-33 ca 300 noAK"),
    ("flow_44-45_mx_lam15.txt",          "flow.py 44-45 mx 300"),
    ("flow_72_mx_lam15.txt",             "flow.py 72 mx 300"),
    ("flow_44-45_ca_lam15_noAK_det.txt", "flow.py 44-45 ca 300 noAK detrend"),
    ("flow_72_ca_lam15_noAK_det.txt",    "flow.py 72 ca 300 noAK detrend"),
    ("flow_31-33_ca_lam15_noAK_det.txt", "flow.py 31-33 ca 300 noAK detrend"),
    ("flow_44-45_mx_lam15_det.txt",      "flow.py 44-45 mx 300 detrend"),
    ("ci_44-45_ca_noAK_det.txt", "ci.py 44-45 ca 200 noAK detrend"),
    ("ci_44-45_ca_noAK.txt",     "ci.py 44-45 ca 200 noAK"),
    ("ci_72_ca_noAK_det.txt",    "ci.py 72 ca 200 noAK detrend"),
    ("ci_44-45_mx_det.txt",      "ci.py 44-45 mx 200 detrend"),
    ("fig1_first_stage.png",     "make_fig1.py"),
]
missing = [(f, c) for f, c in RUNS if not (R / f).exists()]
if missing:
    print(f"{len(missing)} result files missing; regenerating:")
    for f, c in missing:
        print("  running", c)
        if subprocess.run([sys.executable] + c.split(), cwd=D, stdout=subprocess.DEVNULL).returncode:
            print("    FAILED:", c)
(D / "logs").mkdir(exist_ok=True)
with open(D / "logs" / "print_results.txt", "w") as fh:
    rc = subprocess.run([sys.executable, "print_results.py"], cwd=D, stdout=fh, stderr=subprocess.STDOUT).returncode
if rc: print("  WARNING: print_results.py failed; see logs/print_results.txt")
CHECKS = [
    ("summary.txt", "mx=24, ca=75, far=2791", "Sec 4.1 county groups"),
    ("robust_44-45_lam15_noAK.txt", "restr=-2.19", "Table 2 baseline, restriction"),
    ("robust_44-45_lam15_noAK.txt", "dip=-1.04", "Table 2 baseline, contrast"),
    ("robust_44-45_lam15_noAK.txt", "dip=-0.37", "Table 2 continuous dose"),
    ("robust_44-45_lam15_noAK.txt", "dip=-1.95", "Table 2 high exposure"),
    ("robust_44-45_lam15_noAK.txt", "median 167.8, max 1444.6", "Sec 4.2 exposure"),
    ("robust_44-45_lam15.txt", "dip=-2.67", "Table 2 memo row, Alaska included"),
    ("robust_44-45_lam10_noAK.txt", "dip=-0.44", "Table 4, lambda 10"),
    ("robust_44-45_lam25_noAK.txt", "dip=-0.32", "Table 4, lambda 25"),
    ("ci_44-45_ca_noAK.txt", "beta = +2.66", "Table 3 row 1"),
    ("ci_44-45_ca_noAK.txt", "[-4.30, -0.39]", "Table 3 row 1, implied CI"),
    ("ci_44-45_ca_noAK_det.txt", "beta = +0.85", "Table 3 row 2"),
    ("ci_44-45_ca_noAK_det.txt", "[-3.95, +2.05]", "Table 3 row 2, implied CI"),
    ("ci_72_ca_noAK_det.txt", "beta = -1.49", "Table 3 row 5"),
    ("ci_44-45_mx_det.txt", "beta = +7.45", "Table 3 row 7"),
    ("flow_31-33_ca_lam15_noAK.txt", "beta=  +1.19", "Sec 7.4 manufacturing placebo"),
    ("flow_44-45_ca_lam15_noAK.txt", "restr: -0.88", "Sec 5 mean shortfall, Canada"),
    ("flow_44-45_mx_lam15.txt", "restr: -0.41", "Sec 5 mean shortfall, Mexico"),
]
bad = 0; rows = []
for f, pat, where in CHECKS:
    txt = (R / f).read_text() if (R / f).exists() else ""
    ok = pat in txt; bad += not ok
    rows.append(f"| {where} | `{f}` | `{pat}` | {'OK' if ok else 'MISMATCH'} |")
    print(("  OK       " if ok else "  MISMATCH ") + f"{where}: {pat}")
print(f"\n{len(CHECKS) - bad}/{len(CHECKS)} headline numbers match the paper")
if P.exists(): shutil.rmtree(P)
(P / "port_analysis").mkdir(parents=True); (P / "logs").mkdir(); (P / "exploratory").mkdir()
MAIN = ["build_qcew_panel_2015_2026.py", "port_analysis.py", "print_results.py", "make_fig1.py",
        "robust.py", "flow.py", "ci.py", "make_package.py"]
for f in MAIN:
    if (D / f).exists(): shutil.copy2(D / f, P / f)
for f in ["es.py", "ri.py"]:
    if (D / f).exists(): shutil.copy2(D / f, P / "exploratory" / f)
for f in ["bts_border_crossing.csv", "2020_Gaz_counties_national.txt", "county_pop_2019.csv", "Ruralurbancontinuumcodes2023.csv"]:
    if (D / f).exists(): shutil.copy2(D / f, P / f)
for f in R.iterdir():
    if f.suffix in (".txt", ".csv", ".png", ".pdf"): shutil.copy2(f, P / "port_analysis" / f.name)
shutil.copy2(D / "logs" / "print_results.txt", P / "logs" / "print_results.txt")
(P / "requirements.txt").write_text("python>=3.9\npandas\nnumpy\npyarrow\nmatplotlib\nxlrd\nopenpyxl\n")
(P / "run_all.sh").write_text("#!/bin/bash\nset -e\nmkdir -p logs\npython3 build_qcew_panel_2015_2026.py\npython3 port_analysis.py\npython3 print_results.py > logs/print_results.txt\npython3 make_fig1.py\n" + "".join(f"python3 {c}\n" for f, c in RUNS if c.startswith(("robust", "flow", "ci"))) + "python3 make_package.py\n")
(P / "get_data.sh").write_text('#!/bin/bash\nset -e\nUA="Mozilla/5.0 (research use)"\nfor y in $(seq 2015 2026); do\n  [ -f ${y}_qtrly_singlefile.zip ] || curl -L -A "$UA" -o ${y}_qtrly_singlefile.zip "https://data.bls.gov/cew/data/files/${y}/csv/${y}_qtrly_singlefile.zip"\ndone\n')
(P / "MANIFEST.md").write_text("# Manifest: where each number in the paper comes from\n\n"
 "Each row gives the location in the paper, the results file in port_analysis/, and the exact string in that file.\n\n"
 "| Location in paper | File | String | Status |\n|---|---|---|---|\n" + "\n".join(rows) + "\n\n"
 "Table 1 (monthly crossing index) is in logs/print_results.txt, block \"Inbound people crossings\".\n"
 "Section 3.4 figures on the 100-mile border zone come from a distance layer built for a separate project and are not included.\n"
 "Figure 1 is port_analysis/fig1_first_stage.png (vector version .pdf), produced by make_fig1.py.\n")
(P / "README.md").write_text("# Replication package\n"
 "**Closing the Land Border: Cross-Border Visitor Flows and Local Employment in U.S. Border Counties, 2020-2025**\n"
 "Junyang Wang (jxw1930@case.edu)\n\n"
 "## Code\n"
 "build_qcew_panel_2015_2026.py builds the county x sector QCEW panels, 2015Q1-2026Q1 (private ownership, suppressed cells set to missing).\n"
 "port_analysis.py computes distance from each county to the nearest land port and defines treatment and comparison groups.\n"
 "print_results.py reports raw group means and the monthly crossing index (Table 1).\n"
 "make_fig1.py produces Figure 1.\n"
 "robust.py estimates the binned event study, the trend-robust contrast, state exclusions, RUCC fixed effects, and dose and exposure-split specifications (Tables 2 and 4).\n"
 "flow.py estimates the flow-intensity design with and without treated-group linear trends (Section 7).\n"
 "ci.py computes randomization confidence intervals by test inversion (Table 3).\n"
 "make_package.py assembles this package and checks headline numbers against the paper.\n"
 "exploratory/ holds earlier event-study scripts (es.py, ri.py), steps 3-4 of the specification log, superseded by robust.py.\n\n"
 "## Data\n"
 "All inputs are public U.S. government data. QCEW quarterly single files 2015-2026 are not included (about 3.6 GB); get_data.sh downloads them from bls.gov/cew/downloadable-data-files.htm. Included: BTS Border Crossing Entry Data (data.transportation.gov, dataset keg4-3bc2), Census 2020 Gazetteer county file, Census county population estimates 2010-2019, USDA ERS Rural-Urban Continuum Codes 2023.\n\n"
 "## Reproducing\n"
 "pip3 install -r requirements.txt, then ./get_data.sh, then ./run_all.sh. All scripts expect inputs in the same folder and write to port_analysis/. Randomization inference uses fixed seeds, so estimates, p-values, and confidence intervals reproduce exactly. A full run takes one to two hours, most of it in ci.py.\n\n"
 "## Notes\n"
 "Alaska is excluded from the main sample (noAK); estimates including it come from the runs without noAK. Appendix A of the paper lists every specification in the order it was estimated. An initial version of the analysis used a border-proximity layer built for a separate project; it is not included, and no result in the paper depends on it.\n\n"
 "## License\nCode and derived files: CC0 1.0. Source data are public-domain government data.\n")
zp = D / "replication_border_closure.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for f in P.rglob("*"):
        if f.is_file(): z.write(f, f.relative_to(P.parent))
print(f"\nPackage: {P}\nZip:     {zp}  ({zp.stat().st_size / 1e6:.1f} MB)")
if bad: print(f"\nWARNING: {bad} headline number(s) did not match. Send me the MISMATCH lines before uploading.")
