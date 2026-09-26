#!/usr/bin/env python3
"""Build Stage-3 baseline data from the freshly generated Stage-2 outputs.

No reference-design value is hardcoded. The script reads the selected Stage-1
rounded design and verifies that Stage 2 used the same values.
"""
from pathlib import Path
import csv, re, sys
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
from pipeline_config import SELECTED_K

S2=ROOT/'results'/'stage2'
S1=ROOT/'results'/'stage1'/f'K{SELECTED_K:02d}'
OUTDIR=ROOT/'results'/'stage3'; OUTDIR.mkdir(parents=True,exist_ok=True)
BASE_CSV=S2/'stage2_baselines.csv'; REF_CSV=S2/'stage2_reference_design.csv'; DESIGN=S1/'reference_design_rounded.dat'; OUT=OUTDIR/'stage3_baselines_k09.dat'
CASES=(1,2)

def parse_design(path):
    txt=path.read_text(encoding='utf-8'); out=[]
    for n in ('P_PV_MAX','P_WD_MAX','H2_ST_MAX'):
        m=re.search(rf'param\s+{n}\s*:=\s*([0-9eE+\-.]+)\s*;',txt)
        if not m: raise SystemExit(f'Missing {n} in {path}')
        out.append(float(m.group(1)))
    return tuple(out)

def close(a,b,tol=1e-6): return abs(a-b)<=tol

def parse_nper(path):
    txt=path.read_text(encoding='utf-8'); m=re.search(r'param:\s+NPER\s+PROB\s*:=\s*(.*?)\s*;',txt,re.S)
    if not m: raise SystemExit(f'Could not parse NPER from {path}')
    out={}
    for line in m.group(1).splitlines():
        a=line.split()
        if len(a)>=3 and a[0].isdigit(): out[int(a[0])]=int(a[1])
    return out

def write_slices(f,name,data,times_by_sc):
    f.write(f'param {name} :=\n')
    for s in sorted(times_by_sc):
        for c in CASES:
            vals=data[(s,c)]; f.write(f'[{s},{c},*]'); count=0
            for t in sorted(vals):
                f.write(f' {t} {vals[t]:.15f}'); count+=1
                if count%6==0: f.write('\n  ')
            f.write('\n')
    f.write(';\n\n')

for p in (BASE_CSV,REF_CSV,DESIGN,S2/'planning_scenarios.dat'):
    if not p.exists(): raise SystemExit(f'Missing {p}; run previous stages first.')
expected=parse_design(DESIGN)
with REF_CSV.open(newline='') as fh:
    r=next(csv.DictReader(fh)); got=(float(r['pv_MW']),float(r['wind_MW']),float(r['h2_storage_kg']))
if not all(close(a,b) for a,b in zip(got,expected)):
    raise SystemExit(f'Reference-design mismatch: Stage2={got}, Stage1={expected}')
NPER=parse_nper(S2/'planning_scenarios.dat')
fields={'BASE_P2A':'p2a_MW','BASE_PEL':'pel_MW','BASE_H2PROD':'h2prod_kgph','BASE_NH3':'nh3_kgph','BASE_PV':'pv_MW','BASE_WD':'wind_MW','BASE_MATCH_LOAD':'match_load_MW'}
data={n:{} for n in fields}; h2={}; rows={(s,c):0 for s in NPER for c in CASES}
with BASE_CSV.open(newline='') as fh:
    for row in csv.DictReader(fh):
        c=int(row['case']);
        if c not in CASES: continue
        s=int(row['scenario']); t=int(row['t']); key=(s,c); rows[key]+=1
        for name,col in fields.items(): data[name].setdefault(key,{})[t]=float(row[col])
        h2.setdefault(key,{})[t]=float(row['h2st_kg'])
for s,n in NPER.items():
    for c in CASES:
        if rows[(s,c)]!=n: raise SystemExit(f'Incomplete baseline s={s}, c={c}: {rows[(s,c)]}/{n}')
        h2[(s,c)][0]=0.5*expected[2]
cum_nh3={}; cum_res={}; cum_match={}
for s,n in NPER.items():
    for c in CASES:
        key=(s,c); cum_nh3[key]={0:0.}; cum_res[key]={0:0.}; cum_match[key]={0:0.}; a=b=d=0.
        for t in range(1,n+1):
            a+=data['BASE_NH3'][key][t]; b+=data['BASE_PV'][key][t]+data['BASE_WD'][key][t]; d+=data['BASE_MATCH_LOAD'][key][t]
            cum_nh3[key][t]=a; cum_res[key][t]=b; cum_match[key][t]=d
with OUT.open('w',newline='\n') as f:
    f.write('# Generated from freshly validated Stage-2 baselines. Cases 1=MONTHLY, 2=HOURLY.\n\ndata;\n\n')
    for name in fields: write_slices(f,name,data[name],NPER)
    for name,obj in [('BASE_H2ST',h2),('BASE_NH3_CUM',cum_nh3),('BASE_RES_CUM',cum_res),('BASE_MATCH_CUM',cum_match)]: write_slices(f,name,obj,NPER)
print('Stage-3 baseline input created:',OUT)
print(f'Validated design: PV={expected[0]} MW, wind={expected[1]} MW, H2={expected[2]} kg')
