import sys, numpy as np, pandas as pd
from pathlib import Path
src = open(Path(__file__).resolve().parent / "flow.py").read()
exec(src[:src.index("\nsay(f\"{'DETRENDED")])
NP = NPERM; GRID = 41; out2 = []
def say2(x=""): print(x); out2.append(str(x))
def mk(codes):
    n = np.bincount(codes)
    return lambda v: np.asarray(v, float) - (np.bincount(codes, weights=np.asarray(v, float), minlength=len(n)) / n)[codes]
def run(use_dose, mask, label):
    r = mk(pd.factorize(pd.Series(g[mask]))[0])
    pm = ispre[mask]; rp = mk(pd.factorize(pd.Series(g[mask][pm]))[0])
    cim, pim, ttm = ci[mask], pi[mask], tt[mask]
    def beta(P, yv):
        w = dose[P[cim]] if use_dose else cty.treat.values[P[cim]].astype(float)
        x = Dm[P[cim], pim] * (dose[P[cim]] if use_dose else 1.0)
        y = yv
        if DET:
            T = ttm * w; Tp = rp(T[pm]); c = (Tp @ rp(y[pm])) / (Tp @ Tp) if (Tp @ Tp) > 0 else 0.0
            y = y - c * T
        xr = r(x); d = xr @ xr
        return (xr @ r(y)) / d if d > 0 else 0.0
    I = np.arange(len(cty)); yv = s.y.values[mask]
    xobs = Dm[cim, pim] * (dose[cim] if use_dose else 1.0)
    Ps = [perm() for _ in range(NP)]
    b = beta(I, yv); null = np.array([beta(P, yv) for P in Ps])
    p0 = (np.abs(null) >= abs(b)).mean()
    yb = yv - b * xobs; sd0 = np.array([beta(P, yb) for P in Ps]).std()
    grid = np.linspace(b - 5 * sd0, b + 5 * sd0, GRID); acc = []
    for b0 in grid:
        y0 = yv - b0 * xobs
        bo = beta(I, y0); bn = np.array([beta(P, y0) for P in Ps])
        if (np.abs(bn) >= abs(bo)).mean() >= 0.05: acc.append(b0)
    lo, hi = (min(acc), max(acc)) if acc else (np.nan, np.nan)
    edge = " (CI reaches grid edge; widen)" if acc and (lo == grid[0] or hi == grid[-1]) else ""
    sh = Dm[cty.treat.values == 1][:, np.isin(np.array(pers), np.unique(per[BIN == "restr"]))].mean()
    say2(f"\n{label}")
    say2(f"  beta = {b:+.2f}   p_RI = {p0:.3f}   95% CI [{lo:+.2f}, {hi:+.2f}]{edge}")
    say2(f"  implied employment effect at the mean restriction-period shortfall ({sh:+.2f}): "
         f"{b*sh:+.2f}, CI [{min(lo*sh, hi*sh):+.2f}, {max(lo*sh, hi*sh):+.2f}] log points x100")
say2(f"{'DETRENDED ' if DET else ''}CI  industry {IND}, border {BORDER}, LAM={LAM}, perms={NP}, grid={GRID}")
full = np.ones(len(s), bool); win = per <= "2022Q1"
for use_dose, dn in [(False, "shortfall x 1"), (True, "shortfall x dose (per 1 SD)")]:
    run(use_dose, win, f"[{dn}] restriction window 2015Q1-2022Q1")
    run(use_dose, full, f"[{dn}] full sample 2015Q1-2026Q1")
f = O / f"ci_{IND}_{BORDER}{'_noAK' if 'noAK' in a else ''}{'_det' if DET else ''}.txt"
f.write_text("\n".join(out2)); print(f"\nSaved to {f}")
