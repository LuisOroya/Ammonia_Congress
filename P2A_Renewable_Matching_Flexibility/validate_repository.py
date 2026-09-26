#!/usr/bin/env python3
from pathlib import Path
import re, sys, json
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from pipeline_config import SELECTED_K,K_VALUES,PWL_SEGMENTS

def parse_scen(path):
    txt=path.read_text(encoding='utf-8')
    sm=re.search(r'set S\s*:=\s*(.*?)\s*;',txt,re.S); pm=re.search(r'param:\s+NPER\s+PROB\s*:=\s*(.*?)\s*;',txt,re.S)
    if not sm or not pm: raise ValueError(f'Cannot parse {path}')
    S=[int(x) for x in sm.group(1).split()]; rows=[]
    for line in pm.group(1).splitlines():
        a=line.split()
        if len(a)>=3 and a[0].isdigit(): rows.append((int(a[0]),int(a[1]),float(a[2])))
    return S,rows


def parse_pwl(path):
    txt=path.read_text(encoding='utf-8')
    sm=re.search(r'set N\s*:=\s*(.*?)\s*;',txt,re.S)
    tm=re.search(r'param:\s+L\s+U\s+A\s+B\s*:=\s*(.*?)\s*;',txt,re.S)
    if not sm or not tm: raise ValueError(f'Cannot parse PWL file {path}')
    nset=[int(x) for x in sm.group(1).split()]
    rows=[]
    for line in tm.group(1).splitlines():
        a=line.split()
        if len(a)>=5 and a[0].isdigit(): rows.append((int(a[0]),float(a[1]),float(a[2]),float(a[3]),float(a[4])))
    return nset,rows

def main():
    errors=[]
    # Central PEM/PWL preprocessing artifact used by all optimization stages.
    pwl=ROOT/'00_pem_curve'/'generated'/f'pem_pwl_{PWL_SEGMENTS}segments.dat'
    if not pwl.exists():
        errors.append(f'Missing generated PEM/PWL input: {pwl}')
    else:
        try:
            nset,prows=parse_pwl(pwl)
            if len(nset)!=PWL_SEGMENTS or len(prows)!=PWL_SEGMENTS:
                errors.append(f'PWL segment-count mismatch: configured {PWL_SEGMENTS}, file has {len(prows)}')
            expected_bp=[0.15000,0.26401,0.38909,0.52523,0.67242,0.83068,1.00000]
            got=[prows[0][1]]+[r[2] for r in prows] if prows else []
            if len(got)==len(expected_bp) and max(abs(a-b) for a,b in zip(got,expected_bp))>5e-5:
                errors.append(f'Unexpected six-segment PEM breakpoints: {got}')
        except Exception as e: errors.append(str(e))
    # PWL coefficients must not be duplicated in the stage-specific common-data files.
    for rel in ('01_stage1_reference_sizing/planning_common.dat','02_stage2_baselines/stage2_common.dat','03_stage3_flexibility/flex_common.dat'):
        txt=(ROOT/rel).read_text(encoding='utf-8')
        if re.search(r'param:\s+L\s+U\s+A\s+B',txt): errors.append(f'Duplicated PWL coefficient table remains in {rel}')
    for k in K_VALUES:
        d=ROOT/'01_stage1_reference_sizing'/'scenario_sets'/f'K{k:02d}'
        for f in ('planning_scenarios.dat','planning_profiles.dat','scenario_map.csv'):
            if not (d/f).exists(): errors.append(f'Missing {d/f}')
        try:
            S,rows=parse_scen(d/'planning_scenarios.dat')
            if len(S)!=k or len(rows)!=k: errors.append(f'K{k:02d}: scenario count mismatch')
            ps=sum(r[2] for r in rows)
            if abs(ps-1)>1e-9: errors.append(f'K{k:02d}: probability sum={ps}')
            if any(r[1]>744 or r[1]<=0 for r in rows): errors.append(f'K{k:02d}: invalid NPER')
        except Exception as e: errors.append(str(e))
    # prevent stale design hardcodes in Stage3 prep/source commons
    text='\n'.join((ROOT/'03_stage3_flexibility'/f).read_text(encoding='utf-8') for f in ('prepare_stage3_inputs.py','flex_common.dat'))
    for stale in ('159.96','499.30','27920'):
        if stale in text: errors.append(f'Stale design literal remains in Stage3 source: {stale}')
    # Font files are intentionally excluded from the public repository.
    if list(ROOT.rglob('*.otf')) or list(ROOT.rglob('*.ttf')): errors.append('Font file present; remove before publication.')
    if errors:
        print('Repository validation FAILED:'); [print(' -',e) for e in errors]; raise SystemExit(1)
    print('Repository input validation passed')
    print(f'  configured selected K: {SELECTED_K}')
    print(f'  K scenario sets: {min(K_VALUES)}..{max(K_VALUES)}')
    print('  probability sums and scenario counts: OK')
    print(f'  centralized PEM/PWL file: {PWL_SEGMENTS} segments, OK')
    print('  no stale Stage-3 design literals: OK')
    print('  no font files: OK')
if __name__=='__main__': main()
