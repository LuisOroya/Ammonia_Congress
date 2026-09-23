from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent
SELECTED_K = 9
KDIR = ROOT / "01_Stage1_ReferenceSizing" / "K_sweep_results" / f"K{SELECTED_K:02d}"
INPUT_KDIR = ROOT.parent / "Stage1_K05_K15_inputs" / f"K{SELECTED_K:02d}"
SRC = KDIR / "reference_design_rounded.dat"
TARGETS = [
    ROOT / "02_Stage2_Baselines" / "stage2_fixed_common.dat",
    ROOT / "03_Stage3_Flexibility" / "flex_common.dat",
]

if not SRC.exists():
    raise SystemExit(f"Missing selected design: {SRC}")

txt = SRC.read_text()
vals = {}
for name in ("P_PV_MAX", "P_WD_MAX", "H2_ST_MAX"):
    m = re.search(rf"param\s+{name}\s*:=\s*([0-9eE+\-.]+)\s*;", txt)
    if not m:
        raise SystemExit(f"Could not parse {name} from {SRC}")
    vals[name] = m.group(1)

for path in TARGETS:
    s = path.read_text()
    for name, val in vals.items():
        s, n = re.subn(rf"(param\s+{name}\s*:=\s*)[^;]+;", rf"\g<1>{val};", s, count=1)
        if n != 1:
            raise SystemExit(f"Could not update {name} in {path}")
    path.write_text(s)
    print("Updated design in", path)

# Keep Stage 2 tied to the selected K=9 representative set.
stage2 = ROOT / "02_Stage2_Baselines"
for src_name, dst_name in [
    ("planning_scenarios_2025.dat", "planning_scenarios_2025.dat"),
    ("planning_profiles_2025.dat", "planning_profiles_2025.dat"),
]:
    shutil.copy2(KDIR / src_name, stage2 / dst_name)

map_src = INPUT_KDIR / f"scenario_map_K{SELECTED_K:02d}.csv"
if map_src.exists():
    shutil.copy2(map_src, stage2 / "scenario_map_2025.csv")

print(f"Synchronized selected K={SELECTED_K} reference design and Stage-2 scenarios:")
for k, v in vals.items():
    print(f"  {k} = {v}")
print("IMPORTANT: rerun Stage 2 before preparing Stage 3 inputs.")
