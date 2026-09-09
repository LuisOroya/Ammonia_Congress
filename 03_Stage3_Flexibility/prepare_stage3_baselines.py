from pathlib import Path
import csv
import re

# Development pilot months. Change later when final representative scenarios are available.
SELECTED_SCENARIOS = [3, 9]
CASES = [1, 2, 3]  # monthly, weekly, hourly
NPER = {1:744, 2:672, 3:744, 4:720, 5:744, 6:720, 7:744, 8:744, 9:720, 10:744, 11:720, 12:744}

HERE = Path(__file__).resolve().parent
STAGE2 = HERE.parent / '02_Stage2_Baselines'
BASE_CSV = STAGE2 / 'stage2_baselines.csv'
DESIGN_CSV = STAGE2 / 'stage2_reference_design.csv'
COMMON = HERE / 'flex_common.dat'
OUT = HERE / 'flex_baselines_2025.dat'

for p in [BASE_CSV, DESIGN_CSV, COMMON]:
    if not p.exists():
        raise SystemExit(f'Missing required file: {p}\nRun Stage 2 first, then rerun this script.')

def read_common_design(path: Path):
    txt = path.read_text()
    vals = {}
    for name in ('P_PV_MAX', 'P_WD_MAX', 'H2_ST_MAX'):
        m = re.search(rf'param\s+{name}\s*:=\s*([0-9eE+\-.]+)\s*;', txt)
        if not m:
            raise SystemExit(f'Could not read {name} from {path}')
        vals[name] = float(m.group(1))
    return vals

common_design = read_common_design(COMMON)
with DESIGN_CSV.open(newline='') as f:
    row = next(csv.DictReader(f))
stage2_design = {
    'P_PV_MAX': float(row['pv_MW']),
    'P_WD_MAX': float(row['wind_MW']),
    'H2_ST_MAX': float(row['h2_storage_kg']),
}

for k in common_design:
    if abs(common_design[k] - stage2_design[k]) > 1e-8:
        raise SystemExit(
            f'DESIGN MISMATCH for {k}: Stage2={stage2_design[k]} vs Stage3={common_design[k]}.\n'
            'Do not use tolerances to bypass this. Synchronize the rounded reference design and rerun Stage 2.'
        )

with BASE_CSV.open(newline='') as f:
    rows = list(csv.DictReader(f))

# Index requested baseline rows.
idx = {}
for r in rows:
    s, c, t = int(r['scenario']), int(r['case']), int(r['t'])
    if s in SELECTED_SCENARIOS and c in CASES:
        idx[(s,c,t)] = r

for s in SELECTED_SCENARIOS:
    for c in CASES:
        missing = [t for t in range(1, NPER[s]+1) if (s,c,t) not in idx]
        if missing:
            raise SystemExit(f'Missing Stage-2 baseline rows for scenario {s}, case {c}; first missing t={missing[0]}')

fields = [
    ('BASE_P2A', 'p2a_MW'),
    ('BASE_PEL', 'pel_MW'),
    ('BASE_H2PROD', 'h2prod_kgph'),
    ('BASE_NH3', 'nh3_kgph'),
    ('BASE_PV', 'pv_MW'),
    ('BASE_WD', 'wind_MW'),
]

with OUT.open('w', newline='') as f:
    f.write('# Auto-generated from Stage-2 baselines using the SAME rounded reference design.\n')
    f.write('data;\n\n')
    for pname, col in fields:
        f.write(f'param {pname} :=\n')
        for s in SELECTED_SCENARIOS:
            for c in CASES:
                for t in range(1, NPER[s]+1):
                    v = float(idx[(s,c,t)][col])
                    f.write(f'  [{s},{c},{t}] {v:.10f}\n')
        f.write(';\n\n')

    f.write('param BASE_H2ST :=\n')
    h0 = 0.5 * common_design['H2_ST_MAX']
    for s in SELECTED_SCENARIOS:
        for c in CASES:
            f.write(f'  [{s},{c},0] {h0:.10f}\n')
            for t in range(1, NPER[s]+1):
                v = float(idx[(s,c,t)]['h2st_kg'])
                f.write(f'  [{s},{c},{t}] {v:.10f}\n')
    f.write(';\n')

print('Created:', OUT)
print('Reference design verified:')
print(f"  PV   = {common_design['P_PV_MAX']:.2f} MW")
print(f"  Wind = {common_design['P_WD_MAX']:.2f} MW")
print(f"  H2   = {common_design['H2_ST_MAX']:.0f} kg")
print('Selected scenarios:', SELECTED_SCENARIOS)
