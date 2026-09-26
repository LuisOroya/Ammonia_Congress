#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, shutil, subprocess, sys, tempfile

HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
from pipeline_config import SELECTED_K
from scripts.repro_utils import require_executable, tee_command, file_hashes, write_manifest

S1=ROOT/'results'/'stage1'/f'K{SELECTED_K:02d}'
SCEN=ROOT/'01_stage1_reference_sizing'/'scenario_sets'/f'K{SELECTED_K:02d}'
RESULTS=ROOT/'results'/'stage2'
MODEL=HERE/'p2a_stage2_fixed_baselines_sbpwl.mod'; RUN=HERE/'main_stage2_baselines.run'; COMMON=HERE/'stage2_common.dat'
PWL=ROOT/'00_pem_curve'/'generated'/'pem_pwl_6segments.dat'
OUTPUTS=['stage2_case_summary.csv','stage2_case_scenario_summary.csv','stage2_scenario_solve_summary.csv','stage2_baselines.csv','stage2_segments.csv','stage2_reference_design.csv']

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--overwrite',action='store_true',
                    help='Replace existing Stage-2 outputs and solve Stage 2 again.')
    ap.add_argument('--validate-only',action='store_true',
                    help='Validate existing Stage-2 outputs without solving AMPL again.')
    a=ap.parse_args()
    if not a.validate_only:
        require_executable('ampl')
    design=S1/'reference_design_rounded.dat'
    required=[MODEL,RUN,COMMON,PWL,design,SCEN/'planning_scenarios.dat',SCEN/'planning_profiles.dat',SCEN/'scenario_map.csv']
    missing=[p for p in required if not p.exists()]
    if missing: raise SystemExit('Stage 2 requires a completed selected-K Stage 1. Missing:\n'+'\n'.join(map(str,missing)))

    if a.validate_only:
        missing_outputs=[RESULTS/x for x in OUTPUTS if not (RESULTS/x).exists()]
        extra_needed=[RESULTS/'planning_scenarios.dat', RESULTS/'stage2_reference_design.csv']
        missing_outputs += [p for p in extra_needed if not p.exists()]
        if missing_outputs:
            raise SystemExit('Cannot validate Stage 2; missing existing output(s):\n'+'\n'.join(map(str,missing_outputs)))
        subprocess.run([sys.executable,str(HERE/'validate_stage2_results.py'),str(RESULTS),
                        '--cost-lock-eps','0.01','--expected-design',str(design)],check=True)
        write_manifest(RESULTS/'manifest.json',{
            'stage':'stage2','selected_K':SELECTED_K,'validated_existing_outputs':True,
            'input_hashes':file_hashes(required, ROOT),
            'output_hashes':file_hashes([RESULTS/x for x in OUTPUTS], ROOT)})
        print(f'Stage 2 existing outputs validated: {RESULTS}')
        return

    if RESULTS.exists() and any(RESULTS.iterdir()):
        keep=RESULTS/'README.md'
        existing=[p for p in RESULTS.iterdir() if p.name!='README.md']
        if existing and not a.overwrite: raise SystemExit(f'{RESULTS} contains outputs; use --overwrite.')
        for p in existing:
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    RESULTS.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='p2a_stage2_') as td:
        w=Path(td)
        for src,name in [(MODEL,MODEL.name),(RUN,RUN.name),(COMMON,COMMON.name),(PWL,'pem_pwl.dat'),(design,'reference_design.dat'),
                         (SCEN/'planning_scenarios.dat','planning_scenarios.dat'),(SCEN/'planning_profiles.dat','planning_profiles.dat')]:
            shutil.copy2(src,w/name)
        log=RESULTS/'solver_log.txt'
        rc=tee_command(['ampl',RUN.name],w,log)
        if rc!=0: raise SystemExit(f'Stage 2 failed; see {log}')
        for name in OUTPUTS:
            p=w/name
            if not p.exists(): raise SystemExit(f'Missing Stage-2 output {name}')
            shutil.copy2(p,RESULTS/name)
    shutil.copy2(design,RESULTS/'reference_design.dat')
    shutil.copy2(SCEN/'planning_scenarios.dat',RESULTS/'planning_scenarios.dat')
    shutil.copy2(SCEN/'scenario_map.csv',RESULTS/'scenario_map.csv')
    subprocess.run([sys.executable,str(HERE/'validate_stage2_results.py'),str(RESULTS),'--cost-lock-eps','0.01','--expected-design',str(design)],check=True)
    write_manifest(RESULTS/'manifest.json',{'stage':'stage2','selected_K':SELECTED_K,'input_hashes':file_hashes(required, ROOT),'output_hashes':file_hashes([RESULTS/x for x in OUTPUTS], ROOT)})
    print(f'Stage 2 complete: {RESULTS}')
if __name__=='__main__': main()
