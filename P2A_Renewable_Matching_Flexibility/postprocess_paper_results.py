#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parent; R=ROOT/'results'
need=[R/'stage2'/'stage2_case_summary.csv',R/'stage3'/'stage3_retention_summary.csv']
for p in need:
    if not p.exists(): raise SystemExit(f'Missing {p}; complete the pipeline first.')
s2=pd.read_csv(need[0]); s3=pd.read_csv(need[1])
lines=['# Compact paper-result summary','']
if (R/'stage1'/'stage1_stability_K08_K13.csv').exists():
    st=pd.read_csv(R/'stage1'/'stage1_stability_K08_K13.csv'); lines+=['## Stage 1 — K=8..13 stability','',st.to_markdown(index=False,floatfmt='.6g'),'']
lines+=['## Stage 2 — probability-weighted baselines','',s2.to_markdown(index=False,floatfmt='.6g'),'']
lines+=['## Stage 3 — probability-weighted retained flexibility','',s3.to_markdown(index=False,floatfmt='.6g'),'']
# compact hourly-only table for manuscript use
h=s3[s3.case_name=='HOURLY'].copy();
if len(h):
    piv=h.pivot(index='duration_h',columns='direction',values=['weighted_mean_phys_MW','weighted_mean_rm_MW','weighted_retained_ratio','weighted_loss_MW'])
    lines+=['## Stage 3 — hourly matching compact pivot','',piv.to_markdown(floatfmt='.6g'),'']
out=R/'paper_result_summary.md'; out.write_text('\n'.join(lines),encoding='utf-8'); print('Wrote',out)
