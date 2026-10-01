# Replication package
**Closing the Land Border: Cross-Border Visitor Flows and Local Employment in U.S. Border Counties, 2020-2025**
Junyang Wang (jxw1930@case.edu)

## Code
build_qcew_panel_2015_2026.py builds the county x sector QCEW panels, 2015Q1-2026Q1 (private ownership, suppressed cells set to missing).
port_analysis.py computes distance from each county to the nearest land port and defines treatment and comparison groups.
print_results.py reports raw group means and the monthly crossing index (Table 1).
make_fig1.py produces Figure 1.
robust.py estimates the binned event study, the trend-robust contrast, state exclusions, RUCC fixed effects, and dose and exposure-split specifications (Tables 2 and 4).
flow.py estimates the flow-intensity design with and without treated-group linear trends (Section 7).
ci.py computes randomization confidence intervals by test inversion (Table 3).
make_package.py assembles this package and checks headline numbers against the paper.
exploratory/ holds earlier event-study scripts (es.py, ri.py), steps 3-4 of the specification log, superseded by robust.py.

## Data
All inputs are public U.S. government data. QCEW quarterly single files 2015-2026 are not included (about 3.6 GB); get_data.sh downloads them from bls.gov/cew/downloadable-data-files.htm. Included: BTS Border Crossing Entry Data (data.transportation.gov, dataset keg4-3bc2), Census 2020 Gazetteer county file, Census county population estimates 2010-2019, USDA ERS Rural-Urban Continuum Codes 2023.

## Reproducing
pip3 install -r requirements.txt, then ./get_data.sh, then ./run_all.sh. All scripts expect inputs in the same folder and write to port_analysis/. Randomization inference uses fixed seeds, so estimates, p-values, and confidence intervals reproduce exactly. A full run takes one to two hours, most of it in ci.py.

## Notes
Alaska is excluded from the main sample (noAK); estimates including it come from the runs without noAK. Appendix A of the paper lists every specification in the order it was estimated. An initial version of the analysis used a border-proximity layer built for a separate project; it is not included, and no result in the paper depends on it.

## License
Code and derived files: CC0 1.0. Source data are public-domain government data.
