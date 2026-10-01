# Closing the Land Border

Replication package for *Closing the Land Border: Cross-Border Visitor Flows and Local Employment in U.S. Border Counties, 2020–2026.*

Junyang Wang · jxw1930@case.edu

---

## The paper

From March 2020 to November 2021 the United States restricted non-essential travel across its land borders with Canada and Mexico. Inbound person crossings on the Canadian border fell to **3 percent** of their 2019 level. Truck freight was exempt and fell only to 67 percent, which makes the collapse in visitors a policy shock rather than a general contraction.

This paper asks whether the loss of cross-border visitors reduced employment in nearby U.S. counties.

**The finding is a bounded null.** Retail employment in Canada-port counties was about 2.3 log points lower during the restrictions than in 2019, relative to same-state comparison counties. Once the treated group's pre-existing linear trend is removed, the estimate is not distinguishable from zero, with a randomization confidence interval running from roughly −4 to +2 log points. That rules out the large effects the cross-border shopping literature would predict, and the paper gives three mechanisms for why: the restrictions were two-way, employment is a coarse margin with the Paycheck Protection Program in force, and there is a pre-existing relative decline whose counterfactual cannot be tested.

### A measurement problem in the existing treatment definition

An earlier version of this analysis defined border counties using the 100-mile zone that follows the Customs and Border Protection enforcement boundary. That layer measures distance to **all** external boundaries, including coastlines and the Great Lakes shoreline. It places Cook County, Illinois 7.2 miles from the border, and classifies New York, Los Angeles, Miami, Seattle and Boston as border counties — 1,128 in total.

Results built on that definition measure the coastal-metropolitan pandemic shock, not a border effect. The design here is rebuilt around distance to the nearest land port of entry. Section 3.4 of the paper documents the problem.

---

## Reproducing the results

```bash
bash get_data.sh        # downloads QCEW, BTS crossings, Gazetteer, population, RUCC
pip install -r requirements.txt
bash run_all.sh         # builds the panel, estimates everything, writes tables and figures
```

Runtime is roughly an hour on a laptop, most of it in panel construction. No proprietary data and no credentials are required.

---

## What is in here

| File | What it does |
|---|---|
| `build_qcew_panel_2015_2026.py` | Builds the county × industry × quarter panel from QCEW single files. Private ownership only; suppressed cells set to missing rather than zero. 3,235 counties, 45 quarters. |
| `port_analysis.py` | Great-circle distances from county internal points to each of the 111 land ports with 2019 passenger traffic; assigns port-proximity groups. |
| `robust.py` | Binned event study, the trend-robust contrast, state exclusions, rural-urban-by-quarter fixed effects, gravity exposure, and the dose split. |
| `flow.py` | The main flow-intensity design, using each county's time-varying visitor shortfall. Optional detrending. |
| `ci.py` | Randomization confidence intervals by test inversion. |
| `make_fig1.py` | Figure 1, the first stage. |
| `make_package.py` | Assembles this package and runs the verification check below. |
| `run_all.sh` | Everything, in order. |
| `MANIFEST.md` | Every output file, with the table or figure it produces. |
| `exploratory/` | Earlier scripts kept for provenance. Not part of the reported results. |

---

## Verification

`make_package.py` checks **eighteen headline numbers** from the text of the paper against the values the code actually produces. All eighteen match. The check runs as part of package assembly, so the numbers in the paper cannot drift from the numbers in the code without the build failing.

Appendix A of the paper is a specification log: every specification in the order it was estimated, with the reason for each change, including the changes that weakened the result.

---

## Methods worth noting

**Gravity-allocated exposure.** Summing crossings at all nearby ports double-counts. Each port's 2019 traffic is instead allocated across surrounding counties by

```
a_cj = R_c · exp(−d_cj / λ) · 1{d_cj ≤ 75 miles},    s_cj = a_cj / Σ_k a_kj
```

where `R_c` is the county's 2019 retail employment, so visitors are assumed to go where the stores are, with `λ = 15` miles. Results under `λ = 10` and `λ = 25` are in the robustness section.

**Trend-robust contrast.** The pre-period coefficient is not zero, so the reported contrast is

```
dip = β_restr − w · β_after,    w = (m_restr − m_ref) / (m_after − m_ref) = 0.545
```

with `m` the mean time of each bin. A linear trend contributes to the two coefficients in proportion to their distance from the reference period, so this weighting cancels it exactly.

**Randomization inference.** Treated counties sit in roughly a dozen states, too few for cluster-robust standard errors. Every p-value comes from reassigning each county's full treatment path at random among counties in the same state. Confidence intervals are obtained by inverting that test over a grid of candidate values rather than from standard errors.

---

## Data

All sources are public and free.

- BLS Quarterly Census of Employment and Wages, quarterly single files, 2015–2026
- BTS Border Crossing Entry Data
- 2020 Census Gazetteer county file
- Census county population estimates, 2010–2019
- USDA ERS 2023 Rural-Urban Continuum Codes

---

## Related

Replication package for my E-Verify paper, archived under CC0:
[doi.org/10.7910/DVN/XR82YN](https://doi.org/10.7910/DVN/XR82YN) · paper at [ssrn.com/abstract=7399981](https://ssrn.com/abstract=7399981)

## License

Code released under the MIT License. The underlying data are public U.S. federal government sources and carry no additional restrictions.
