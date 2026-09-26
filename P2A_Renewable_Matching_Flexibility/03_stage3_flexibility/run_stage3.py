#!/usr/bin/env python3
from pathlib import Path
import argparse, shutil, subprocess, sys, tempfile
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
from pipeline_config import SELECTED_K
from scripts.repro_utils import require_executable, tee_command, file_hashes, write_manifest
S1=ROOT/'results'/'stage1'/f'K{SELECTED_K:02d}'; S2=ROOT/'results'/'stage2'; RESULTS=ROOT/'results'/'stage3'; SCEN=ROOT/'01_stage1_reference_sizing'/'scenario_sets'/f'K{SELECTED_K:02d}'
MODEL=HERE/'p2a_stage3_paired_flex_sbpwl.mod'; COMMON=HERE/'flex_common.dat'; PWL=ROOT/'00_pem_curve'/'generated'/'pem_pwl_6segments.dat'; PILOT=HERE/'main_stage3_pilot.run'; FULL=HERE/'main_stage3_flexibility.run'; PREP=HERE/'prepare_stage3_inputs.py'; ANALYZE=HERE/'analyze_stage3_results.py'

def run_ampl(runfile, output_csv, logname, baseline):
    with tempfile.TemporaryDirectory(prefix='p2a_stage3_') as td:
        w=Path(td)
        for src,name in [(MODEL,MODEL.name),(COMMON,COMMON.name),(PWL,'pem_pwl.dat'),(runfile,runfile.name),(S1/'reference_design_rounded.dat','reference_design.dat'),(SCEN/'planning_scenarios.dat','planning_scenarios.dat'),(SCEN/'planning_profiles.dat','planning_profiles.dat'),(baseline,'stage3_baselines_k09.dat')]: shutil.copy2(src,w/name)
        log=RESULTS/logname; rc=tee_command(['ampl',runfile.name],w,log)
        if rc!=0: raise SystemExit(f'{runfile.name} failed; see {log}')
        p=w/output_csv
        if not p.exists(): raise SystemExit(f'Missing {output_csv}')
        shutil.copy2(p,RESULTS/output_csv)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--overwrite',action='store_true'); ap.add_argument('--pilot-only',action='store_true'); a=ap.parse_args(); require_executable('ampl')
    needed=[PWL,S1/'reference_design_rounded.dat',S2/'stage2_baselines.csv',S2/'stage2_reference_design.csv',SCEN/'planning_scenarios.dat',SCEN/'planning_profiles.dat']
    miss=[p for p in needed if not p.exists()]
    if miss: raise SystemExit('Stage 3 requires completed Stages 1 and 2. Missing:\n'+'\n'.join(map(str,miss)))
    RESULTS.mkdir(parents=True,exist_ok=True)
    if a.overwrite:
        for p in RESULTS.iterdir():
            if p.name!='README.md': shutil.rmtree(p) if p.is_dir() else p.unlink()
    elif any(p.name!='README.md' for p in RESULTS.iterdir()):
        raise SystemExit(f'{RESULTS} contains outputs; use --overwrite.')
    subprocess.run([sys.executable,str(PREP)],check=True)
    baseline=RESULTS/'stage3_baselines_k09.dat'
    run_ampl(PILOT,'stage3_pilot_results.csv','pilot_solver_log.txt',baseline)
    subprocess.run([sys.executable,str(ANALYZE),str(RESULTS/'stage3_pilot_results.csv'),'--output-dir',str(RESULTS),'--prefix','pilot_'],check=True)
    # Pilot should be 64 rows and have no violations.
    import pandas as pd
    p=pd.read_csv(RESULTS/'stage3_pilot_results.csv')
    if len(p)!=64: raise SystemExit(f'Pilot expected 64 rows, got {len(p)}')
    if (p.F_RM_MW > p.F_PHYS_MW + 1e-3).any(): raise SystemExit('Pilot nesting validation failed; full run not started.')
    if a.pilot_only: return
    run_ampl(FULL,'stage3_flexibility_results.csv','full_solver_log.txt',baseline)
    subprocess.run([sys.executable,str(ANALYZE),str(RESULTS/'stage3_flexibility_results.csv'),'--output-dir',str(RESULTS),'--expect-full'],check=True)
    write_manifest(RESULTS/'manifest.json',{'stage':'stage3','selected_K':SELECTED_K,'input_hashes':file_hashes(needed+[baseline], ROOT),'output_hashes':file_hashes([RESULTS/'stage3_flexibility_results.csv',RESULTS/'stage3_retention_summary.csv',RESULTS/'stage3_scenario_summary.csv'], ROOT)})
    print(f'Stage 3 complete: {RESULTS}')
if __name__=='__main__': main()
