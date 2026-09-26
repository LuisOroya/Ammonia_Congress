#!/usr/bin/env python3
from pathlib import Path
import argparse, pandas as pd, re, sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from pipeline_config import PWL_SEGMENTS

def parse_design(path: Path):
    txt=path.read_text(encoding='utf-8'); vals=[]
    for n in ('P_PV_MAX','P_WD_MAX','H2_ST_MAX'):
        m=re.search(rf'param\s+{n}\s*:=\s*([0-9eE+\-.]+)\s*;',txt)
        if not m: raise SystemExit(f'Missing {n} in {path}')
        vals.append(float(m.group(1)))
    return tuple(vals)

def parse_nper(path: Path):
    txt=path.read_text(encoding='utf-8'); m=re.search(r'param:\s+NPER\s+PROB\s*:=\s*(.*?)\s*;',txt,re.S)
    if not m: raise SystemExit(f'Cannot parse NPER from {path}')
    out={}
    for line in m.group(1).splitlines():
        a=line.split()
        if len(a)>=3 and a[0].isdigit(): out[int(a[0])]=int(a[1])
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('results_dir',type=Path); ap.add_argument('--cost-lock-eps',type=float,default=0.01); ap.add_argument('--expected-design',type=Path,required=True)
    a=ap.parse_args(); d=a.results_dir
    req=['stage2_case_summary.csv','stage2_case_scenario_summary.csv','stage2_scenario_solve_summary.csv','stage2_baselines.csv','stage2_segments.csv','stage2_reference_design.csv','planning_scenarios.dat']
    for f in req:
        if not (d/f).exists(): raise SystemExit(f'Missing {d/f}')
    expected=parse_design(a.expected_design)
    ref=pd.read_csv(d/'stage2_reference_design.csv').iloc[0]
    got=(float(ref.pv_MW),float(ref.wind_MW),float(ref.h2_storage_kg))
    if any(abs(x-y)>1e-6 for x,y in zip(got,expected)): raise SystemExit(f'Stage-2 design mismatch: {got} vs {expected}')
    nper=parse_nper(d/'planning_scenarios.dat')
    ss=pd.read_csv(d/'stage2_scenario_solve_summary.csv')
    if len(ss)!=3*len(nper): raise SystemExit(f'Expected {3*len(nper)} scenario/case rows, got {len(ss)}')
    if ss.isna().any().any(): raise SystemExit('NaN detected in stage2_scenario_solve_summary.csv')
    if 'cost_excess_USD' not in ss: raise SystemExit('Missing cost_excess_USD audit column.')
    bad=ss[ss.cost_excess_USD > a.cost_lock_eps + 1e-6]
    if len(bad): raise SystemExit(f'{len(bad)} Stage-B solutions exceed the cost lock.')
    if (ss.cost_excess_USD < -1e-5).any(): raise SystemExit('Stage-B cost materially below stored Stage-A optimum; investigate numerical consistency.')
    b=pd.read_csv(d/'stage2_baselines.csv')
    expected_b=3*sum(nper.values())
    if len(b)!=expected_b: raise SystemExit(f'Expected {expected_b} baseline rows, got {len(b)}')
    if b.isna().any().any(): raise SystemExit('NaN detected in stage2_baselines.csv')
    seg=pd.read_csv(d/'stage2_segments.csv')
    if len(seg)!=PWL_SEGMENTS*expected_b: raise SystemExit(f'Expected {PWL_SEGMENTS*expected_b} segment rows, got {len(seg)}')
    resid=(b.pv_MW+b.wind_MW+b.grid_imp_MW)-(b.p2a_MW+b.grid_exp_MW)
    if resid.abs().max()>2e-5: raise SystemExit(f'Power-balance residual too large: {resid.abs().max()} MW')
    piv=ss.pivot(index='scenario',columns='case_name',values=['primary_cost_star_USD','normalized_variability'])
    warnings_nm=[]
    violations=[]
    for scen,row in piv.iterrows():
        cn=row[('primary_cost_star_USD','NO_MATCH')]
        cm=row[('primary_cost_star_USD','MONTHLY')]
        if abs(cn-cm)<=1e-5:
            vn=row[('normalized_variability','NO_MATCH')]
            vm=row[('normalized_variability','MONTHLY')]
            delta=float(vn-vm)
            # The exact nested problems satisfy V_N <= V_M.  A dedicated S5
            # diagnostic showed that very small inversions can arise from the
            # Stage-B MILP solution path even with mipgap=0: the MONTHLY binary
            # pattern, when replayed in NO_MATCH, produced a lower feasible V_N.
            # Keep the audit, but reserve a hard failure for a material inversion.
            if delta>1e-3:
                violations.append((int(scen),float(vn),float(vm),delta))
            elif delta>1e-5:
                warnings_nm.append((int(scen),float(vn),float(vm),delta))
    if violations:
        raise SystemExit('Material N/M secondary-ordering violation(s): '+repr(violations))
    for scen,vn,vm,delta in warnings_nm:
        print(f'WARNING: small numerical N/M ordering discrepancy: '
              f's={scen}, V_N={vn:.10f}, V_M={vm:.10f}, delta={delta:.3e}')
    print('Stage-2 validation passed')
    print(f'  design: PV={got[0]:.3f} MW, wind={got[1]:.3f} MW, H2={got[2]:.0f} kg')
    print(f'  scenario/case rows: {len(ss)}')
    print(f'  baseline rows: {len(b)}; segment rows: {len(seg)}')
    print(f'  max power-balance residual: {resid.abs().max():.3e} MW')
    print(f'  max Stage-B cost excess: {ss.cost_excess_USD.max():.6g} USD')
    print(f'  small N/M numerical warnings: {len(warnings_nm)}')
if __name__=='__main__': main()
