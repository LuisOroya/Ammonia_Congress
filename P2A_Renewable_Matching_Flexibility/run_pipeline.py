#!/usr/bin/env python3
from pathlib import Path
import argparse, subprocess, sys
ROOT=Path(__file__).resolve().parent

def run(args):
    print('\n>>>',' '.join(map(str,args))); subprocess.run(args,cwd=ROOT,check=True)

def main():
    ap=argparse.ArgumentParser(description='Reproduce PEM preprocessing and the P2A optimization workflow.')
    ap.add_argument('--from-stage',type=int,choices=(0,1,2,3),default=1)
    ap.add_argument('--stage1-mode',choices=('sweep','selected'),default='sweep')
    ap.add_argument('--fresh',action='store_true',help='Delete generated results before starting.')
    ap.add_argument('--pilot-only',action='store_true')
    a=ap.parse_args()
    run([sys.executable,'validate_repository.py'])
    if a.fresh: run([sys.executable,'scripts/clean_results.py'])
    if a.from_stage<=0:
        run([sys.executable,'00_pem_curve/generate_pem_pwl.py','--segments','6'])
        run([sys.executable,'validate_repository.py'])
    if a.from_stage<=1:
        cmd=[sys.executable,'01_stage1_reference_sizing/run_stage1.py','--overwrite']
        if a.stage1_mode=='selected': cmd.append('--selected-only')
        run(cmd)
        if a.stage1_mode=='sweep': run([sys.executable,'01_stage1_reference_sizing/analyze_stage1_sweep.py'])
    if a.from_stage<=2: run([sys.executable,'02_stage2_baselines/run_stage2.py','--overwrite'])
    if a.from_stage<=3:
        cmd=[sys.executable,'03_stage3_flexibility/run_stage3.py','--overwrite']
        if a.pilot_only: cmd.append('--pilot-only')
        run(cmd)
        if not a.pilot_only: run([sys.executable,'postprocess_paper_results.py'])
    print('\nPipeline finished successfully.')
if __name__=='__main__': main()
