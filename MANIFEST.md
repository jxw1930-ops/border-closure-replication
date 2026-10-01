# Manifest: where each number in the paper comes from

Each row gives the location in the paper, the results file in port_analysis/, and the exact string in that file.

| Location in paper | File | String | Status |
|---|---|---|---|
| Sec 4.1 county groups | `summary.txt` | `mx=24, ca=75, far=2791` | OK |
| Table 2 baseline, restriction | `robust_44-45_lam15_noAK.txt` | `restr=-2.19` | OK |
| Table 2 baseline, contrast | `robust_44-45_lam15_noAK.txt` | `dip=-1.04` | OK |
| Table 2 continuous dose | `robust_44-45_lam15_noAK.txt` | `dip=-0.37` | OK |
| Table 2 high exposure | `robust_44-45_lam15_noAK.txt` | `dip=-1.95` | OK |
| Sec 4.2 exposure | `robust_44-45_lam15_noAK.txt` | `median 167.8, max 1444.6` | OK |
| Table 2 memo row, Alaska included | `robust_44-45_lam15.txt` | `dip=-2.67` | OK |
| Table 4, lambda 10 | `robust_44-45_lam10_noAK.txt` | `dip=-0.44` | OK |
| Table 4, lambda 25 | `robust_44-45_lam25_noAK.txt` | `dip=-0.32` | OK |
| Table 3 row 1 | `ci_44-45_ca_noAK.txt` | `beta = +2.66` | OK |
| Table 3 row 1, implied CI | `ci_44-45_ca_noAK.txt` | `[-4.30, -0.39]` | OK |
| Table 3 row 2 | `ci_44-45_ca_noAK_det.txt` | `beta = +0.85` | OK |
| Table 3 row 2, implied CI | `ci_44-45_ca_noAK_det.txt` | `[-3.95, +2.05]` | OK |
| Table 3 row 5 | `ci_72_ca_noAK_det.txt` | `beta = -1.49` | OK |
| Table 3 row 7 | `ci_44-45_mx_det.txt` | `beta = +7.45` | OK |
| Sec 7.4 manufacturing placebo | `flow_31-33_ca_lam15_noAK.txt` | `beta=  +1.19` | OK |
| Sec 5 mean shortfall, Canada | `flow_44-45_ca_lam15_noAK.txt` | `restr: -0.88` | OK |
| Sec 5 mean shortfall, Mexico | `flow_44-45_mx_lam15.txt` | `restr: -0.41` | OK |

Table 1 (monthly crossing index) is in logs/print_results.txt, block "Inbound people crossings".
Section 3.4 figures on the 100-mile border zone come from a distance layer built for a separate project and are not included.
Figure 1 is port_analysis/fig1_first_stage.png (vector version .pdf), produced by make_fig1.py.
