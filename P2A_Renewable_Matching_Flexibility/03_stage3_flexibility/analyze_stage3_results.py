#!/usr/bin/env python3
from pathlib import Path
import argparse, pandas as pd, numpy as np
ZERO_TOL=1e-3; NEST_TOL=1e-3

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input',type=Path); ap.add_argument('--output-dir',type=Path,required=True); ap.add_argument('--prefix',default=''); ap.add_argument('--expect-full',action='store_true')
    a=ap.parse_args(); a.output_dir.mkdir(parents=True,exist_ok=True)
    df=pd.read_csv(a.input)
    req={'scenario','probability','case','case_name','duration_h','start','direction','F_PHYS_MW','F_RM_MW','retained_ratio','loss_MW'}
    miss=req-set(df.columns)
    if miss: raise SystemExit(f'Missing columns: {sorted(miss)}')
    if df.isna().any().any(): raise SystemExit('NaN detected in raw Stage-3 results.')
    key=['scenario','case','duration_h','start','direction']
    if df.duplicated(key).any(): raise SystemExit('Duplicate Stage-3 event rows detected.')
    df.loc[df.F_PHYS_MW.abs()<=ZERO_TOL,'F_PHYS_MW']=0.; df.loc[df.F_RM_MW.abs()<=ZERO_TOL,'F_RM_MW']=0.
    df['loss_MW']=df.F_PHYS_MW-df.F_RM_MW
    df['retained_ratio']=np.where(df.F_PHYS_MW>ZERO_TOL,df.F_RM_MW/df.F_PHYS_MW,np.nan)
    viol=df[df.F_RM_MW>df.F_PHYS_MW+NEST_TOL].copy()
    if len(viol): viol.to_csv(a.output_dir/f'{a.prefix}stage3_nesting_violations.csv',index=False)
    if a.expect_full:
        if set(df.scenario)!=set(range(1,10)) or set(df.case)!=set((1,2)) or set(df.duration_h)!=set((1,4,12,24)) or set(df.direction)!=set(('INC','DEC')):
            raise SystemExit('Full Stage-3 categorical coverage is incomplete.')
        if len(df)!=2864: raise SystemExit(f'Expected 2864 full paired-event rows, got {len(df)}')
    gcols=['scenario','probability','case','case_name','duration_h','direction']; rows=[]
    for keyv,g in df.groupby(gcols,sort=True):
        s,p,c,cname,d,q=keyv; phys=g.F_PHYS_MW.mean(); rm=g.F_RM_MW.mean(); valid=g[g.F_PHYS_MW>ZERO_TOL]
        rows.append({'scenario':s,'probability':p,'case':c,'case_name':cname,'duration_h':d,'direction':q,'n_events':len(g),'mean_phys_MW':phys,'mean_rm_MW':rm,'retained_ratio_of_means':rm/phys if phys>ZERO_TOL else np.nan,'mean_event_retained_ratio':(valid.F_RM_MW/valid.F_PHYS_MW).mean() if len(valid) else np.nan,'mean_loss_MW':(g.F_PHYS_MW-g.F_RM_MW).mean(),'rm_zero_fraction':(g.F_RM_MW<=ZERO_TOL).mean(),'min_phys_MW':g.F_PHYS_MW.min(),'max_phys_MW':g.F_PHYS_MW.max(),'min_rm_MW':g.F_RM_MW.min(),'max_rm_MW':g.F_RM_MW.max()})
    scen=pd.DataFrame(rows); scen.to_csv(a.output_dir/f'{a.prefix}stage3_scenario_summary.csv',index=False)
    rows=[]
    for (c,cname,d,q),g in scen.groupby(['case','case_name','duration_h','direction'],sort=True):
        w=g.probability.to_numpy(float); coverage=float(w.sum()); wn=w/coverage; phys=float(np.sum(wn*g.mean_phys_MW)); rm=float(np.sum(wn*g.mean_rm_MW)); loss=phys-rm
        rows.append({'case':c,'case_name':cname,'duration_h':d,'direction':q,'n_scenarios':len(g),'n_events':int(g.n_events.sum()),'probability_coverage':coverage,'weighted_mean_phys_MW':phys,'weighted_mean_rm_MW':rm,'weighted_retained_ratio':rm/phys if phys>ZERO_TOL else np.nan,'weighted_loss_MW':loss,'weighted_loss_fraction':loss/phys if phys>ZERO_TOL else np.nan,'weighted_rm_zero_fraction':float(np.sum(wn*g.rm_zero_fraction))})
    summary=pd.DataFrame(rows); summary.to_csv(a.output_dir/f'{a.prefix}stage3_retention_summary.csv',index=False)
    print('Stage-3 analysis complete'); print(f'  input rows: {len(df)}'); print(f'  nesting violations RM > PHYS + {NEST_TOL}: {len(viol)}')
    if a.expect_full and len(viol): raise SystemExit('Full Stage-3 nesting validation failed.')
    print(summary.to_string(index=False))
if __name__=='__main__': main()
