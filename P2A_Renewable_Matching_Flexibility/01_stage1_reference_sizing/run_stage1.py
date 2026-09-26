#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, math, re, shutil, sys, tempfile, csv
from decimal import Decimal, ROUND_CEILING

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from pipeline_config import SELECTED_K, K_VALUES, PV_WIND_ROUND_DECIMALS
from scripts.repro_utils import require_executable, tee_command, file_hashes, write_manifest

MODEL = HERE/'p2a_planning_scenarios.mod'
RUN = HERE/'main_stage1_reference_sizing.run'
COMMON = HERE/'planning_common.dat'
PWL = ROOT/'00_pem_curve'/'generated'/'pem_pwl_6segments.dat'
SCEN_ROOT = HERE/'scenario_sets'
RESULTS = ROOT/'results'/'stage1'
OUTPUTS = ['planning_summary.csv','planning_scenario_summary.csv','planning_dispatch.csv','planned_capacities_exact.dat']


def parse_exact(path: Path):
    txt=path.read_text(encoding='utf-8')
    vals={}
    for name in ('P_PV_MAX','P_WD_MAX','H2_ST_MAX'):
        m=re.search(rf'param\s+{name}\s*:=\s*([0-9eE+\-.]+)\s*;', txt)
        if not m: raise RuntimeError(f'Missing {name} in {path}')
        vals[name]=Decimal(m.group(1))
    return vals


def ceil_decimal(x: Decimal, decimals: int):
    q=Decimal(1).scaleb(-decimals)
    return x.quantize(q, rounding=ROUND_CEILING)


def write_rounded(exact_path: Path, out_path: Path):
    v=parse_exact(exact_path)
    pv=ceil_decimal(v['P_PV_MAX'], PV_WIND_ROUND_DECIMALS)
    wd=ceil_decimal(v['P_WD_MAX'], PV_WIND_ROUND_DECIMALS)
    h2=v['H2_ST_MAX'].quantize(Decimal('1'), rounding=ROUND_CEILING)
    out_path.write_text(
        '# Conservative upward-rounded reference design from Stage 1\n'
        'data;\n'
        f'param P_PV_MAX := {pv:.3f};\n'
        f'param P_WD_MAX := {wd:.3f};\n'
        f'param H2_ST_MAX := {h2:.0f};\n', encoding='utf-8')
    return float(pv), float(wd), float(h2)


def run_one(k: int, overwrite: bool):
    tag=f'K{k:02d}'
    scen=SCEN_ROOT/tag
    dest=RESULTS/tag
    if dest.exists() and any(dest.iterdir()):
        if not overwrite: raise SystemExit(f'{dest} already contains results; use --overwrite.')
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    required=[MODEL,RUN,COMMON,PWL,scen/'planning_scenarios.dat',scen/'planning_profiles.dat',scen/'scenario_map.csv']
    missing=[p for p in required if not p.exists()]
    if missing: raise SystemExit('Missing Stage-1 input(s):\n'+'\n'.join(map(str,missing)))
    with tempfile.TemporaryDirectory(prefix=f'p2a_stage1_{tag}_') as td:
        w=Path(td)
        for src,name in [(MODEL,MODEL.name),(RUN,RUN.name),(COMMON,COMMON.name),(PWL,'pem_pwl.dat'),
                         (scen/'planning_scenarios.dat','planning_scenarios.dat'),
                         (scen/'planning_profiles.dat','planning_profiles.dat')]:
            shutil.copy2(src,w/name)
        log=dest/'solver_log.txt'
        rc=tee_command(['ampl',RUN.name], w, log)
        if rc!=0: raise SystemExit(f'{tag} AMPL run failed; see {log}')
        for name in OUTPUTS:
            p=w/name
            if not p.exists(): raise SystemExit(f'{tag} missing expected output: {name}')
            shutil.copy2(p,dest/name)
    shutil.copy2(scen/'planning_scenarios.dat',dest/'planning_scenarios.dat')
    shutil.copy2(scen/'planning_profiles.dat',dest/'planning_profiles.dat')
    shutil.copy2(scen/'scenario_map.csv',dest/'scenario_map.csv')
    rounded=write_rounded(dest/'planned_capacities_exact.dat',dest/'reference_design_rounded.dat')
    write_manifest(dest/'manifest.json', {
        'stage':'stage1','K':k,'selected_for_downstream':k==SELECTED_K,
        'rounded_reference_design':{'pv_MW':rounded[0],'wind_MW':rounded[1],'h2_storage_kg':rounded[2]},
        'input_hashes':file_hashes(required, ROOT),
        'output_hashes':file_hashes([dest/x for x in OUTPUTS]+[dest/'reference_design_rounded.dat'], ROOT)
    })
    print(f'\n{tag} saved to {dest}')


def summarize(ks):
    rows=[]
    for k in ks:
        p=RESULTS/f'K{k:02d}'/'planning_summary.csv'
        if not p.exists(): continue
        with p.open(newline='') as fh:
            r=next(csv.DictReader(fh))
        rows.append({'K':k,**r})
    if rows:
        fields=list(rows[0].keys())
        with (RESULTS/'stage1_sweep_summary.csv').open('w',newline='',encoding='utf-8') as fh:
            w=csv.DictWriter(fh,fieldnames=fields); w.writeheader(); w.writerows(rows)


def main():
    ap=argparse.ArgumentParser()
    g=ap.add_mutually_exclusive_group()
    g.add_argument('--selected-only',action='store_true',help=f'Run only selected K={SELECTED_K}.')
    g.add_argument('--k',type=int,help='Run one K value.')
    ap.add_argument('--overwrite',action='store_true')
    a=ap.parse_args()
    require_executable('ampl')
    ks=[a.k] if a.k is not None else ([SELECTED_K] if a.selected_only else list(K_VALUES))
    for k in ks:
        if k not in K_VALUES: raise SystemExit(f'K={k} not in configured K_VALUES={K_VALUES}')
        run_one(k,a.overwrite)
    summarize(ks if not a.selected_only and a.k is None else K_VALUES)
    if not (RESULTS/f'K{SELECTED_K:02d}'/'reference_design_rounded.dat').exists():
        print(f'WARNING: selected K={SELECTED_K} result is not available yet; Stage 2 cannot run.')

if __name__=='__main__': main()
