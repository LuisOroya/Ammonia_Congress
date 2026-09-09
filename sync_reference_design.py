from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
SRC = ROOT / '01_Stage1_ReferenceSizing' / 'reference_design_rounded.dat'
TARGETS = [
    ROOT / '02_Stage2_Baselines' / 'stage2_fixed_common.dat',
    ROOT / '03_Stage3_Flexibility' / 'flex_common.dat',
]

if not SRC.exists():
    raise SystemExit(f'Missing {SRC}. Run Stage 1 first.')

txt = SRC.read_text()
vals = {}
for name in ('P_PV_MAX','P_WD_MAX','H2_ST_MAX'):
    m = re.search(rf'param\s+{name}\s*:=\s*([0-9eE+\-.]+)\s*;', txt)
    if not m:
        raise SystemExit(f'Could not parse {name} from {SRC}')
    vals[name] = m.group(1)

for path in TARGETS:
    s = path.read_text()
    for name, val in vals.items():
        s, n = re.subn(rf'(param\s+{name}\s*:=\s*)[^;]+;', rf'\g<1>{val};', s, count=1)
        if n != 1:
            raise SystemExit(f'Could not update {name} in {path}')
    path.write_text(s)
    print('Updated', path)

print('Synchronized rounded reference design:')
for k,v in vals.items():
    print(f'  {k} = {v}')
print('IMPORTANT: rerun Stage 2 after any design change before preparing Stage 3 data.')
