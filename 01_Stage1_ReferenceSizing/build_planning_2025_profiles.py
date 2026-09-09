from pathlib import Path
import pandas as pd
import calendar

# ------------------------------------------------------------------
# Provisional 2025 scenario builder.
# Reads Renewables.ninja point-API CSVs with comment metadata lines.
# It keeps UTC calendar months for this computational test.
# ------------------------------------------------------------------

BASE = Path(__file__).resolve().parent
PV_FILE = Path('/mnt/data/PV_2025 (1)(1).csv')
WD_FILE = Path('/mnt/data/WD_2025 (1)(1).csv')

SCEN_DAT = BASE / 'planning_scenarios_2025.dat'
PROF_DAT = BASE / 'planning_profiles_2025.dat'
MAP_CSV = BASE / 'scenario_map_2025.csv'


def read_ninja(path: Path, value_name: str) -> pd.DataFrame:
    df = pd.read_csv(path, comment='#')
    if list(df.columns) != ['time', 'electricity']:
        raise ValueError(f'Unexpected columns in {path}: {df.columns.tolist()}')
    df['time'] = pd.to_datetime(df['time'], format='%Y-%m-%d %H:%M')
    df = df.rename(columns={'electricity': value_name})
    return df


pv = read_ninja(PV_FILE, 'pv')
wd = read_ninja(WD_FILE, 'wd')

df = pv.merge(wd, on='time', how='inner', validate='one_to_one')
if len(df) != 8760:
    raise ValueError(f'Expected 8760 matched hours for 2025, got {len(df)}')
if df['time'].min() != pd.Timestamp('2025-01-01 00:00'):
    raise ValueError('Unexpected first timestamp')
if df['time'].max() != pd.Timestamp('2025-12-31 23:00'):
    raise ValueError('Unexpected last timestamp')

scenario_rows = []
profiles = {}
for month in range(1, 13):
    s = month
    sub = df[df['time'].dt.month.eq(month)].copy().reset_index(drop=True)
    expected = calendar.monthrange(2025, month)[1] * 24
    if len(sub) != expected:
        raise ValueError(f'Month {month}: expected {expected} h, got {len(sub)}')
    profiles[s] = sub
    scenario_rows.append({
        'scenario': s,
        'month': calendar.month_name[month],
        'year': 2025,
        'hours': len(sub),
        'probability': 1/12,
        'time_basis': 'UTC',
    })

meta = pd.DataFrame(scenario_rows)
meta.to_csv(MAP_CSV, index=False)

# Scenario structure file.
with SCEN_DAT.open('w', encoding='utf-8') as f:
    f.write('# ============================================================\n')
    f.write('# planning_scenarios_2025.dat\n')
    f.write('# Provisional test: each UTC calendar month of 2025 is one scenario.\n')
    f.write('# Equal temporary probability 1/12.\n')
    f.write('# ============================================================\n\n')
    f.write('set S := 1 2 3 4 5 6 7 8 9 10 11 12;\n')
    f.write('param TMAX := 744;\n\n')
    f.write('param: NPER PROB :=\n')
    for row in scenario_rows:
        f.write(f"{row['scenario']:2d} {row['hours']:3d} {row['probability']:.12f}\n")
    f.write(';\n')

# Profile matrices. Values after NPER[s] are padded with zero and ignored.
TMAX = 744
with PROF_DAT.open('w', encoding='utf-8') as f:
    f.write('# ============================================================\n')
    f.write('# planning_profiles_2025.dat\n')
    f.write('# Renewables.ninja normalized profiles; source timestamps in UTC.\n')
    f.write('# Rows = scenarios/months, columns = within-month hour 1..744.\n')
    f.write('# Padded zeros after each scenario\'s NPER are ignored by the model.\n')
    f.write('# ============================================================\n\n')

    cols = ' '.join(str(t) for t in range(1, TMAX + 1))
    f.write(f'param zeta_PV: {cols} :=\n')
    for s in range(1, 13):
        vals = profiles[s]['pv'].astype(float).tolist()
        vals += [0.0] * (TMAX - len(vals))
        f.write(str(s) + ' ' + ' '.join(f'{v:.6f}' for v in vals) + '\n')
    f.write(';\n\n')

    f.write(f'param zeta_WD: {cols} :=\n')
    for s in range(1, 13):
        vals = profiles[s]['wd'].astype(float).tolist()
        vals += [0.0] * (TMAX - len(vals))
        f.write(str(s) + ' ' + ' '.join(f'{v:.6f}' for v in vals) + '\n')
    f.write(';\n')

print(f'Wrote {SCEN_DAT}')
print(f'Wrote {PROF_DAT}')
print(f'Wrote {MAP_CSV}')
print(meta.to_string(index=False))
