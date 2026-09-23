#!/usr/bin/env python3
"""Prepare Stage-3 AMPL baseline data from the final Stage-2 CSV.

Expected location:
  03_Stage3_Flexibility/prepare_stage3_inputs.py
Reads:
  ../02_Stage2_Baselines/stage2_baselines.csv
  ../02_Stage2_Baselines/stage2_reference_design.csv
Writes:
  stage3_baselines_k09.dat

Only Stage-2 cases 1 (MONTHLY) and 2 (HOURLY) are loaded because the
no-matching case has no distinct RM branch (RM == PHYS).
"""
from pathlib import Path
import csv
import math

HERE = Path(__file__).resolve().parent
S2 = HERE.parent / "02_Stage2_Baselines"
BASE_CSV = S2 / "stage2_baselines.csv"
REF_CSV = S2 / "stage2_reference_design.csv"
OUT = HERE / "stage3_baselines_k09.dat"

EXPECTED_REF = (159.96, 499.30, 27920.0)
CASES = (1, 2)
EXPECTED_NPER = {1:744, 2:744, 3:696, 4:720, 5:744, 6:744, 7:744, 8:720, 9:720}


def close(a, b, tol=1e-6):
    return abs(a-b) <= tol


def write_slices(f, name, data, times_by_sc, include_zero=False):
    f.write(f"param {name} :=\n")
    for s in sorted(times_by_sc):
        for c in CASES:
            vals = data[(s,c)]
            f.write(f"[{s},{c},*]")
            count = 0
            for t in sorted(vals):
                f.write(f" {t} {vals[t]:.15f}")
                count += 1
                if count % 6 == 0:
                    f.write("\n")
                    if t != max(vals):
                        f.write("  ")
            f.write("\n")
    f.write(";\n\n")


if not BASE_CSV.exists():
    raise SystemExit(f"Missing {BASE_CSV}. Run final Stage 2 first.")
if not REF_CSV.exists():
    raise SystemExit(f"Missing {REF_CSV}.")

with REF_CSV.open(newline="") as fh:
    row = next(csv.DictReader(fh))
ref = (float(row["pv_MW"]), float(row["wind_MW"]), float(row["h2_storage_kg"]))
if not all(close(a,b) for a,b in zip(ref, EXPECTED_REF)):
    raise SystemExit(f"Reference-design mismatch: got {ref}, expected {EXPECTED_REF}")

fields = {
    "BASE_P2A": "p2a_MW",
    "BASE_PEL": "pel_MW",
    "BASE_H2PROD": "h2prod_kgph",
    "BASE_NH3": "nh3_kgph",
    "BASE_PV": "pv_MW",
    "BASE_WD": "wind_MW",
    "BASE_MATCH_LOAD": "match_load_MW",
}
data = {name:{} for name in fields}
h2 = {}
rows_seen = {(s,c):0 for s in EXPECTED_NPER for c in CASES}

with BASE_CSV.open(newline="") as fh:
    reader = csv.DictReader(fh)
    for row in reader:
        c = int(row["case"])
        if c not in CASES:
            continue
        s = int(row["scenario"])
        t = int(row["t"])
        key = (s,c)
        rows_seen[key] += 1
        for name, col in fields.items():
            data[name].setdefault(key,{})[t] = float(row[col])
        h2.setdefault(key,{})[t] = float(row["h2st_kg"])

for s,n in EXPECTED_NPER.items():
    for c in CASES:
        if rows_seen[(s,c)] != n:
            raise SystemExit(f"Incomplete baseline for scenario {s}, case {c}: "
                             f"{rows_seen[(s,c)]} rows, expected {n}")
        # Stage-2 initial H2 state is 50% of the fixed 27,920 kg tank.
        h2[(s,c)][0] = 0.5*EXPECTED_REF[2]

# Prefix cumulative histories, with k=0 representing no elapsed hour.
cum_nh3, cum_res, cum_match = {}, {}, {}
for s,n in EXPECTED_NPER.items():
    for c in CASES:
        key=(s,c)
        cum_nh3[key]={0:0.0}
        cum_res[key]={0:0.0}
        cum_match[key]={0:0.0}
        a=b=d=0.0
        for t in range(1,n+1):
            a += data["BASE_NH3"][key][t]       # dt=1 h
            b += data["BASE_PV"][key][t] + data["BASE_WD"][key][t]
            d += data["BASE_MATCH_LOAD"][key][t]
            cum_nh3[key][t]=a
            cum_res[key][t]=b
            cum_match[key][t]=d

with OUT.open("w", newline="\n") as f:
    f.write("# ============================================================\n")
    f.write("# stage3_baselines_k09.dat\n")
    f.write("# Generated from FINAL independent-scenario Stage-2 baselines.\n")
    f.write("# Cases: 1=MONTHLY, 2=HOURLY.\n")
    f.write("# Prefix cumulative quantities include hours 1..k; k=0 is zero.\n")
    f.write("# ============================================================\n\n")
    f.write("data;\n\n")
    for name in ["BASE_P2A","BASE_PEL","BASE_H2PROD","BASE_NH3",
                 "BASE_PV","BASE_WD","BASE_MATCH_LOAD"]:
        write_slices(f, name, data[name], EXPECTED_NPER)
    write_slices(f, "BASE_H2ST", h2, EXPECTED_NPER, include_zero=True)
    write_slices(f, "BASE_NH3_CUM", cum_nh3, EXPECTED_NPER, include_zero=True)
    write_slices(f, "BASE_RES_CUM", cum_res, EXPECTED_NPER, include_zero=True)
    write_slices(f, "BASE_MATCH_CUM", cum_match, EXPECTED_NPER, include_zero=True)

print("Stage-3 baseline input created:")
print(f"  {OUT}")
print("Validated:")
print("  reference design = 159.96 MW PV / 499.30 MW wind / 27,920 kg H2")
print("  scenarios = 1..9")
print("  cases = 1 MONTHLY, 2 HOURLY")
