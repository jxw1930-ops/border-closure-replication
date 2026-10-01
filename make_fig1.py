import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
D = Path(__file__).resolve().parent; OUT = D / "port_analysis"; OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.titlesize": 10})
PEOPLE = ["Personal Vehicle Passengers", "Pedestrians", "Bus Passengers", "Train Passengers"]
b = pd.read_csv(D / "bts_border_crossing.csv")
b["date"] = pd.to_datetime(b["Date"], format="%b %Y")
b = b[b.date >= "2015-01-01"]
b["kind"] = np.where(b.Measure.isin(PEOPLE), "Persons", np.where(b.Measure.eq("Trucks"), "Trucks", None))
m = b[b.kind.notna()].groupby(["Border", "kind", "date"]).Value.sum().reset_index()
base = m[m.date.dt.year == 2019].groupby(["Border", "kind"]).Value.mean().rename("base")
m = m.join(base, on=["Border", "kind"]); m["idx"] = 100 * m.Value / m.base
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=True)
for ax, bd, title in zip(axes, ["US-Canada Border", "US-Mexico Border"], ["A. US-Canada border", "B. US-Mexico border"]):
    ax.axvspan(pd.Timestamp("2020-03-21"), pd.Timestamp("2021-11-08"), color="0.88", lw=0, zorder=0)
    for k, sty in [("Persons", dict(color="black", lw=1.3, ls="-")), ("Trucks", dict(color="0.45", lw=1.0, ls="--"))]:
        s = m[(m.Border == bd) & (m.kind == k)].sort_values("date")
        ax.plot(s.date, s.idx, label=k, **sty)
    ax.axhline(100, color="0.6", lw=0.5)
    if bd == "US-Canada Border":
        for d in ["2022-04-01", "2022-10-01"]:
            ax.axvline(pd.Timestamp(d), color="0.3", lw=0.7, ls=":")
    ax.set_title(title, loc="left"); ax.set_ylim(0, max(150, 1.05 * m[m.Border == bd].idx.max()))
    ax.grid(axis="y", color="0.9", lw=0.5); ax.spines[["top", "right"]].set_visible(False)
axes[0].set_ylabel("Index (2019 monthly mean = 100)")
axes[0].legend(frameon=False, loc="lower left")
plt.tight_layout()
for ext in ["png", "pdf"]:
    plt.savefig(OUT / f"fig1_first_stage.{ext}", dpi=300)
print("saved", OUT / "fig1_first_stage.png")
