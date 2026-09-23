#!/usr/bin/env python3
"""Summarize paired Stage-3 PHYS/RM flexibility results."""
from pathlib import Path
import sys
import pandas as pd
import numpy as np

HERE = Path(__file__).resolve().parent
inp = HERE / (sys.argv[1] if len(sys.argv) > 1 else "stage3_flexibility_results.csv")
if not inp.exists():
    raise SystemExit(f"Missing {inp}")

df = pd.read_csv(inp)
required = {"scenario","probability","case","case_name","duration_h","start","direction",
            "F_PHYS_MW","F_RM_MW","retained_ratio","loss_MW"}
missing = required - set(df.columns)
if missing:
    raise SystemExit(f"Missing columns: {sorted(missing)}")

# Numerical/reporting threshold: 1 kW. This is far below the MW-scale
# flexibility values of interest and prevents replay-tolerance residues
# from being interpreted as physical flexibility.
ZERO_TOL = 1e-3
NEST_TOL = 1e-3

# Sanitize any tiny residuals in older/pilot CSVs before aggregation.
df.loc[df.F_PHYS_MW.abs() <= ZERO_TOL, "F_PHYS_MW"] = 0.0
df.loc[df.F_RM_MW.abs() <= ZERO_TOL, "F_RM_MW"] = 0.0
df["loss_MW"] = df.F_PHYS_MW - df.F_RM_MW
df["retained_ratio"] = np.where(df.F_PHYS_MW > ZERO_TOL,
                                df.F_RM_MW / df.F_PHYS_MW,
                                np.nan)

viol = df[df.F_RM_MW > df.F_PHYS_MW + NEST_TOL].copy()

# Scenario-level aggregation first, so months with more admissible sampled
# starts are not inadvertently given more weight.
gcols=["scenario","probability","case","case_name","duration_h","direction"]
rows=[]
for key,g in df.groupby(gcols, sort=True):
    s,p,c,cname,d,q=key
    phys=g.F_PHYS_MW.mean()
    rm=g.F_RM_MW.mean()
    valid=g[g.F_PHYS_MW > ZERO_TOL]
    rows.append({
        "scenario":s,"probability":p,"case":c,"case_name":cname,
        "duration_h":d,"direction":q,"n_events":len(g),
        "mean_phys_MW":phys,"mean_rm_MW":rm,
        "retained_ratio_of_means": (rm/phys if phys > ZERO_TOL else np.nan),
        "mean_event_retained_ratio": (valid.F_RM_MW/valid.F_PHYS_MW).mean() if len(valid) else np.nan,
        "mean_loss_MW":(g.F_PHYS_MW-g.F_RM_MW).mean(),
        "rm_zero_fraction":(g.F_RM_MW <= ZERO_TOL).mean(),
        "min_phys_MW":g.F_PHYS_MW.min(),"max_phys_MW":g.F_PHYS_MW.max(),
        "min_rm_MW":g.F_RM_MW.min(),"max_rm_MW":g.F_RM_MW.max(),
    })
scen=pd.DataFrame(rows)
scen.to_csv(HERE/"stage3_scenario_summary.csv",index=False)

# Probability-weight scenario means. For the final K=9 sweep, the scenario
# probabilities sum to 1. For a pilot containing only a subset of scenarios,
# normalize over the included probability mass so the reported MW values are
# interpretable, and record the covered probability mass explicitly.
rows=[]
for (c,cname,d,q),g in scen.groupby(["case","case_name","duration_h","direction"], sort=True):
    w=g.probability.to_numpy(float)
    coverage=float(np.sum(w))
    if coverage <= 0:
        raise SystemExit("Non-positive probability coverage in Stage-3 summary.")
    wn=w/coverage
    phys=float(np.sum(wn*g.mean_phys_MW))
    rm=float(np.sum(wn*g.mean_rm_MW))
    loss=phys-rm
    rows.append({
        "case":c,"case_name":cname,"duration_h":d,"direction":q,
        "n_scenarios":len(g),"n_events":int(g.n_events.sum()),
        "probability_coverage":coverage,
        "weighted_mean_phys_MW":phys,"weighted_mean_rm_MW":rm,
        "weighted_retained_ratio":(rm/phys if phys > ZERO_TOL else np.nan),
        "weighted_loss_MW":loss,
        "weighted_loss_fraction":(loss/phys if phys > ZERO_TOL else np.nan),
        "weighted_rm_zero_fraction":float(np.sum(wn*g.rm_zero_fraction)),
    })
summary=pd.DataFrame(rows)
summary.to_csv(HERE/"stage3_retention_summary.csv",index=False)

print("Stage-3 analysis complete")
print(f"  input rows: {len(df)}")
print(f"  nesting violations RM > PHYS + {NEST_TOL}: {len(viol)}")
print("  outputs:")
print("    stage3_scenario_summary.csv")
print("    stage3_retention_summary.csv")
if len(viol):
    viol.to_csv(HERE/"stage3_nesting_violations.csv",index=False)
    print("    stage3_nesting_violations.csv")
else:
    p=HERE/"stage3_nesting_violations.csv"
    if p.exists(): p.unlink()

if len(summary):
    print("\nProbability-weighted summary:")
    print(summary.to_string(index=False))
