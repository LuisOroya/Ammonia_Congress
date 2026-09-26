#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; p=ROOT/'results'/'stage1'/'stage1_sweep_summary.csv'
if not p.exists(): raise SystemExit(f'Missing {p}; run full Stage-1 sweep first.')
df=pd.read_csv(p); band=df[df.K.between(8,13)].copy(); k9=df[df.K==9].iloc[0]
band['total_RES_MW']=band.pv_MW+band.wind_MW
metrics=[]
for label,col,ref in [('total_RES_MW','total_RES_MW',float(k9.pv_MW+k9.wind_MW)),('h2_storage_kg','h2_storage_kg',float(k9.h2_storage_kg)),('objective_USD_per_year','objective_USD_per_year',float(k9.objective_USD_per_year))]:
    vals=band[col].astype(float); metrics.append({'metric':label,'K_min':8,'K_max':13,'min':vals.min(),'max':vals.max(),'K9_reference':ref,'range_over_K9_percent':100*(vals.max()-vals.min())/ref})
out=ROOT/'results'/'stage1'/'stage1_stability_K08_K13.csv'; pd.DataFrame(metrics).to_csv(out,index=False)
print(pd.DataFrame(metrics).to_string(index=False)); print('Wrote',out)
